"""
Enhanced Event Translator with Rich Media Support

Extends the base translator to handle:
- Browser screenshots (base64 encoding)
- ANSI-formatted terminal output
- File diffs with syntax highlighting
- Auto Drive decision trees
"""

import base64
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from utils.event_translator import CodeEventTranslator, OpenAIEvent, EventType


class EnhancedCodeEventTranslator(CodeEventTranslator):
    """Enhanced translator with rich media support"""

    def __init__(self):
        super().__init__()
        self.screenshot_cache: Dict[str, str] = {}
        self.ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def _handle_browser_screenshot_update(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle browser screenshot with base64 encoding"""
        screenshot = msg.get("screenshot", {})

        # Get screenshot data
        image_data = screenshot.get("data")
        image_path = screenshot.get("path")

        # Encode image as base64 if it's a file path
        if image_path and Path(image_path).exists():
            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                    image_data = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
                    self.screenshot_cache[image_path] = image_data
            except Exception as e:
                print(f"Error encoding screenshot: {e}")
                return []
        elif image_path in self.screenshot_cache:
            image_data = self.screenshot_cache[image_path]

        if not image_data:
            return []

        # Create OpenAI event with image attachment
        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "object": "thread.message.delta",
                    "delta": {
                        "role": "assistant",
                        "content": [{
                            "type": "image",
                            "image_url": {
                                "url": image_data,
                                "detail": "auto"
                            }
                        }],
                        "metadata": {
                            "browser_screenshot": {
                                "url": screenshot.get("url"),
                                "title": screenshot.get("title"),
                                "timestamp": screenshot.get("timestamp"),
                                "viewport": screenshot.get("viewport")
                            }
                        }
                    }
                }
            )
        ]

    def _handle_exec_output_with_ansi(
        self,
        msg: Dict[str, Any]
    ) -> List[OpenAIEvent]:
        """Handle terminal output with ANSI color codes"""
        chunk = msg.get("chunk", "")
        is_stderr = msg.get("is_stderr", False)

        # Parse ANSI codes for styling
        styled_output = self._parse_ansi_codes(chunk)

        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "object": "thread.message.delta",
                    "delta": {
                        "role": "assistant",
                        "content": [{
                            "type": "terminal_output",
                            "text": chunk,
                            "styled": styled_output,
                            "is_stderr": is_stderr
                        }]
                    }
                }
            )
        ]

    def _parse_ansi_codes(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse ANSI escape codes into styled segments

        Returns list of segments with text and style information
        """
        segments = []
        current_styles = []
        last_end = 0

        # Find all ANSI codes
        for match in self.ansi_escape_pattern.finditer(text):
            # Add text before this code
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    segments.append({
                        "text": plain_text,
                        "styles": current_styles.copy()
                    })

            # Parse the ANSI code
            code = match.group(0)
            style = self._parse_ansi_code(code)

            if style:
                if style == "reset":
                    current_styles = []
                else:
                    current_styles.append(style)

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            plain_text = text[last_end:]
            if plain_text:
                segments.append({
                    "text": plain_text,
                    "styles": current_styles.copy()
                })

        return segments

    def _parse_ansi_code(self, code: str) -> Optional[str]:
        """Parse a single ANSI escape code"""
        # Extract the numeric code
        match = re.search(r'\[(\d+)m', code)
        if not match:
            return None

        num = int(match.group(1))

        # Map common codes to styles
        ansi_map = {
            0: "reset",
            1: "bold",
            2: "dim",
            3: "italic",
            4: "underline",
            30: "black",
            31: "red",
            32: "green",
            33: "yellow",
            34: "blue",
            35: "magenta",
            36: "cyan",
            37: "white",
            90: "bright-black",
            91: "bright-red",
            92: "bright-green",
            93: "bright-yellow",
            94: "bright-blue",
            95: "bright-magenta",
            96: "bright-cyan",
            97: "bright-white"
        }

        return ansi_map.get(num)

    def _handle_patch_with_diff(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle file patch with formatted diff"""
        call_id = msg.get("call_id", str(int(time.time() * 1000)))
        changes = msg.get("changes", [])
        diff_text = msg.get("diff", "")

        # Format diff with syntax highlighting hints
        formatted_diff = self._format_diff(diff_text)

        self.current_tool_calls[call_id] = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": "file_edit",
                "arguments": json.dumps({
                    "changes": changes,
                    "diff": formatted_diff
                })
            }
        }

        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{call_id}",
                    "object": "thread.message.delta",
                    "delta": {
                        "role": "assistant",
                        "tool_calls": [self.current_tool_calls[call_id]]
                    }
                }
            )
        ]

    def _format_diff(self, diff_text: str) -> str:
        """Format diff text with markers for syntax highlighting"""
        if not diff_text:
            return ""

        lines = diff_text.split('\n')
        formatted_lines = []

        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                formatted_lines.append(f"<diff-header>{line}</diff-header>")
            elif line.startswith('+'):
                formatted_lines.append(f"<diff-add>{line}</diff-add>")
            elif line.startswith('-'):
                formatted_lines.append(f"<diff-remove>{line}</diff-remove>")
            elif line.startswith('@@'):
                formatted_lines.append(f"<diff-hunk>{line}</diff-hunk>")
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _handle_auto_drive_decision_tree(
        self,
        msg: Dict[str, Any]
    ) -> List[OpenAIEvent]:
        """Handle Auto Drive decision with structured tree format"""
        status = msg.get("status")
        progress = msg.get("progress", {})
        agents = msg.get("agents", [])
        decision = msg.get("decision", {})

        # Create a structured representation of the decision
        decision_tree = {
            "status": status,
            "progress": progress,
            "agents": agents,
            "decision": decision,
            "timestamp": int(time.time() * 1000)
        }

        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "object": "thread.message.delta",
                    "delta": {
                        "role": "assistant",
                        "content": [{
                            "type": "auto_drive_decision",
                            "data": decision_tree
                        }]
                    }
                }
            )
        ]

    def translate(self, code_event: Dict[str, Any]) -> List[OpenAIEvent]:
        """
        Enhanced translate with rich media support

        Overrides base translate to add rich media handlers
        """
        # Get message
        if "method" in code_event:
            params = code_event.get("params", {})
            msg = params.get("msg", {})
            event_type = msg.get("type")
        elif "msg" in code_event:
            msg = code_event["msg"]
            event_type = msg.get("type")
        else:
            return []

        # Check for rich media events first
        if event_type == "browser_screenshot_update":
            return self._handle_browser_screenshot_update(msg)
        elif event_type == "exec_command_output_delta":
            return self._handle_exec_output_with_ansi(msg)
        elif event_type == "patch_apply_begin" and msg.get("diff"):
            return self._handle_patch_with_diff(msg)
        elif event_type == "auto_coordinator_decision":
            return self._handle_auto_drive_decision_tree(msg)

        # Fall back to base implementation
        return super().translate(code_event)


# Helper functions for frontend integration

def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def encode_image_file(file_path: str) -> Optional[str]:
    """Encode image file as base64 data URL"""
    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
            return f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


import time
import json

