"""
Event Translator: Code JSON-RPC Events → OpenAI SSE Format

This module translates between Code's rich JSON-RPC event protocol and
OpenAI's Server-Sent Events (SSE) format used by chat completion streams.

Event Mapping Reference:
- session_configured → thread.created
- task_started → thread.run.created
- agent_message → thread.message.delta (final)
- agent_message_delta → thread.message.delta
- agent_reasoning → metadata
- exec_command_begin → function_call (bash)
- patch_apply_begin → function_call (file_edit)
- token_count → usage statistics
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
import time


class EventType(str, Enum):
    """OpenAI SSE event types"""
    THREAD_CREATED = "thread.created"
    THREAD_RUN_CREATED = "thread.run.created"
    THREAD_RUN_IN_PROGRESS = "thread.run.in_progress"
    THREAD_RUN_COMPLETED = "thread.run.completed"
    THREAD_MESSAGE_DELTA = "thread.message.delta"
    THREAD_MESSAGE_COMPLETED = "thread.message.completed"
    DONE = "done"
    ERROR = "error"


class OpenAIEvent:
    """Represents an OpenAI-compatible SSE event"""

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or str(int(time.time() * 1000))

    def to_sse_format(self) -> str:
        """Convert to SSE format string"""
        lines = []

        if self.event_id:
            lines.append(f"id: {self.event_id}")

        lines.append(f"event: {self.event_type}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to end event

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for non-SSE responses"""
        return {
            "event": self.event_type,
            "data": self.data,
            "id": self.event_id
        }


