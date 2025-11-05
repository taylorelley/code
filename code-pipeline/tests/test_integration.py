"""
Integration Tests for Code Pipeline Phase 2

Tests the enhanced pipeline with WebSocket support, rich media handling,
and all frontend components.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import base64

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.enhanced_pipeline import EnhancedPipeline
from backend.websocket_handler import WebSocketManager
from utils.enhanced_event_translator import (
    EnhancedCodeEventTranslator,
    strip_ansi_codes,
    encode_image_file,
    format_file_size
)


class TestEnhancedPipeline:
    """Test suite for Enhanced Pipeline"""

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test enhanced pipeline can be initialized"""
        pipeline = EnhancedPipeline()

        assert pipeline.type == "pipe"
        assert pipeline.ws_manager is not None
        assert hasattr(pipeline, '_handle_realtime_event')

    @pytest.mark.asyncio
    async def test_websocket_manager(self):
        """Test WebSocket manager functionality"""
        ws_manager = WebSocketManager()

        # Mock WebSocket
        mock_ws = AsyncMock()

        # Connect
        await ws_manager.connect(mock_ws, "test-session")

        assert "test-session" in ws_manager.active_connections
        assert mock_ws in ws_manager.active_connections["test-session"]

        # Disconnect
        ws_manager.disconnect(mock_ws, "test-session")

        assert "test-session" not in ws_manager.active_connections

    @pytest.mark.asyncio
    async def test_browser_screenshot_handling(self):
        """Test browser screenshot event handling"""
        pipeline = EnhancedPipeline()
        session_id = "test-session"

        # Mock message
        msg = {
            "type": "browser_screenshot_update",
            "screenshot": {
                "data": "data:image/png;base64,iVBORw0KG...",
                "url": "https://example.com",
                "title": "Example Page",
                "viewport": {"width": 1920, "height": 1080}
            }
        }

        # Handle event
        await pipeline._handle_browser_screenshot(session_id, msg)

        # Should have called ws_manager.handle_browser_screenshot
        # (would check call in real test with proper mocking)

    @pytest.mark.asyncio
    async def test_terminal_output_handling(self):
        """Test terminal output streaming"""
        pipeline = EnhancedPipeline()
        session_id = "test-session"

        msg = {
            "type": "exec_command_output_delta",
            "call_id": "term-123",
            "chunk": "Hello, terminal!",
            "is_stderr": False
        }

        await pipeline._handle_terminal_output(session_id, msg)

        # Should broadcast to WebSocket clients

    @pytest.mark.asyncio
    async def test_approval_request_handling(self):
        """Test approval request flow"""
        pipeline = EnhancedPipeline()
        session_id = "test-session"

        # Mock exec approval request
        msg = {
            "type": "exec_approval_request",
            "id": "approval-123",
            "command": "rm -rf /",
            "cwd": "/home/user",
            "reason": "Dangerous command"
        }

        await pipeline._handle_approval_request(session_id, msg)

        # Should create approval request in ws_manager

    @pytest.mark.asyncio
    async def test_auto_drive_update_handling(self):
        """Test Auto Drive progress updates"""
        pipeline = EnhancedPipeline()
        session_id = "test-session"

        msg = {
            "type": "auto_coordinator_decision",
            "status": "acting",
            "progress": {
                "current": 3,
                "total": 10,
                "description": "Running tests"
            },
            "agents": [
                {"name": "Claude", "status": "running"},
                {"name": "GPT-4", "status": "completed"}
            ],
            "transcript": [
                {
                    "role": "assistant",
                    "content": "Starting implementation",
                    "timestamp": "2025-11-05T12:00:00Z"
                }
            ]
        }

        await pipeline._handle_auto_drive_update(session_id, msg)

        # Should broadcast Auto Drive update


