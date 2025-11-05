"""
Settings Manager - Persist and manage Code Pipeline settings per session

Handles:
- Settings persistence to disk
- Real-time settings sync via WebSocket
- Settings validation
- Default configuration management
"""

import json
import os
import copy
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages Code Pipeline settings for a specific session"""

    DEFAULT_SETTINGS = {
        "model": {
            "provider": "anthropic",
            "name": "claude-sonnet-4-20250514",
            "reasoningEffort": "medium",
            "maxTokens": 8192,
            "temperature": 0.7,
        },
        "tools": {
            "bash": True,
            "browser": True,
            "mcp": True,
            "computer": False,
            "webSearch": True,
        },
        "mcpServers": [],
        "autoDrive": {
            "enabled": True,
            "maxSteps": 10,
            "requireApproval": True,
            "maxParallelAgents": 3,
        },
        "browser": {
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
            "userAgent": None,
        },
        "terminal": {
            "shell": "/bin/bash",
            "fontSize": 14,
            "fontFamily": 'Menlo, Monaco, "Courier New", monospace',
            "theme": "dark",
            "cursorBlink": True,
            "scrollback": 1000,
        },
        "workspace": {
            "path": "",
            "gitEnabled": True,
            "autoSave": True,
        },
    }

    def __init__(self, session_id: str, base_dir: str = "./sessions"):
        """
        Initialize settings manager for a session

        Args:
            session_id: Unique session identifier
            base_dir: Base directory for session storage
        """
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_dir = self.base_dir / session_id
        self.settings_file = self.session_dir / "settings.json"
        self._ensure_session_dir()

    def _ensure_session_dir(self):
        """Ensure session directory exists"""
        self.session_dir.mkdir(parents=True, exist_ok=True)

    async def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from disk

        Returns:
            Settings dictionary (defaults if file doesn't exist)
        """
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                logger.info(f"Loaded settings for session {self.session_id}")
                return self._merge_with_defaults(settings)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                return self.get_default_settings()
        else:
            logger.info(f"No settings file found for session {self.session_id}, using defaults")
            return self.get_default_settings()

    async def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Persist settings to disk

        Args:
            settings: Settings dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate settings before saving
            if not self._validate_settings(settings):
                logger.error("Settings validation failed")
                return False

            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)

            logger.info(f"Saved settings for session {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    async def update_setting(self, path: str, value: Any) -> bool:
        """
        Update a specific setting by path

        Args:
            path: Dot-separated path (e.g., "model.provider")
            value: New value

        Returns:
            True if successful
        """
        settings = await self.load_settings()

        # Navigate to the setting location
        keys = path.split(".")
        current = settings
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

        return await self.save_settings(settings)

    def _merge_with_defaults(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user settings with defaults (to handle new settings)

        Args:
            settings: User settings

        Returns:
            Merged settings
        """
        def merge_dicts(base: dict, overlay: dict) -> dict:
            result = base.copy()
            for key, value in overlay.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result

        return merge_dicts(self.DEFAULT_SETTINGS, settings)

    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Validate settings structure and values

        Args:
            settings: Settings to validate

        Returns:
            True if valid
        """
        # Check required top-level keys
        required_keys = ["model", "tools", "autoDrive", "browser", "terminal", "workspace"]
        for key in required_keys:
            if key not in settings:
                logger.error(f"Missing required settings key: {key}")
                return False

        # Validate model settings
        if "provider" not in settings["model"]:
            return False
        if settings["model"]["provider"] not in ["anthropic", "openai", "google"]:
            logger.error(f"Invalid model provider: {settings['model']['provider']}")
            return False

        # Validate tool settings
        for tool in ["bash", "browser", "mcp", "computer", "webSearch"]:
            if tool not in settings["tools"]:
                return False
            if not isinstance(settings["tools"][tool], bool):
                logger.error(f"Tool {tool} must be boolean")
                return False

        # Validate MCP servers
        if "mcpServers" in settings:
            for server in settings["mcpServers"]:
                if not all(key in server for key in ["id", "name", "command", "enabled"]):
                    logger.error("Invalid MCP server configuration")
                    return False

        return True

    @staticmethod
    def get_default_settings() -> Dict[str, Any]:
        """Get default settings"""
        return copy.deepcopy(SettingsManager.DEFAULT_SETTINGS)

    async def reset_to_defaults(self) -> bool:
        """
        Reset settings to defaults

        Returns:
            True if successful
        """
        return await self.save_settings(self.get_default_settings())

    async def export_settings(self) -> str:
        """
        Export settings as JSON string

        Returns:
            JSON string of current settings
        """
        settings = await self.load_settings()
        return json.dumps(settings, indent=2)

    async def import_settings(self, settings_json: str) -> bool:
        """
        Import settings from JSON string

        Args:
            settings_json: JSON string of settings

        Returns:
            True if successful
        """
        try:
            settings = json.loads(settings_json)
            return await self.save_settings(settings)
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False


# Singleton registry for settings managers
_settings_managers: Dict[str, SettingsManager] = {}


def get_settings_manager(session_id: str) -> SettingsManager:
    """
    Get or create settings manager for a session

    Args:
        session_id: Session identifier

    Returns:
        SettingsManager instance
    """
    if session_id not in _settings_managers:
        _settings_managers[session_id] = SettingsManager(session_id)
    return _settings_managers[session_id]
