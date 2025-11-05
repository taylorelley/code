# Integration Strategy: Code TUI + Open WebUI
## Enabling Agentic Coding Through Web UI

**Date:** 2025-11-05
**Status:** Proposed Strategy
**Goal:** Enable all Code project TUI features through Open WebUI's web interface

---

## Executive Summary

After comprehensive analysis of both projects, the **recommended approach is to create an Open WebUI Pipeline** that wraps Code's functionality, exposing all TUI features through the web interface. This approach:

✅ Preserves both projects' architectures
✅ Requires minimal modifications to either codebase
✅ Leverages existing integration points (Code's app-server + Open WebUI Pipelines)
✅ Enables rapid development and iteration
✅ Maintains compatibility with future updates

**Estimated Development Time:** 4-6 weeks for MVP, 8-12 weeks for feature parity

---

## Architecture Overview

### Current State

#### Code Project Architecture
```
┌─────────────────────────────────────────────────┐
│                  TUI Layer                      │
│  - Ratatui-based terminal interface             │
│  - Slash commands (/plan, /solve, /code, etc.) │
│  - Theme system & settings UI                   │
│  - Auto Drive orchestration                     │
│  - Browser integration display                  │
│  - Activity cards & overlays                    │
└──────────────────┬──────────────────────────────┘
                   │ AppEvent (JSON-RPC 2.0)
┌──────────────────▼──────────────────────────────┐
│              app-server (Rust)                  │
│  - JSON-RPC 2.0 over stdio (JSONL)              │
│  - Bidirectional communication                  │
│  - Used by VS Code extension                    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            Core Engine (Rust)                   │
│  - ConversationManager                          │
│  - Multi-agent orchestration                    │
│  - Browser automation (CDP)                     │
│  - Tool execution (bash, file ops, MCP)         │
│  - LLM provider integrations                    │
└─────────────────────────────────────────────────┘
```

#### Open WebUI Architecture
```
┌─────────────────────────────────────────────────┐
│          Svelte Frontend (Web UI)               │
│  - Chat interface                               │
│  - Document management                          │
│  - Settings & configuration                     │
│  - Real-time streaming                          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────────┐
│          Python Backend (FastAPI)               │
│  - User authentication & RBAC                   │
│  - Session management                           │
│  - Model provider routing                       │
└──────────────────┬──────────────────────────────┘
                   │ OpenAI-compatible API
┌──────────────────▼──────────────────────────────┐
│         Pipelines Framework (Python)            │
│  - Pipe pipelines (OpenAI API proxy)            │
│  - Filter pipelines (message processing)        │
│  - Custom logic integration                     │
│  - Port 9099, HTTP-based                        │
└─────────────────────────────────────────────────┘
```

### Proposed Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Open WebUI Frontend (Enhanced)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Chat         │  │ Code Panel   │  │ Settings     │         │
│  │ Interface    │  │ - Activity   │  │ - Themes     │         │
│  │              │  │ - Browser    │  │ - Agents     │         │
│  │              │  │ - Terminal   │  │ - Auto Drive │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket + Custom Events
┌────────────────────────────▼────────────────────────────────────┐
│                 Open WebUI Backend (Enhanced)                   │
│  - Route /code requests to Code Pipeline                        │
│  - WebSocket bridge for streaming events                        │
│  - Session persistence                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ OpenAI API + Extensions
┌────────────────────────────▼────────────────────────────────────┐
│             **NEW: Code Pipe Pipeline** (Python)                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ CodePipeline Class                                        │ │
│  │  - Spawns code app-server subprocess                      │ │
│  │  - JSON-RPC 2.0 communication via stdio                   │ │
│  │  - Event translation (Code events → OpenAI SSE format)    │ │
│  │  - Command dispatch (/plan, /solve, /code, /auto, etc.)  │ │
│  │  - State management (sessions, history)                   │ │
│  │  - Browser screenshot relay                               │ │
│  │  - Terminal output streaming                              │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ JSON-RPC 2.0 (stdio)
┌────────────────────────────▼────────────────────────────────────┐
│                 code app-server (Rust)                          │
│  - Existing component, no modifications needed                  │
│  - JSONL streaming over stdio                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Code Core Engine (Rust)                       │
│  - All existing functionality preserved                         │
│  - Multi-agent orchestration                                    │
│  - Browser automation                                           │
│  - Tool execution                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommended Approach: Code Pipe Pipeline

### Why This Approach?

1. **Leverages Existing Infrastructure**
   - Code's `app-server` already provides a rich JSON-RPC interface
   - Open WebUI's Pipelines framework is designed for exactly this use case
   - No major architectural changes to either project

2. **Feature Parity Achievable**
   - All Code events can be translated to Open WebUI format
   - UI components can be recreated in Svelte
   - State management handled by pipeline

3. **Maintains Project Independence**
   - Code project continues development independently
   - Open WebUI continues its roadmap
   - Integration layer is separate and upgradeable

4. **Deployment Flexibility**
   - Can run as single Docker container or separate services
   - Scales independently
   - Easy to debug and monitor

### Implementation Components

#### Component 1: Code Pipe Pipeline (`pipelines/code_pipeline.py`)

**Responsibilities:**
- Spawn and manage `code app-server` subprocess
- Translate JSON-RPC messages to/from OpenAI API format
- Handle session lifecycle and state persistence
- Stream events in real-time via Server-Sent Events (SSE)
- Relay browser screenshots and terminal output
- Manage slash command dispatch

**Key Features:**
```python
class CodePipeline:
    class Valves(BaseModel):
        CODE_BINARY_PATH: str = "/usr/local/bin/code"
        ENABLE_BROWSER: bool = True
        ENABLE_AUTO_DRIVE: bool = True
        MAX_CONCURRENT_SESSIONS: int = 10

    def __init__(self):
        self.type = "pipe"  # OpenAI API-compatible endpoint
        self.valves = self.Valves()
        self.sessions = {}  # Session ID → subprocess mapping

    async def pipe(self, body: dict) -> Union[str, Generator]:
        """Main entry point from Open WebUI"""
        # 1. Extract user message and session context
        # 2. Route to appropriate handler (slash command or chat)
        # 3. Stream events back to Open WebUI

    async def _handle_slash_command(self, command: str, args: str):
        """Handle /plan, /solve, /code, /auto, etc."""

    async def _stream_code_events(self, session_id: str):
        """Translate Code events → OpenAI SSE format"""
```

**Event Translation Map:**
```
Code Event                    → OpenAI/Open WebUI Format
─────────────────────────────────────────────────────────
session_configured            → thread.created
task_started                  → thread.run.created
agent_message                 → thread.message.delta (text)
agent_reasoning              → thread.message.delta (metadata)
exec_command_begin           → function_call (bash_exec)
exec_command_end             → function_call.completed
browser_screenshot_update    → attachment (image/png base64)
patch_apply_begin            → function_call (file_edit)
custom_tool_call_begin       → function_call (mcp_*)
auto_coordinator_decision    → metadata update
token_count                  → usage statistics
```

#### Component 2: Enhanced Open WebUI Frontend

**New Svelte Components:**

```
src/lib/components/code/
├── CodeChatPanel.svelte       # Main chat interface with Code context
├── ActivityCards.svelte       # Display tool/agent execution cards
│   ├── AutoDriveCard.svelte   # Auto Drive orchestration
│   ├── BrowserCard.svelte     # Browser session with screenshot
│   ├── TerminalCard.svelte    # Terminal output
│   └── AgentCard.svelte       # Agent execution status
├── SlashCommands.svelte       # Command palette for /plan, /solve, etc.
├── ThemeSelector.svelte       # Code theme picker
├── SettingsPanel.svelte       # Code-specific settings
│   ├── AgentSettings.svelte   # Multi-agent configuration
│   ├── BrowserSettings.svelte # CDP/browser settings
│   └── AutoDriveSettings.svelte # Auto Drive config
└── CodeMarkdown.svelte        # Enhanced markdown with syntax highlighting
```

**WebSocket Event Handler:**
```typescript
// src/lib/stores/codeEvents.ts
import { writable } from 'svelte/store';

export const codeEvents = writable({
  sessions: {},
  activeTools: [],
  browserScreenshots: {},
  terminalOutputs: {},
  autoDriveState: null
});

export function subscribeToCodeEvents(sessionId: string) {
  const eventSource = new EventSource(`/api/code/stream/${sessionId}`);

  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    handleCodeEvent(data);
  });
}
```

#### Component 3: Open WebUI Backend Extensions

**New API Routes (`backend/apps/code/`):**

```python
# backend/apps/code/main.py
from fastapi import APIRouter, WebSocket
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.post("/api/code/chat")
async def code_chat(request: CodeChatRequest):
    """Proxy to Code Pipeline"""
    return await pipeline_manager.route_to_code(request)

@router.get("/api/code/stream/{session_id}")
async def code_event_stream(session_id: str):
    """SSE endpoint for real-time Code events"""
    async def event_generator():
        async for event in code_pipeline.stream_events(session_id):
            yield {
                "event": event.type,
                "data": event.to_json()
            }

    return EventSourceResponse(event_generator())

@router.websocket("/api/code/terminal/{session_id}")
async def code_terminal_ws(websocket: WebSocket, session_id: str):
    """WebSocket for interactive terminal access"""
    await websocket.accept()
    # Bidirectional terminal I/O
```

---

## Feature Mapping: TUI → Web UI

### Phase 1: Core Features (Weeks 1-4)

| TUI Feature | Web UI Implementation | Status |
|-------------|----------------------|--------|
| Chat interface | Svelte chat panel with Code context | MVP |
| Slash commands `/plan`, `/solve`, `/code` | Command palette + autocomplete | MVP |
| Message streaming | SSE with delta updates | MVP |
| Reasoning display | Collapsible reasoning sections | MVP |
| Tool execution cards | Activity card components | MVP |
| File change display | Diff viewer component | MVP |
| Settings (basic) | Settings modal with form | MVP |

### Phase 2: Advanced Features (Weeks 5-8)

| TUI Feature | Web UI Implementation | Status |
|-------------|----------------------|--------|
| Auto Drive (`/auto`) | Dedicated Auto Drive panel | Phase 2 |
| Multi-agent orchestration | Agent status dashboard | Phase 2 |
| Browser integration (`/chrome`, `/browser`) | Browser preview panel with screenshots | Phase 2 |
| Terminal sessions | Web-based terminal emulator (xterm.js) | Phase 2 |
| Theme system | Theme picker with live preview | Phase 2 |
| Approval modals | Interactive approval dialogs | Phase 2 |
| Session persistence | Backend session store | Phase 2 |

### Phase 3: Advanced UX (Weeks 9-12)

| TUI Feature | Web UI Implementation | Status |
|-------------|----------------------|--------|
| Undo timeline | Visual timeline component | Phase 3 |
| Model selection | Dropdown with provider config | Phase 3 |
| Reasoning effort control | Slider with presets | Phase 3 |
| Cloud tasks | Task list integration | Phase 3 |
| MCP server config | Server management UI | Phase 3 |
| Validation settings | Tool validation toggles | Phase 3 |
| GitHub workflow watcher | PR status panel | Phase 3 |

---

## Implementation Roadmap

### Week 1-2: Foundation
- [ ] Set up Code Pipeline skeleton
- [ ] Implement subprocess management for `code app-server`
- [ ] Create basic JSON-RPC ↔ OpenAI translation layer
- [ ] Test basic chat functionality

### Week 3-4: Core Integration
- [ ] Implement event streaming (SSE)
- [ ] Add slash command routing (`/plan`, `/solve`, `/code`)
- [ ] Create basic Svelte components (chat, activity cards)
- [ ] Session state management
- [ ] File change/diff display

### Week 5-6: Multi-Agent & Auto Drive
- [ ] Auto Drive coordinator integration
- [ ] Agent execution tracking
- [ ] Decision/thinking stream display
- [ ] Approval flow implementation
- [ ] Agent configuration UI

### Week 7-8: Browser & Terminal
- [ ] Browser CDP integration
- [ ] Screenshot streaming and display
- [ ] Terminal emulator (xterm.js)
- [ ] Interactive terminal sessions
- [ ] Browser action timeline

### Week 9-10: Settings & Configuration
- [ ] Theme system port
- [ ] Advanced settings panels
- [ ] Model/provider selection
- [ ] Validation tool configuration
- [ ] MCP server management

### Week 11-12: Polish & Testing
- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Docker deployment setup

---

## Alternative Approaches Considered

### ❌ Approach 1: Full Codebase Merge
**Description:** Merge Code (Rust) into Open WebUI (Python/Svelte) as a native component.

**Pros:**
- Single codebase
- Tightest integration

**Cons:**
- Requires rewriting Code core in Python (massive effort)
- Breaks compatibility with Code updates
- Complex build process (Rust + Python)
- Difficult to maintain

**Verdict:** Not recommended due to extreme development cost and maintenance burden.

---

### ❌ Approach 2: REST API Bridge
**Description:** Create a standalone REST API server wrapping Code CLI.

**Pros:**
- Language-agnostic
- Can be used by other clients

**Cons:**
- Extra layer of abstraction
- Pipelines framework already provides this
- More deployment complexity
- Duplicates Pipeline functionality

**Verdict:** Not recommended - Pipelines framework is better suited.

---

### ❌ Approach 3: Direct Binary Integration
**Description:** Call `code` CLI directly from Open WebUI Python backend.

**Pros:**
- Simple initial implementation
- No middleware needed

**Cons:**
- No access to rich `app-server` protocol
- Limited to basic CLI mode
- Can't leverage bidirectional communication
- Misses out on event streaming

**Verdict:** Not recommended - insufficient feature access.

---

### ✅ Approach 4: TypeScript SDK + Node.js Middleware (Alternative)
**Description:** Use Code's TypeScript SDK in a Node.js service between Open WebUI and Code.

**Pros:**
- Leverages official SDK
- Type-safe event handling
- Good developer experience

**Cons:**
- Requires Node.js runtime (additional dependency)
- More complex deployment than pure Python
- Pipelines framework expects Python

**Verdict:** Viable alternative, but Python Pipeline is simpler for Open WebUI ecosystem.

---

## Technical Challenges & Solutions

### Challenge 1: Event Format Translation
**Problem:** Code emits rich JSON-RPC events; OpenAI uses simpler SSE format.

**Solution:**
- Create event adapter layer in Pipeline
- Buffer and coalesce rapid updates (30-50ms window)
- Use OpenAI's `function_call` format for tool execution
- Store rich metadata in message metadata fields

### Challenge 2: Browser Screenshot Streaming
**Problem:** Terminal images use ANSI/sixel; web needs standard formats.

**Solution:**
- Code already captures browser screenshots as PNG
- Base64 encode and embed in SSE events
- Use Open WebUI's attachment system
- Implement lazy loading for large images

### Challenge 3: Terminal Sessions
**Problem:** TUI has native PTY access; web needs emulation.

**Solution:**
- Use xterm.js for web-based terminal
- Proxy terminal I/O through WebSocket
- Code already provides terminal output in JSONL events
- Implement terminal session persistence

### Challenge 4: Session Persistence
**Problem:** Code stores sessions in `~/.code/sessions`; multi-user needs isolation.

**Solution:**
- Run Code with per-user working directories
- Map Open WebUI user ID → Code session directory
- Implement session cleanup policies
- Store metadata in Open WebUI database

### Challenge 5: Multi-Agent Orchestration Display
**Problem:** Auto Drive has complex state machine; needs rich UI.

**Solution:**
- Subscribe to `auto_coordinator_*` events
- Build state tracker in frontend
- Display as nested activity cards
- Real-time decision/thinking stream

---

## Deployment Architecture

### Docker Compose Setup

```yaml
version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - open-webui-data:/app/backend/data
      - ./pipelines:/app/backend/pipelines
    environment:
      - OPENAI_API_BASE_URLS=http://code-pipeline:9099
      - ENABLE_CODE_INTEGRATION=true
    depends_on:
      - code-pipeline

  code-pipeline:
    build:
      context: ./code-pipeline
      dockerfile: Dockerfile
    ports:
      - "9099:9099"
    volumes:
      - code-sessions:/home/pipeline/.code
      - /var/run/docker.sock:/var/run/docker.sock  # For sandboxing
    environment:
      - CODE_BINARY_PATH=/usr/local/bin/code
      - PIPELINES_PORT=9099
      - LOG_LEVEL=info

volumes:
  open-webui-data:
  code-sessions:
```

### Code Pipeline Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Code binary
RUN curl -fsSL https://just-every.github.io/code/install.sh | sh

# Install Pipeline dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy pipeline code
COPY code_pipeline.py .
COPY utils/ ./utils/

# Run Pipelines server
CMD ["python", "-m", "pipelines"]
```

---

## Success Metrics

### MVP Success Criteria (Week 4)
- [ ] Users can send messages and receive streamed responses
- [ ] `/plan`, `/solve`, `/code` commands work
- [ ] Tool execution visible as activity cards
- [ ] File changes displayed with diffs
- [ ] Session persistence across browser refreshes

### Phase 2 Success Criteria (Week 8)
- [ ] Auto Drive fully functional with approval flow
- [ ] Multi-agent orchestration visible
- [ ] Browser integration with screenshot display
- [ ] Terminal sessions work via web emulator
- [ ] Theme switching functional

### Phase 3 Success Criteria (Week 12)
- [ ] Feature parity with Code TUI for 90%+ use cases
- [ ] Performance: <100ms latency for event streaming
- [ ] Stability: 24hr continuous operation without crashes
- [ ] Documentation: Complete setup and usage guide
- [ ] Docker: One-command deployment

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Event format incompatibility | Medium | High | Extensive testing, adapter layer |
| Performance bottleneck in translation | Low | Medium | Event batching, async processing |
| State sync issues (browser ↔ backend) | Medium | Medium | WebSocket heartbeat, reconnection logic |
| Code CLI breaking changes | Low | High | Version pinning, compatibility layer |
| Complex UI features difficult to port | Medium | Medium | Iterate in phases, MVP first |
| Multi-user session isolation | Medium | High | Proper directory isolation, testing |

---

## Next Steps

### Immediate Actions (This Week)
1. **Validate assumptions** - Test Code `app-server` directly with sample JSON-RPC
2. **Prototype pipeline** - Build minimal Python wrapper around Code CLI
3. **Test event streaming** - Verify SSE compatibility with Open WebUI
4. **Design data models** - Define event translation schemas

### Week 2 Deliverables
1. Working Code Pipeline proof-of-concept
2. Basic chat working in Open WebUI
3. Simple activity card display
4. Architecture decision record (ADR) documented

### Month 1 Milestone
- MVP deployed and testable
- Core slash commands functional
- Demo video showing integration
- Initial documentation

---

## Conclusion

The **Code Pipe Pipeline approach** provides the optimal balance of:
- **Development speed** - Leverages existing infrastructure
- **Feature completeness** - All TUI features mappable to web UI
- **Maintainability** - Clean separation of concerns
- **Flexibility** - Easy to iterate and extend

This strategy enables rapid MVP delivery while maintaining a clear path to full feature parity. The phased approach reduces risk and allows for early user feedback.

**Recommendation: Proceed with Code Pipe Pipeline implementation.**

---

## Appendix A: Code Events Reference

### Core Events
- `session_configured` - Initial session setup
- `task_started` - New turn begins
- `task_completed` - Turn finished successfully
- `error` - Fatal error occurred

### Message Events
- `agent_message` - Final assistant response
- `agent_message_delta` - Streaming response chunk
- `agent_reasoning` - Extended thinking output
- `agent_reasoning_delta` - Streaming reasoning chunk

### Tool Events
- `exec_command_begin` - Shell command started
- `exec_command_chunk` - stdout/stderr output
- `exec_command_end` - Command completed
- `exec_approval_request` - Awaiting user approval

### File Events
- `patch_apply_begin` - File modification started
- `patch_apply_end` - File modification completed
- `apply_patch_approval_request` - File change approval needed

### Browser Events
- `browser_screenshot_update` - New screenshot available
- `browser_action` - Browser action performed (click, type, navigate)

### Agent Events
- `agent_run_begin` - External agent started
- `agent_run_end` - External agent completed
- `agent_status_update` - Agent progress update

### Auto Drive Events
- `auto_coordinator_decision` - Auto Drive decided next action
- `auto_coordinator_thinking` - Auto Drive reasoning
- `auto_coordinator_user_reply` - User provided input
- `auto_coordinator_countdown` - Approval timeout countdown

### Metadata Events
- `token_count` - Token usage statistics
- `review_output` - Code review feedback
- `background_event` - Informational message

---

## Appendix B: Slash Commands Reference

### Primary Commands
- `/plan <task>` - Multi-agent consensus planning
- `/solve <problem>` - Race multiple agents to solution
- `/code <feature>` - Implement feature with multi-agent review
- `/auto <task>` - Full Auto Drive automation

### Browser Commands
- `/chrome [port]` - Connect to external Chrome (CDP)
- `/browser [url]` - Use internal headless browser

### Configuration Commands
- `/settings` - Open settings panel
- `/model` - Switch model/provider
- `/themes` - Theme selection
- `/reasoning <low|medium|high>` - Set reasoning effort

### Session Commands
- `/new` - Start new conversation
- `/undo` - Show undo timeline
- `/resume <id>` - Resume previous session

### Utility Commands
- `/status` - Show current status
- `/limits` - Token/rate limit info
- `/cloud` - Cloud tasks integration
- `/github` - GitHub workflow watcher

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Author:** Integration Strategy Team
**Review Status:** Pending Approval
