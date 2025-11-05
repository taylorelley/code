"""Backend modules for Code Pipeline Phase 2"""

from .websocket_handler import ws_manager, websocket_endpoint, WebSocketManager
from .enhanced_pipeline import EnhancedPipeline

__all__ = [
    "ws_manager",
    "websocket_endpoint",
    "WebSocketManager",
    "EnhancedPipeline",
]
