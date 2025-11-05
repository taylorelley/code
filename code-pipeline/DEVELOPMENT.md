# Development Guide - Code Pipeline

## Getting Started

### Prerequisites

- Python 3.11+
- Code binary (from main project)
- Docker (for containerized development)
- Git

### Setup Development Environment

1. **Clone and setup:**
   ```bash
   cd code-pipeline
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dev dependencies
   ```

2. **Build Code binary:**
   ```bash
   cd ../code-rs
   cargo build --release --bin code
   cp target/release/code /usr/local/bin/code
   code --version
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Architecture Deep Dive

### Component Interaction Flow

```
User Message (Open WebUI)
    ↓
Pipeline.pipe()
    ↓
_get_or_create_session()
    ├─ CodeServerManager.start()
    │   └─ Spawns: code app-server
    ├─ CodeEventTranslator()
    └─ Returns session_data
    ↓
_handle_chat() or _handle_slash_command()
    ├─ manager.send_user_message()
    │   └─ JSON-RPC request → stdin
    │
    └─ async for event in manager.stream_events()
        ├─ Read from stdout (JSONL)
        ├─ translator.translate(event)
        │   └─ Code event → OpenAI SSE format
        └─ yield SSE string
            ↓
        Open WebUI renders response
```

### Event Translation Details

#### Code Events → OpenAI Events

| Code Event | OpenAI Event | Notes |
|------------|--------------|-------|
| `session_configured` | `thread.created` | Session initialization |
| `task_started` | `thread.run.created` | Turn begins |
| `agent_message_delta` | `thread.message.delta` | Streaming response |
| `agent_message` | `thread.message.completed` | Final response |
| `agent_reasoning` | `metadata` | Thinking/reasoning |
| `exec_command_begin` | `function_call` (bash) | Command execution |
| `patch_apply_begin` | `function_call` (file_edit) | File changes |
| `mcp_tool_call_begin` | `function_call` (mcp_*) | MCP tools |
| `token_count` | `usage` | Token statistics |
| `task_complete` | `done` | Turn complete |
| `error` | `error` | Error occurred |

#### SSE Format

```
id: 1699564800000
event: thread.message.delta
data: {"id":"msg_123","object":"thread.message.delta","delta":{"role":"assistant","content":[{"type":"text","text":{"value":"Hello"}}]}}

```

### Session Management

#### Session Lifecycle

1. **Creation** (`_get_or_create_session`):
   - Check if session exists and is alive
   - If not, create new CodeServerManager
   - Spawn `code app-server` subprocess
   - Initialize Code session
   - Create new conversation
   - Store in `self.sessions[session_id]`

2. **Usage**:
   - Reuse existing session for same user
   - Send messages to same conversation
   - Stream events back

3. **Cleanup** (`on_shutdown`):
   - Stop all CodeServerManager instances
   - Graceful shutdown of subprocesses
   - Clean up temp files

#### Session Isolation

Each user gets:
- Dedicated `CodeServerManager` instance
- Separate `code app-server` process
- Isolated working directory: `/data/code-workspace/user_{id}`
- Independent conversation history

### Error Handling

#### Subprocess Failures

```python
# In subprocess_manager.py
try:
    self.process = await asyncio.create_subprocess_exec(...)
except FileNotFoundError:
    raise RuntimeError("Code binary not found")
except Exception as e:
    raise RuntimeError(f"Failed to start: {e}")
```

#### Event Stream Errors

```python
# In code_pipeline.py
try:
    async for code_event in manager.stream_events():
        openai_events = translator.translate(code_event)
        for event in openai_events:
            yield event.to_sse_format()
except Exception as e:
    logger.error(f"Stream error: {e}")
    yield error_event(str(e))
```

#### Session Recovery

```python
# Check if session died
if not manager.is_running():
    logger.warning("Session died, recreating")
    del self.sessions[session_id]
    # Next request will create new session
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=pipelines --cov=utils --cov-report=html

# Run specific test
pytest tests/test_pipeline.py::TestPipeline::test_pipeline_initialization -v
```

### Integration Tests

Requires Code binary:

```bash
# Run integration tests
pytest tests/ -m integration -v

# Skip integration tests
pytest tests/ -m "not integration"
```

### Manual Testing

1. **Test pipeline standalone:**
   ```bash
   python pipelines/code_pipeline.py
   ```

2. **Test with mock requests:**
   ```python
   import asyncio
   from pipelines.code_pipeline import Pipeline

   async def test():
       pipeline = Pipeline()
       await pipeline.on_startup()

       body = {
           "messages": [{"role": "user", "content": "Hello!"}]
       }

       async for event in pipeline.pipe(body, __user__={"id": "test"}):
           print(event)

       await pipeline.on_shutdown()

   asyncio.run(test())
   ```

3. **Test event translation:**
   ```python
   from utils.event_translator import CodeEventTranslator

   translator = CodeEventTranslator()

   code_event = {
       "msg": {
           "type": "agent_message",
           "message": "Hello, world!"
       }
   }

   openai_events = translator.translate(code_event)
   for event in openai_events:
       print(event.to_dict())
   ```

## Debugging

### Enable Debug Logging

```python
# In code_pipeline.py
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
export LOG_LEVEL=debug
python pipelines/code_pipeline.py
```

### Debug Subprocess Communication

```python
# In subprocess_manager.py, add logging:
async def send_request(self, method, params, timeout=30.0):
    request = {...}
    logger.debug(f"Sending request: {json.dumps(request, indent=2)}")
    # ...
    response = await future
    logger.debug(f"Received response: {json.dumps(response, indent=2)}")
