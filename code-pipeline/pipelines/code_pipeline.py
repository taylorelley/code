"""
Code Pipeline for Open WebUI

This pipeline integrates the Code agentic coding assistant into Open WebUI,
providing all TUI features through a web interface.

Features:
- Multi-agent orchestration (/plan, /solve, /code)
- Auto Drive automation (/auto)
- Browser integration
- Terminal sessions
- File operations with approval
- MCP tool support
- Streaming responses

Usage:
1. Install Code binary (https://github.com/just-every/code)
2. Configure pipeline in Open WebUI
3. Set CODE_BINARY_PATH if needed
4. Chat with Code through web UI!
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List, Union, AsyncIterator, Generator
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from utils.event_translator import CodeEventTranslator, OpenAIEvent
from utils.subprocess_manager import CodeServerManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Pipeline:
    """
    Code Pipeline for Open WebUI

    This is a Pipe-type pipeline that provides OpenAI-compatible endpoints
    while routing requests to Code app-server for agentic coding capabilities.
    """

    class Valves(BaseModel):
        """Pipeline configuration (user-editable settings)"""

        CODE_BINARY_PATH: str = Field(
            default=os.getenv("CODE_BINARY_PATH", "code"),
            description="Path to the Code binary executable"
        )

        ENABLE_BROWSER: bool = Field(
            default=True,
            description="Enable browser integration features"
        )

        ENABLE_AUTO_DRIVE: bool = Field(
            default=True,
            description="Enable Auto Drive multi-agent orchestration"
        )

        MAX_CONCURRENT_SESSIONS: int = Field(
            default=10,
            description="Maximum number of concurrent Code sessions"
        )

        DEFAULT_WORKING_DIR: str = Field(
            default=os.getenv("CODE_WORKING_DIR", "/tmp/code-workspace"),
            description="Default working directory for Code sessions"
        )

        APPROVAL_POLICY: str = Field(
            default="on-request",
            description="Command approval policy: untrusted | on-failure | on-request | never"
        )

        SANDBOX_MODE: str = Field(
            default="workspace-write",
            description="Sandbox mode: read-only | workspace-write | danger-full-access"
        )

        MODEL: str = Field(
            default="gpt-4",
            description="Default model to use (can be overridden per request)"
        )

    def __init__(self):
        """Initialize the pipeline"""
        self.type = "pipe"  # Pipe-type pipeline (OpenAI API compatible)
        self.id = "code_pipeline"
        self.name = "Code Agentic Assistant"
        self.valves = self.Valves()

        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_lock = asyncio.Lock()

        logger.info("Code Pipeline initialized")

    async def on_startup(self):
        """Called when the pipeline server starts"""
        logger.info("Code Pipeline starting up...")
        logger.info(f"Code binary: {self.valves.CODE_BINARY_PATH}")
        logger.info(f"Default working dir: {self.valves.DEFAULT_WORKING_DIR}")

        # Ensure working directory exists
        Path(self.valves.DEFAULT_WORKING_DIR).mkdir(parents=True, exist_ok=True)

    async def on_shutdown(self):
        """Called when the pipeline server shuts down"""
        logger.info("Code Pipeline shutting down...")

        # Clean up all active sessions
        async with self.session_lock:
            for session_id, session_data in self.sessions.items():
                try:
                    manager: CodeServerManager = session_data.get("manager")
                    if manager and manager.is_running():
                        logger.info(f"Stopping session {session_id}")
                        await manager.stop()
                except Exception as e:
                    logger.error(f"Error stopping session {session_id}: {e}")

            self.sessions.clear()

        logger.info("Code Pipeline shut down complete")

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Any = None
    ) -> Union[str, Generator, AsyncIterator]:
        """
        Main pipeline entry point (OpenAI-compatible)

        This method is called by Open WebUI for each chat request.

        Args:
            body: Request body (OpenAI chat completion format)
            __user__: User information from Open WebUI
            __event_emitter__: Event emitter for sending status updates

        Returns:
            Async generator yielding SSE-formatted events
        """
        logger.info("=== Code Pipeline Request ===")
        logger.debug(f"Body: {body}")
        logger.debug(f"User: {__user__}")

        # Extract user message
        messages = body.get("messages", [])
        if not messages:
            return "Error: No messages provided"

        # Get the latest user message
        last_message = messages[-1]
        user_input = last_message.get("content", "")

        if not user_input:
            return "Error: Empty message"

        # Get or create session for this user
        user_id = __user__.get("id") if __user__ else "default"
        session_id = f"session_{user_id}"

        try:
            # Get or create Code session
            session_data = await self._get_or_create_session(session_id, user_id)
            manager: CodeServerManager = session_data["manager"]
            translator: CodeEventTranslator = session_data["translator"]
            conversation_id: str = session_data["conversation_id"]

            # Check for slash commands
            if user_input.strip().startswith("/"):
                return self._handle_slash_command(
                    user_input,
                    manager,
                    translator,
                    conversation_id,
                    __event_emitter__
                )

            # Send regular message
            return self._handle_chat(
                user_input,
                manager,
                translator,
                conversation_id,
                __event_emitter__
            )

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return f"Error: {str(e)}"

    async def _get_or_create_session(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get or create a Code session for the user"""
        async with self.session_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                # Check if session is still alive
                if session["manager"].is_running():
                    return session
                else:
                    # Session died, clean up
                    logger.warning(f"Session {session_id} died, recreating")
                    del self.sessions[session_id]

            # Create new session
            logger.info(f"Creating new Code session for user {user_id}")

            # Create user-specific working directory
            working_dir = os.path.join(
                self.valves.DEFAULT_WORKING_DIR,
                f"user_{user_id}"
            )
            Path(working_dir).mkdir(parents=True, exist_ok=True)

            # Create manager
            manager = CodeServerManager(
                code_binary_path=self.valves.CODE_BINARY_PATH,
                working_dir=working_dir
            )

            # Start the server
            await manager.start()

            # Initialize Code session
            await manager.initialize_session({
                "name": "open-webui-pipeline",
                "version": "0.1.0",
                "user_id": user_id
            })

            # Create a new conversation
            conversation_id = await manager.new_conversation(working_dir)

            # Create event translator
            translator = CodeEventTranslator()

            # Store session
            session_data = {
                "manager": manager,
                "translator": translator,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "working_dir": working_dir
            }

            self.sessions[session_id] = session_data

            # Start monitoring stderr in background
            asyncio.create_task(manager.monitor_stderr())

            logger.info(f"Session {session_id} created with conversation {conversation_id}")

            return session_data

    async def _handle_chat(
        self,
        user_input: str,
        manager: CodeServerManager,
        translator: CodeEventTranslator,
        conversation_id: str,
        event_emitter: Any
    ) -> AsyncIterator[str]:
        """
        Handle regular chat message

        Args:
            user_input: User's message
            manager: Code server manager
            translator: Event translator
            conversation_id: Code conversation ID
            event_emitter: Event emitter for status updates

        Yields:
            SSE-formatted event strings
        """
        logger.info(f"Sending message to Code: {user_input[:100]}...")

        # Send user message to Code
        await manager.send_user_message(conversation_id, user_input)

        # Stream events from Code and translate to OpenAI format
        async for code_event in manager.stream_events():
            # Translate Code event to OpenAI format
            openai_events = translator.translate(code_event)

            # Yield each translated event
            for event in openai_events:
                # Send status update via event emitter if available
                if event_emitter and event.event_type != "thread.message.delta":
                    await event_emitter({
                        "type": "status",
                        "data": {
                            "description": f"Code: {event.event_type}",
                            "done": event.event_type == "done"
                        }
                    })

                # Yield SSE-formatted event
                yield event.to_sse_format()

                # Check for completion
                if event.event_type == "done":
                    logger.info("Conversation turn completed")
                    return

    async def _handle_slash_command(
        self,
        command: str,
        manager: CodeServerManager,
        translator: CodeEventTranslator,
        conversation_id: str,
        event_emitter: Any
    ) -> AsyncIterator[str]:
        """
        Handle slash commands like /plan, /solve, /code, /auto

        Args:
            command: Full command string
            manager: Code server manager
            translator: Event translator
            conversation_id: Code conversation ID
            event_emitter: Event emitter

        Yields:
            SSE-formatted event strings
        """
        logger.info(f"Handling slash command: {command}")

        # Parse command
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Map of supported commands
        supported_commands = {
            "/plan": "Multi-agent planning mode",
            "/solve": "Multi-agent problem solving",
            "/code": "Multi-agent code implementation",
            "/auto": "Auto Drive orchestration",
            "/browser": "Browser integration",
            "/chrome": "Connect to Chrome DevTools",
            "/settings": "Show settings",
            "/help": "Show help"
        }

        if cmd == "/help":
            help_text = "**Available Commands:**\n\n"
            for cmd_name, desc in supported_commands.items():
                help_text += f"- `{cmd_name}`: {desc}\n"

            yield self._create_simple_response(help_text)
            return

        if cmd not in supported_commands:
            error_msg = f"Unknown command: {cmd}\n\nTry `/help` for available commands."
            yield self._create_simple_response(error_msg)
            return

        # For now, pass the command as-is to Code
        # Code's CLI handles slash commands natively
        full_message = f"{cmd} {args}".strip()

        # Use regular chat handler (Code will interpret the command)
        async for event in self._handle_chat(
            full_message,
            manager,
            translator,
            conversation_id,
            event_emitter
        ):
            yield event

    def _create_simple_response(self, text: str) -> str:
        """Create a simple text response in SSE format"""
        event = OpenAIEvent(
            "thread.message.completed",
            {
                "id": f"msg_{id(text)}",
                "object": "thread.message.completed",
                "delta": {
                    "role": "assistant",
                    "content": [{
                        "type": "text",
                        "text": {"value": text}
                    }]
                }
            }
        )
        return event.to_sse_format() + "\n" + OpenAIEvent(
            "done",
            {"[DONE]": True}
        ).to_sse_format()


# Required for Open WebUI Pipelines
def get_pipeline():
    """Return pipeline instance (required by Open WebUI)"""
    return Pipeline()


# Standalone testing
if __name__ == "__main__":
    import asyncio

    async def test_pipeline():
        """Test the pipeline locally"""
        pipeline = Pipeline()

        await pipeline.on_startup()

        try:
            # Test body (OpenAI format)
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! Can you help me write a Python function to calculate fibonacci numbers?"
                    }
                ]
            }

            user = {"id": "test_user"}

            print("\n=== Testing Code Pipeline ===\n")

            async for event in pipeline.pipe(body, __user__=user):
                if isinstance(event, str):
                    print(event, end="")
                else:
                    print(f"Event: {event}")

        finally:
            await pipeline.on_shutdown()

    # Run test
    asyncio.run(test_pipeline())