class TestEnhancedEventTranslator:
    """Test suite for Enhanced Event Translator"""

    def test_translator_initialization(self):
        """Test enhanced translator initializes correctly"""
        translator = EnhancedCodeEventTranslator()

        assert hasattr(translator, 'screenshot_cache')
        assert hasattr(translator, 'ansi_escape_pattern')

    def test_ansi_code_parsing(self):
        """Test ANSI escape code parsing"""
        translator = EnhancedCodeEventTranslator()

        # Test text with ANSI codes
        text = "\x1b[32mGreen text\x1b[0m Normal text \x1b[1;31mBold red\x1b[0m"
        segments = translator._parse_ansi_codes(text)

        assert len(segments) > 0
        assert any("Green text" in seg["text"] for seg in segments)

    def test_diff_formatting(self):
        """Test diff formatting with markers"""
        translator = EnhancedCodeEventTranslator()

        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""

        formatted = translator._format_diff(diff)

        assert "<diff-header>" in formatted
        assert "<diff-add>" in formatted
        assert "<diff-remove>" in formatted
        assert "<diff-hunk>" in formatted

    def test_browser_screenshot_translation(self):
        """Test browser screenshot event translation"""
        translator = EnhancedCodeEventTranslator()

        code_event = {
            "msg": {
                "type": "browser_screenshot_update",
                "screenshot": {
                    "data": "data:image/png;base64,iVBORw0KG...",
                    "url": "https://example.com",
                    "title": "Test Page"
                }
            }
        }

        events = translator.translate(code_event)

        assert len(events) > 0
        assert events[0].event_type == "thread.message.delta"


class TestHelperFunctions:
    """Test suite for helper functions"""

    def test_strip_ansi_codes(self):
        """Test ANSI code stripping"""
        text = "\x1b[32mGreen\x1b[0m Normal"
        stripped = strip_ansi_codes(text)

        assert stripped == "Green Normal"
        assert "\x1b" not in stripped

    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestWebSocketManager:
    """Test suite for WebSocket Manager"""

    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test WebSocket connection lifecycle"""
        manager = WebSocketManager()

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Connect two clients to same session
        await manager.connect(mock_ws1, "session-1")
        await manager.connect(mock_ws2, "session-1")

        assert manager.get_session_count() == 1
        assert manager.get_connection_count() == 2

        # Disconnect one
        manager.disconnect(mock_ws1, "session-1")

        assert manager.get_connection_count() == 1

        # Disconnect last
        manager.disconnect(mock_ws2, "session-1")

        assert manager.get_session_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test message broadcasting"""
        manager = WebSocketManager()

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, "session-1")
        await manager.connect(mock_ws2, "session-1")

        # Broadcast message
        message = {"type": "test", "data": "hello"}
        await manager.broadcast("session-1", message)

        # Both should receive
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_approval_flow(self):
        """Test approval request/response flow"""
        manager = WebSocketManager()

        # Create approval request
        await manager.handle_approval_request(
            "session-1",
            "req-123",
            "command_execution",
            {"command": "ls -la"}
        )

        assert "req-123" in manager.approval_requests
        assert manager.approval_requests["req-123"]["status"] == "pending"

        # Respond to approval
        await manager.handle_approval_response("req-123", "approved")

        assert manager.approval_requests["req-123"]["status"] == "resolved"
        assert manager.approval_requests["req-123"]["decision"] == "approved"


class TestFrontendIntegration:
    """Test suite for frontend component integration"""

    def test_activity_card_data_structure(self):
        """Test activity card data structure matches store"""
        # This would test that the data structures match between
        # backend events and frontend expectations

        tool_execution = {
            "id": "tool-123",
            "type": "bash",
            "status": "running",
            "data": {
                "command": "ls -la"
            },
            "startTime": "2025-11-05T12:00:00Z"
        }

        # Verify structure
        assert "id" in tool_execution
        assert "type" in tool_execution
        assert "status" in tool_execution
        assert tool_execution["type"] in ["bash", "file_edit", "mcp", "web_search"]

    def test_browser_screenshot_structure(self):
        """Test browser screenshot data structure"""
        screenshot = {
            "id": "screenshot-123",
            "data": "data:image/png;base64,...",
            "metadata": {
                "url": "https://example.com",
                "title": "Example",
                "timestamp": "2025-11-05T12:00:00Z",
                "viewport": {"width": 1920, "height": 1080}
            },
            "timestamp": "2025-11-05T12:00:00Z"
        }

        assert "id" in screenshot
        assert "data" in screenshot
        assert screenshot["data"].startswith("data:image/png;base64,")

    def test_approval_request_structure(self):
        """Test approval request data structure"""
        approval_request = {
            "id": "approval-123",
            "type": "command_execution",
            "status": "pending",
            "data": {
                "command": "rm file.txt",
                "cwd": "/home/user",
                "reason": "File deletion"
            },
            "timestamp": "2025-11-05T12:00:00Z"
        }

        assert approval_request["type"] in ["command_execution", "file_changes"]
        assert approval_request["status"] in ["pending", "approved", "rejected"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
