"""
Enhanced Code Pipeline with WebSocket Support

Extends the base pipeline with:
- WebSocket integration for real-time events
- Browser screenshot streaming
- Terminal I/O handling
- Approval flow management
- Auto Drive progress tracking
"""

import asyncio
import base64
import logging
from typing import Dict, Any, Optional, AsyncIterator
from pathlib import Path

from pipelines.code_pipeline import Pipeline as BasePipeline
from backend.websocket_handler import ws_manager
from utils.event_translator import CodeEventTranslator

logger = logging.getLogger(__name__)


class EnhancedPipeline(BasePipeline):
    """
    Enhanced Code Pipeline with WebSocket support

    This extends the base pipeline to provide real-time updates
    via WebSocket for better UX.
    """

    def __init__(self):
        super().__init__()
        self.ws_manager = ws_manager

    async def _handle_chat(
        self,
        user_input: str,
        manager,
        translator: CodeEventTranslator,
        conversation_id: str,
        event_emitter: Any
    ) -> AsyncIterator[str]:
        """
        Enhanced chat handler with WebSocket support

        Overrides base implementation to also broadcast events via WebSocket
        """
        logger.info(f"Enhanced chat handler: {user_input[:100]}...")

        # Send user message to Code
        await manager.send_user_message(conversation_id, user_input)

        # Determine session ID for WebSocket broadcasts
        session_id = f"session_{conversation_id}"

        # Stream events from Code and translate
        async for code_event in manager.stream_events():
            # Translate to OpenAI format
            openai_events = translator.translate(code_event)

            # Also handle WebSocket-specific events
            await self._handle_realtime_event(session_id, code_event)

            # Yield OpenAI events for SSE
            for event in openai_events:
                if event_emitter and event.event_type != "thread.message.delta":
                    await event_emitter({
                        "type": "status",
                        "data": {
                            "description": f"Code: {event.event_type}",
                            "done": event.event_type == "done"
                        }
                    })

                yield event.to_sse_format()

                if event.event_type == "done":
                    logger.info("Conversation turn completed")
                    return

    async def _handle_realtime_event(
        self,
        session_id: str,
        code_event: Dict[str, Any]
    ):
        """
        Handle real-time events for WebSocket broadcasting

        This processes Code events and sends appropriate WebSocket messages
        """
        if "method" in code_event:
            params = code_event.get("params", {}) or {}
            msg = params.get("msg", {}) or {}
        else:
            msg = code_event.get("msg", {}) or {}

        event_type = msg.get("type")
        if not event_type:
            return

        # Browser screenshot
        if event_type == "browser_screenshot_update":
            await self._handle_browser_screenshot(session_id, msg)

        # Terminal output
        elif event_type == "exec_command_output_delta":
            await self._handle_terminal_output(session_id, msg)

        # Approval request
        elif event_type in ["exec_approval_request", "apply_patch_approval_request"]:
            await self._handle_approval_request(session_id, msg)

        # Auto Drive update
        elif event_type == "auto_coordinator_decision":
            await self._handle_auto_drive_update(session_id, msg)

        # Tool execution
        elif event_type in ["exec_command_begin", "exec_command_end",
                           "patch_apply_begin", "patch_apply_end",
                           "mcp_tool_call_begin", "mcp_tool_call_end"]:
            await self._handle_tool_execution(session_id, msg)
    async def _handle_browser_screenshot(
        self,
        session_id: str,
        msg: Dict[str, Any]
    ):
        """Handle browser screenshot event"""
        screenshot = msg.get("screenshot", {})

        # Extract screenshot data
        image_data = screenshot.get("data")  # May be base64 data URL or file path
        image_path = screenshot.get("path")

        if not image_data and image_path:
            image_data = image_path

        # If file path, read and encode
        if image_data and not image_data.startswith("data:"):
            try:
                with open(image_data, "rb") as f:
                    image_bytes = f.read()
                    image_data = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
            except Exception as e:
                logger.error(f"Error reading screenshot: {e}")
                return

        if not image_data:
            logger.warning("Dropping browser screenshot with no data or path")
            return

        # Extract metadata
        metadata = {
            "url": screenshot.get("url"),
            "title": screenshot.get("title"),
            "timestamp": screenshot.get("timestamp"),
            "viewport": screenshot.get("viewport")
        }

        # Broadcast via WebSocket
        await self.ws_manager.handle_browser_screenshot(
            session_id,
            image_data,
            metadata
        )
    async def _handle_terminal_output(
        self,
        session_id: str,
        msg: Dict[str, Any]
    ):
        """Handle terminal output event"""
        terminal_id = msg.get("call_id", "default")
        chunk = msg.get("chunk", "")
        is_stderr = msg.get("is_stderr", False)

        await self.ws_manager.handle_terminal_output(
            session_id,
            terminal_id,
            chunk,
            is_stderr
        )

    async def _handle_approval_request(
        self,
        session_id: str,
        msg: Dict[str, Any]
    ):
        """Handle approval request event"""
        request_id = msg.get("id", msg.get("call_id"))

        # Determine request type
        if msg.get("type") == "exec_approval_request":
            request_type = "command_execution"
            request_data = {
                "command": msg.get("command"),
                "cwd": msg.get("cwd"),
                "reason": msg.get("reason")
            }
        else:  # patch approval
            request_type = "file_changes"
            request_data = {
                "changes": msg.get("changes", []),
                "diff": msg.get("diff")
            }

        await self.ws_manager.handle_approval_request(
            session_id,
            request_id,
            request_type,
            request_data
        )

    async def _handle_auto_drive_update(
        self,
        session_id: str,
        msg: Dict[str, Any]
    ):
        """Handle Auto Drive progress update"""
        status = msg.get("status")
        progress = msg.get("progress", {})
        agents = msg.get("agents", [])
        transcript = msg.get("transcript", [])

        await self.ws_manager.handle_auto_drive_update(
            session_id,
            status,
            progress,
            agents,
            transcript
        )

    async def _handle_tool_execution(
        self,
        session_id: str,
        msg: Dict[str, Any]
    ):
        """Handle tool execution event"""
        event_type = msg.get("type")
        tool_id = msg.get("call_id", "unknown")

        # Determine tool type and status
        if "exec_command" in event_type:
            tool_type = "bash"
            status = "running" if "begin" in event_type else "completed"
            data = {
                "command": msg.get("command"),
                "exit_code": msg.get("exit_code")
            }
        elif "patch_apply" in event_type:
            tool_type = "file_edit"
            status = "running" if "begin" in event_type else "completed"
            data = {
                "changes": msg.get("changes", [])
            }
        elif "mcp_tool_call" in event_type:
            tool_type = "mcp"
            status = "running" if "begin" in event_type else "completed"
            invocation = msg.get("invocation", {})
            data = {
                "server": invocation.get("server"),
                "tool": invocation.get("tool"),
                "arguments": invocation.get("arguments")
            }
        else:
            return

        await self.ws_manager.handle_tool_execution(
            session_id,
            tool_id,
            tool_type,
            status,
            data
        )

    async def handle_approval_response(
        self,
        request_id: str,
        decision: str,
        user_data: Optional[Dict[str, Any]] = None
    ):
        """
        Handle approval response from user

        This is called when user approves/rejects via WebSocket
        """
        # Get approval request
        request = await self.ws_manager.handle_approval_response(
            request_id,
            decision,
            user_data
        )

        # Get session
        session_id = request["session_id"]
        session_data = self.sessions.get(session_id)

        if not session_data:
            logger.error(f"Session not found: {session_id}")
            return

        manager = session_data["manager"]

        # Send approval to Code
        if request["request_type"] == "command_execution":
            await manager.send_notification("execApproval", {
                "id": request_id,
                "decision": decision
            })
        else:  # file_changes
            await manager.send_notification("patchApproval", {
                "id": request_id,
                "decision": decision
            })

        logger.info(f"Approval {decision} sent for request {request_id}")


# Create enhanced pipeline instance
def get_pipeline():
    """Return enhanced pipeline instance"""
    return EnhancedPipeline()
