"""
WebSocket Handler for Code Pipeline

Provides real-time bidirectional communication for:
- Terminal I/O streaming
- Approval flow interactions
- Browser events
- Auto Drive progress updates
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""

    def __init__(self):
        # Active connections: session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Terminal sessions: session_id -> terminal state
        self.terminal_sessions: Dict[str, Dict[str, Any]] = {}

        # Approval requests: request_id -> approval state
        self.approval_requests: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a WebSocket client"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up if no more connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                logger.info(f"Last connection closed for session {session_id}")

    async def broadcast(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a session"""
        if session_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, session_id)

    async def send(self, session_id: str, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.disconnect(websocket, session_id)

    async def handle_terminal_input(
        self,
        session_id: str,
        terminal_id: str,
        input_data: str
    ):
        """Handle terminal input from client"""
        logger.debug(f"Terminal input for {terminal_id}: {input_data[:50]}")

        # Broadcast to Code backend (via callback if registered)
        if hasattr(self, 'terminal_input_callback'):
            await self.terminal_input_callback(session_id, terminal_id, input_data)

    async def handle_terminal_output(
        self,
        session_id: str,
        terminal_id: str,
        output_data: str,
        is_stderr: bool = False
    ):
        """Handle terminal output from Code backend"""
        message = {
            "type": "terminal_output",
            "terminal_id": terminal_id,
            "data": output_data,
            "is_stderr": is_stderr,
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast(session_id, message)

    async def handle_approval_request(
        self,
        session_id: str,
        request_id: str,
        request_type: str,
        request_data: Dict[str, Any]
    ):
        """Handle approval request from Code backend"""
        # Store approval request
        self.approval_requests[request_id] = {
            "session_id": session_id,
            "request_type": request_type,
            "data": request_data,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # Broadcast to clients
        message = {
            "type": "approval_request",
            "request_id": request_id,
            "request_type": request_type,
            "data": request_data
        }

        await self.broadcast(session_id, message)

    async def handle_approval_response(
        self,
        request_id: str,
        decision: str,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle approval response from client"""
        if request_id not in self.approval_requests:
            raise ValueError(f"Unknown approval request: {request_id}")

        request = self.approval_requests[request_id]
        request["status"] = "resolved"
        request["decision"] = decision
        request["user_data"] = user_data
        request["resolved_at"] = datetime.now().isoformat()

        # Broadcast confirmation
        session_id = request["session_id"]
        message = {
            "type": "approval_response",
            "request_id": request_id,
            "decision": decision
        }

        await self.broadcast(session_id, message)

        return request

    async def handle_browser_screenshot(
        self,
        session_id: str,
        screenshot_data: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Handle browser screenshot from Code backend"""
        message = {
            "type": "browser_screenshot",
            "data": screenshot_data,  # Base64 encoded
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast(session_id, message)

    async def handle_auto_drive_update(
        self,
        session_id: str,
        status: str,
        progress: Dict[str, Any],
        agents: Optional[list] = None,
        transcript: Optional[list] = None
    ):
        """Handle Auto Drive progress update"""
        message = {
            "type": "auto_drive_update",
            "status": status,
            "progress": progress,
            "agents": agents or [],
            "transcript": transcript or [],
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast(session_id, message)

    async def handle_tool_execution(
        self,
        session_id: str,
        tool_id: str,
        tool_type: str,
        status: str,
        data: Dict[str, Any]
    ):
        """Handle tool execution event"""
        message = {
            "type": "tool_execution",
            "tool_id": tool_id,
            "tool_type": tool_type,
            "status": status,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast(session_id, message)

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_connections)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint handler

    This should be called from FastAPI route:
    @app.websocket("/ws/{session_id}")
    async def websocket_route(websocket: WebSocket, session_id: str):
        await websocket_endpoint(websocket, session_id)
    """
    await ws_manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            # Route message to appropriate handler
            if message_type == "terminal_input":
                await ws_manager.handle_terminal_input(
                    session_id,
                    message.get("terminal_id"),
                    message.get("data")
                )

            elif message_type == "approval_response":
                await ws_manager.handle_approval_response(
                    message.get("request_id"),
                    message.get("decision"),
                    message.get("user_data")
                )

            elif message_type == "ping":
                # Heartbeat
                await ws_manager.send(session_id, websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        ws_manager.disconnect(websocket, session_id)