```

### Monitor Code app-server stderr

```python
# Already implemented in subprocess_manager.py
async def monitor_stderr(self):
    while True:
        line = await self.process.stderr.readline()
        logger.warning(f"Code stderr: {line.decode().strip()}")
```

### Inspect Event Stream

```python
# Add to _handle_chat in code_pipeline.py
async for code_event in manager.stream_events():
    logger.debug(f"Code event: {json.dumps(code_event, indent=2)}")
    # ...
```

## Performance Optimization

### Event Batching

Current implementation streams events immediately. For high-frequency events, consider batching:

```python
# In event_translator.py
class CodeEventTranslator:
    def __init__(self):
        self.event_buffer = []
        self.last_flush = time.time()

    async def get_batched_events(self):
        if len(self.event_buffer) >= 10 or time.time() - self.last_flush > 0.05:
            events = self.event_buffer
            self.event_buffer = []
            self.last_flush = time.time()
            return events
        return []
```

### Session Pooling

For high-traffic scenarios, pre-warm sessions:

```python
# In code_pipeline.py
class Pipeline:
    async def on_startup(self):
        # Pre-warm N sessions
        for i in range(self.valves.PREWARM_SESSIONS):
            await self._create_session(f"pool_{i}")
```

### Memory Management

Monitor session memory usage:

```python
# In subprocess_manager.py
def get_memory_usage(self):
    if not self.process:
        return 0

    try:
        proc = psutil.Process(self.process.pid)
        return proc.memory_info().rss / 1024 / 1024  # MB
    except:
        return 0
```

## Adding New Features

### Adding New Event Types

1. **Update event_translator.py:**
   ```python
   def translate(self, code_event):
       handler_map = {
           # ...existing handlers...
           "new_event_type": self._handle_new_event,
       }

   def _handle_new_event(self, msg):
       return [OpenAIEvent(...)]
   ```

2. **Add tests:**
   ```python
   def test_new_event_translation():
       translator = CodeEventTranslator()
       event = {"msg": {"type": "new_event_type", ...}}
       result = translator.translate(event)
       assert len(result) == 1
   ```

### Adding New Slash Commands

1. **Update _handle_slash_command:**
   ```python
   supported_commands = {
       # ...existing commands...
       "/newcmd": "Description of new command",
   }

   if cmd == "/newcmd":
       # Handle command
       return await self._handle_newcmd(args, ...)
   ```

2. **Implement handler:**
   ```python
   async def _handle_newcmd(self, args, manager, translator, ...):
       # Custom logic
       yield self._create_simple_response(f"Executed: {args}")
   ```

### Adding Configuration Options

1. **Update Valves:**
   ```python
   class Valves(BaseModel):
       NEW_OPTION: bool = Field(
           default=True,
           description="Description of new option"
       )
   ```

2. **Use in pipeline:**
   ```python
   if self.valves.NEW_OPTION:
       # Feature enabled
   ```

## Docker Development

### Build Image

```bash
docker build -t code-pipeline:dev .
```

### Run Standalone

```bash
docker run -it --rm \
    -e CODE_BINARY_PATH=/usr/local/bin/code \
    -e LOG_LEVEL=debug \
    -v $(pwd):/app \
    code-pipeline:dev
```

### Debug Container

```bash
docker run -it --rm \
    --entrypoint /bin/bash \
    code-pipeline:dev
```

### Multi-stage Build (Optimized)

```dockerfile
# Stage 1: Build Code binary
FROM rust:1.75 as code-builder
WORKDIR /build
COPY ../code-rs .
RUN cargo build --release

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=code-builder /build/target/release/code /usr/local/bin/
# ...rest of Dockerfile
```

## Deployment

### Production Checklist

- [ ] Set secure environment variables
- [ ] Configure proper sandbox mode
- [ ] Set approval policy
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure log aggregation
- [ ] Set resource limits
- [ ] Test failover scenarios

### Monitoring

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('pipeline_requests_total', 'Total requests')
request_duration = Histogram('pipeline_request_duration_seconds', 'Request duration')

@request_duration.time()
async def pipe(self, body, **kwargs):
    request_count.inc()
    # ...
```

### Scaling

**Horizontal Scaling:**
- Run multiple pipeline instances
- Use load balancer (nginx, haproxy)
- Share session store (Redis)

**Vertical Scaling:**
- Increase container resources
- Tune `MAX_CONCURRENT_SESSIONS`
- Optimize event batching

## Troubleshooting Development Issues

### Import Errors

```bash
# Ensure parent directory is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Code Binary Not Building

```bash
# Check Rust version
rustc --version  # Should be 1.70+

# Clean build
cd code-rs
cargo clean
cargo build --release
```

### Pipeline Not Loading in Open WebUI

1. Check pipeline location:
   ```bash
   ls ~/.open-webui/pipelines/code_pipeline.py
   ```

2. Check for syntax errors:
   ```bash
   python -m py_compile pipelines/code_pipeline.py
   ```

3. Check Open WebUI logs:
   ```bash
   docker logs open-webui
   ```

### Events Not Streaming

1. Verify Code app-server is running:
   ```python
   manager.is_running()  # Should return True
   ```

2. Check for stderr errors:
   ```python
   # Monitor stderr output
   asyncio.create_task(manager.monitor_stderr())
   ```

3. Test JSON-RPC directly:
   ```bash
   echo '{"jsonrpc":"2.0","id":"1","method":"ping","params":{}}' | code app-server
   ```

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

```python
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
    """
    # Implementation
```

### Git Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes and test:
   ```bash
   pytest tests/
   ```

3. Commit with descriptive message:
   ```bash
   git commit -m "feat: add support for X"
   ```

4. Push and create PR:
   ```bash
   git push origin feature/my-feature
   ```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

---

**Happy coding! 🚀**