class CodeEventTranslator:
    """Translates Code events to OpenAI-compatible format"""

    def __init__(self):
        self.session_id: Optional[str] = None
        self.run_id: Optional[str] = None
        self.message_buffer: List[str] = []
        self.reasoning_buffer: List[str] = []
        self.current_tool_calls: Dict[str, Dict[str, Any]] = {}

    def translate(self, code_event: Dict[str, Any]) -> List[OpenAIEvent]:
        """
        Translate a Code event to one or more OpenAI events

        Args:
            code_event: Raw event from Code app-server

        Returns:
            List of OpenAI-compatible events
        """
        # Handle JSON-RPC notification format
        if "method" in code_event:
            # This is a server notification
            params = code_event.get("params", {})
            msg = params.get("msg", {})
            event_type = msg.get("type")
        elif "msg" in code_event:
            # Direct event format
            msg = code_event["msg"]
            event_type = msg.get("type")
        else:
            # Unknown format
            return []

        # Map to appropriate handler
        handler_map = {
            "session_configured": self._handle_session_configured,
            "task_started": self._handle_task_started,
            "task_complete": self._handle_task_complete,
            "agent_message": self._handle_agent_message,
            "agent_message_delta": self._handle_agent_message_delta,
            "agent_reasoning": self._handle_agent_reasoning,
            "agent_reasoning_delta": self._handle_agent_reasoning_delta,
            "exec_command_begin": self._handle_exec_begin,
            "exec_command_end": self._handle_exec_end,
            "exec_command_output_delta": self._handle_exec_output,
            "patch_apply_begin": self._handle_patch_begin,
            "patch_apply_end": self._handle_patch_end,
            "mcp_tool_call_begin": self._handle_mcp_begin,
            "mcp_tool_call_end": self._handle_mcp_end,
            "web_search_begin": self._handle_web_search_begin,
            "web_search_end": self._handle_web_search_end,
            "token_count": self._handle_token_count,
            "error": self._handle_error,
            "turn_aborted": self._handle_turn_aborted,
        }

        handler = handler_map.get(event_type)
        if handler:
            return handler(msg)

        # Unknown event type - log but don't fail
        return []

    def _handle_session_configured(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle session_configured → thread.created"""
        self.session_id = msg.get("conversation_id", str(int(time.time() * 1000)))

        return [
            OpenAIEvent(
                EventType.THREAD_CREATED,
                {
                    "id": self.session_id,
                    "object": "thread",
                    "created_at": int(time.time()),
                    "metadata": {}
                }
            )
        ]

    def _handle_task_started(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle task_started → thread.run.created"""
        self.run_id = f"run_{int(time.time() * 1000)}"

        return [
            OpenAIEvent(
                EventType.THREAD_RUN_CREATED,
                {
                    "id": self.run_id,
                    "object": "thread.run",
                    "created_at": int(time.time()),
                    "thread_id": self.session_id,
                    "status": "in_progress",
                    "model_context_window": msg.get("model_context_window")
                }
            )
        ]

    def _handle_task_complete(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle task_complete → thread.run.completed"""
        events = []

        # Flush any buffered message content
        if self.message_buffer:
            events.append(self._create_message_event("".join(self.message_buffer), True))
            self.message_buffer.clear()

        # Send run completed
        events.append(
            OpenAIEvent(
                EventType.THREAD_RUN_COMPLETED,
                {
                    "id": self.run_id,
                    "object": "thread.run",
                    "status": "completed",
                    "completed_at": int(time.time()),
                    "last_error": None
                }
            )
        )

        # Send done signal
        events.append(
            OpenAIEvent(
                EventType.DONE,
                {"[DONE]": True}
            )
        )

        return events

    def _handle_agent_message(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle agent_message → final message"""
        message = msg.get("message", "")
        return [self._create_message_event(message, is_final=True)]

    def _handle_agent_message_delta(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle agent_message_delta → streaming delta"""
        delta = msg.get("delta", "")
        self.message_buffer.append(delta)

        return [self._create_message_event(delta, is_final=False)]

    def _handle_agent_reasoning(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle agent_reasoning → metadata"""
        text = msg.get("text", "")

        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "object": "thread.message.delta",
                    "delta": {
                        "role": "assistant",
                        "content": [{
                            "type": "text",
                            "text": {
                                "value": "",
                                "annotations": [{
                                    "type": "reasoning",
                                    "text": text
                                }]
                            }
                        }]
                    }
                }
            )
        ]

    def _handle_agent_reasoning_delta(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle streaming reasoning"""
        delta = msg.get("delta", "")
        self.reasoning_buffer.append(delta)

        # For now, accumulate and send with regular message
        # In production, could send as separate metadata stream
        return []

    def _handle_exec_begin(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle exec_command_begin → function_call start"""
        call_id = msg.get("call_id", str(int(time.time() * 1000)))
        command = msg.get("command", "")

        self.current_tool_calls[call_id] = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": "bash",
                "arguments": json.dumps({"command": command})
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

    def _handle_exec_end(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle exec_command_end → function_call complete"""
        call_id = msg.get("call_id", "")
        exit_code = msg.get("exit_code")

        if call_id in self.current_tool_calls:
            tool_call = self.current_tool_calls[call_id]
            tool_call["status"] = "completed" if exit_code == 0 else "failed"
            tool_call["exit_code"] = exit_code

            del self.current_tool_calls[call_id]

        return []  # Could send completion event if needed

    def _handle_exec_output(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle exec output streaming"""
        # For now, accumulate output
        # In production, could stream to client
        return []

    def _handle_patch_begin(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle patch_apply_begin → file edit function call"""
        call_id = msg.get("call_id", str(int(time.time() * 1000)))
        changes = msg.get("changes", [])

        self.current_tool_calls[call_id] = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": "file_edit",
                "arguments": json.dumps({"changes": changes})
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

    def _handle_patch_end(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle patch completion"""
        call_id = msg.get("call_id", "")

        if call_id in self.current_tool_calls:
            del self.current_tool_calls[call_id]

        return []

    def _handle_mcp_begin(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle MCP tool call begin"""
        call_id = msg.get("call_id", str(int(time.time() * 1000)))
        invocation = msg.get("invocation", {})

        self.current_tool_calls[call_id] = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": f"mcp_{invocation.get('server')}_{invocation.get('tool')}",
                "arguments": json.dumps(invocation.get("arguments", {}))
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

    def _handle_mcp_end(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle MCP tool call completion"""
        call_id = msg.get("call_id", "")

        if call_id in self.current_tool_calls:
            del self.current_tool_calls[call_id]

        return []

    def _handle_web_search_begin(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle web search begin"""
        call_id = msg.get("call_id", str(int(time.time() * 1000)))

        self.current_tool_calls[call_id] = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": "web_search",
                "arguments": json.dumps({})
            }
        }

        return []

    def _handle_web_search_end(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle web search completion"""
        call_id = msg.get("call_id", "")
        query = msg.get("query", "")

        if call_id in self.current_tool_calls:
            self.current_tool_calls[call_id]["function"]["arguments"] = json.dumps({
                "query": query
            })
            del self.current_tool_calls[call_id]

        return []

    def _handle_token_count(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle token_count → usage statistics"""
        info = msg.get("info", {})
        if not info:
            return []

        total_usage = info.get("total_token_usage", {})

        return [
            OpenAIEvent(
                EventType.THREAD_MESSAGE_DELTA,
                {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "object": "thread.message.delta",
                    "delta": {},
                    "usage": {
                        "prompt_tokens": total_usage.get("input_tokens", 0),
                        "completion_tokens": total_usage.get("output_tokens", 0),
                        "total_tokens": total_usage.get("total_tokens", 0)
                    }
                }
            )
        ]

    def _handle_error(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle error event"""
        message = msg.get("message", "Unknown error")

        return [
            OpenAIEvent(
                EventType.ERROR,
                {
                    "error": {
                        "message": message,
                        "type": "code_error",
                        "code": "internal_error"
                    }
                }
            )
        ]

    def _handle_turn_aborted(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
        """Handle turn abortion"""
        reason = msg.get("reason", {})

        return [
            OpenAIEvent(
                EventType.ERROR,
                {
                    "error": {
                        "message": f"Turn aborted: {reason}",
                        "type": "turn_aborted",
                        "code": "aborted"
                    }
                }
            )
        ]

    def _create_message_event(
        self,
        content: str,
        is_final: bool = False
    ) -> OpenAIEvent:
        """Create a message delta event"""
        event_type = EventType.THREAD_MESSAGE_COMPLETED if is_final else EventType.THREAD_MESSAGE_DELTA

        return OpenAIEvent(
            event_type,
            {
                "id": f"msg_{int(time.time() * 1000)}",
                "object": f"thread.message.{('completed' if is_final else 'delta')}",
                "delta": {
                    "role": "assistant",
                    "content": [{
                        "type": "text",
                        "text": {
                            "value": content
                        }
                    }]
                }
            }
        )
