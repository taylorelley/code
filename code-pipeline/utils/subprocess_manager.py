"""
Subprocess Manager for Code app-server

Manages lifecycle of code app-server subprocess including:
- Process spawning and monitoring
- JSON-RPC communication over stdio
- Graceful shutdown and cleanup
- Error handling and recovery
"""

import asyncio
import json
import logging
import os
import signal
from typing import Optional, Dict, Any, AsyncIterator
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)


class CodeServerManager:
    """Manages a Code app-server subprocess"""

    def __init__(
        self,
        code_binary_path: str = "code",
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Code server manager

        Args:
            code_binary_path: Path to code binary (default: "code" in PATH)
            working_dir: Working directory for code execution
            env: Additional environment variables
        """
        self.code_binary_path = code_binary_path
        self.working_dir = working_dir or os.getcwd()
        self.env = env or {}

        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}

        # Ensure working directory exists
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the Code app-server process"""
        if self.process and self.process.returncode is None:
            logger.warning("Code server already running")
            return

        # Build environment
        env = os.environ.copy()
        env.update(self.env)

        # Start code app-server
        # The 'code' binary with no arguments defaults to TUI mode
        # We need to use 'code app-server' mode for JSON-RPC
        cmd = [self.code_binary_path, "app-server"]

        logger.info(f"Starting Code app-server: {' '.join(cmd)}")
        logger.info(f"Working directory: {self.working_dir}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=env
            )

            logger.info(f"Code app-server started with PID {self.process.pid}")

        except FileNotFoundError:
            raise RuntimeError(
                f"Code binary not found at: {self.code_binary_path}. "
                "Please build the project or set CODE_BINARY_PATH."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start Code app-server: {e}")

    async def stop(self) -> None:
        """Stop the Code app-server process gracefully"""
        if not self.process:
            return

        logger.info("Stopping Code app-server...")

        try:
            # Try graceful shutdown first
            if self.process.returncode is None:
                try:
                    # Send shutdown request if possible
                    await self.send_request("shutdown", {}, timeout=5.0)
                except Exception as e:
                    logger.warning(f"Error sending shutdown request: {e}")

                # Wait for graceful exit
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    logger.info("Code app-server exited gracefully")
                    return
                except asyncio.TimeoutError:
                    logger.warning("Graceful shutdown timed out")

            # Force termination
            if self.process.returncode is None:
                logger.warning("Force terminating Code app-server")
                self.process.terminate()

                try:
                    await asyncio.wait_for(self.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.error("Termination timed out, killing process")
                    self.process.kill()
                    await self.process.wait()

        except Exception as e:
            logger.error(f"Error stopping Code app-server: {e}")
        finally:
            self.process = None

    async def send_request(
        self,
        method: str,
        params: Dict[str, Any],
        timeout: float = 30.0
    ) -> Any:
        """
        Send a JSON-RPC request and wait for response

        Args:
            method: JSON-RPC method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response result

        Raises:
            RuntimeError: If server not running or request fails
            asyncio.TimeoutError: If request times out
        """
        if not self.process or self.process.returncode is not None:
            raise RuntimeError("Code app-server not running")

        # Generate request ID
        self.request_id += 1
        req_id = str(self.request_id)

        # Build JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future

        # Send request
        try:
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)

            # Check for error
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"Code error: {error.get('message', error)}")

            return response.get("result")

        except asyncio.TimeoutError:
            del self.pending_requests[req_id]
            raise
        except Exception as e:
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
            raise RuntimeError(f"Request failed: {e}")

    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC notification (no response expected)

        Args:
            method: JSON-RPC method name
            params: Method parameters
        """
        if not self.process or self.process.returncode is not None:
            raise RuntimeError("Code app-server not running")

        # Build JSON-RPC notification (no id field)
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        # Send notification
        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json.encode())
        await self.process.stdin.drain()

    async def stream_events(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream events from Code app-server

        Yields:
            JSON-RPC events/notifications from server

        This is an async generator that reads from stdout and yields
        parsed JSON events. It handles both responses and notifications.
        """
        if not self.process or not self.process.stdout:
            raise RuntimeError("Code app-server not running")

        logger.info("Starting event stream from Code app-server")

        try:
            while True:
                # Read line from stdout
                line = await self.process.stdout.readline()

                if not line:
                    # EOF - process exited
                    logger.info("Code app-server stdout closed")
                    break

                try:
                    # Parse JSON
                    event = json.loads(line.decode().strip())

                    # Check if this is a response to a pending request
                    if "id" in event and event["id"] in self.pending_requests:
                        # This is a response - resolve the future
                        future = self.pending_requests.pop(event["id"])
                        if not future.done():
                            future.set_result(event)
                        continue

                    # This is a notification or unsolicited event - yield it
                    yield event

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from Code: {e}")
                    logger.debug(f"Invalid line: {line}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    continue

        except asyncio.CancelledError:
            logger.info("Event stream cancelled")
            raise
        except Exception as e:
            logger.error(f"Event stream error: {e}")
            raise
        finally:
            logger.info("Event stream ended")

    async def monitor_stderr(self) -> None:
        """Monitor stderr for errors and warnings"""
        if not self.process or not self.process.stderr:
            return

        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break

                stderr_line = line.decode().strip()
                if stderr_line:
                    logger.warning(f"Code stderr: {stderr_line}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring stderr: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    def is_running(self) -> bool:
        """Check if the Code app-server is running"""
        return self.process is not None and self.process.returncode is None

    async def initialize_session(
        self,
        client_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a new Code session

        Args:
            client_info: Optional client information

        Returns:
            Session initialization response
        """
        params = {
            "clientInfo": client_info or {
                "name": "code-pipeline",
                "version": "0.1.0"
            }
        }

        return await self.send_request("initialize", params)

    async def new_conversation(
        self,
        working_dir: Optional[str] = None
    ) -> str:
        """
        Create a new conversation

        Args:
            working_dir: Working directory for the conversation

        Returns:
            Conversation ID
        """
        params = {
            "workingDir": working_dir or self.working_dir
        }

        response = await self.send_request("newConversation", params)
        return response.get("conversationId")

    async def send_user_message(
        self,
        conversation_id: str,
        message: str,
        images: Optional[list] = None
    ) -> None:
        """
        Send a user message to the conversation

        Args:
            conversation_id: Conversation ID
            message: User message text
            images: Optional list of image paths
        """
        params = {
            "conversationId": conversation_id,
            "params": {
                "items": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        }

        if images:
            for img_path in images:
                params["params"]["items"].append({
                    "type": "image",
                    "path": img_path
                })

        await self.send_request("sendUserMessage", params)
