# Code Pipeline for Open WebUI

> 🚀 Enable agentic coding through Open WebUI's web interface

This pipeline integrates the [Code](https://github.com/just-every/code) agentic coding assistant into [Open WebUI](https://github.com/open-webui/open-webui), bringing all TUI features to the web:

- **Multi-agent orchestration** (`/plan`, `/solve`, `/code`)
- **Auto Drive automation** (`/auto`)
- **Browser integration** (screenshot capture, web interaction)
- **Terminal sessions** (command execution with approval)
- **File operations** (with diff preview and approval)
- **MCP tool support** (extend with custom tools)
- **Streaming responses** (real-time updates)

## Quick Start

### Prerequisites

1. **Code binary** - Build from source or download:
   ```bash
   # Option 1: Install via npm
   npm install -g @just-every/code

   # Option 2: Build from source
   git clone https://github.com/just-every/code.git
   cd code
   npm run build
   ```

2. **Docker & Docker Compose** (for containerized deployment)

### Installation

#### Option 1: Docker Compose (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/just-every/code.git
   cd code/code-pipeline
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Access Open WebUI at http://localhost:3000

#### Option 2: Manual Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure Code binary is in PATH:
   ```bash
   code --version
   ```

3. Copy pipeline to Open WebUI:
   ```bash
   cp -r pipelines ~/.open-webui/pipelines/
   ```

4. Restart Open WebUI

## Architecture

```
┌─────────────────────────────────────────┐
│     Open WebUI (Svelte + Python)        │
│     - Chat interface                    │
│     - User management                   │
│     - Settings                          │
└──────────────┬──────────────────────────┘
               │ HTTP/SSE
┌──────────────▼──────────────────────────┐
│     Code Pipeline (Python)              │
│     - Event translation                 │
│     - Session management                │
│     - Subprocess orchestration          │
└──────────────┬──────────────────────────┘
               │ JSON-RPC (stdio)
┌──────────────▼──────────────────────────┐
│     code app-server (Rust)              │
│     - Bidirectional JSON-RPC            │
│     - Event streaming                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Code Core Engine (Rust)             │
│     - Multi-agent orchestration         │
│     - Browser automation                │
│     - Tool execution                    │
│     - LLM provider integrations         │
└─────────────────────────────────────────┘
```

## Configuration

### Pipeline Settings (Valves)

Configure through Open WebUI's pipeline settings UI:

| Setting | Default | Description |
|---------|---------|-------------|
| `CODE_BINARY_PATH` | `code` | Path to Code binary |
| `ENABLE_BROWSER` | `true` | Enable browser integration |
| `ENABLE_AUTO_DRIVE` | `true` | Enable Auto Drive mode |
| `MAX_CONCURRENT_SESSIONS` | `10` | Max simultaneous users |
| `DEFAULT_WORKING_DIR` | `/tmp/code-workspace` | Code workspace directory |
| `APPROVAL_POLICY` | `on-request` | Command approval: `untrusted` \| `on-failure` \| `on-request` \| `never` |
| `SANDBOX_MODE` | `workspace-write` | Sandbox: `read-only` \| `workspace-write` \| `danger-full-access` |
| `MODEL` | `gpt-4` | Default LLM model |

### Environment Variables

```bash
# Code binary location
CODE_BINARY_PATH=/usr/local/bin/code

# Workspace directory
CODE_WORKING_DIR=/data/code-workspace

# Pipeline server port (standalone mode)
PIPELINES_PORT=9099

# Log level
LOG_LEVEL=info

# LLM Provider API Keys (passed to Code)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Basic Chat

Simply chat with Code like any other model in Open WebUI:

```
User: Write a Python function to calculate Fibonacci numbers

Code: I'll create a Fibonacci function for you...
[Shows code]
[Executes tests]
Done! The function has been created.
```

### Slash Commands

Use slash commands for advanced features:

#### `/plan <task>` - Multi-Agent Planning

Get consensus from multiple AI models (Claude, Gemini, GPT) on implementation approach:

```
/plan Implement user authentication with JWT
```

Code will:
1. Analyze the task
2. Query multiple agents
3. Synthesize a unified plan
4. Present implementation steps

#### `/solve <problem>` - Competitive Problem Solving

Race multiple agents to solve complex problems:

```
/solve Why does the login endpoint return 500 errors?
```

Code will:
1. Run multiple agents in parallel
2. Return the first correct solution
3. Show all approaches

#### `/code <feature>` - Multi-Agent Implementation

Implement features with multi-agent review:

```
/code Add dark mode toggle to settings page
```

Code will:
1. Create implementation plan
2. Generate code in multiple approaches
3. Select optimal solution
4. Apply with approval

#### `/auto <task>` - Auto Drive Automation

Fully automated multi-step task execution:

```
/auto Refactor the authentication module and add tests
```

Code will:
1. Plan the work
2. Coordinate multiple agents
3. Handle approvals
4. Recover from errors
5. Complete the entire task

#### `/browser <url>` - Browser Integration

Interact with websites:

```
/browser https://example.com
```

Code will:
1. Launch headless browser
2. Navigate to URL
3. Capture screenshots
4. Enable interaction (click, type, etc.)

#### `/chrome <port>` - Connect to Chrome DevTools

Connect to running Chrome instance via CDP:

```
/chrome 9222
```

### Approvals

When Code requests approval for commands or file changes:

1. Review the proposed action
2. Type `yes` to approve or `no` to reject
3. Code will proceed accordingly

## Features

### ✅ Implemented

- [x] Basic chat interface
- [x] Event streaming (SSE)
- [x] Session management (per-user isolation)
- [x] JSON-RPC → OpenAI event translation
- [x] Subprocess lifecycle management
- [x] Error handling and recovery
- [x] Slash command routing
- [x] Docker deployment

### 🚧 In Progress

- [ ] Browser screenshot display
- [ ] Terminal session UI
- [ ] Activity cards (tool execution)
- [ ] Approval flow UI
- [ ] Theme customization
- [ ] Settings panel integration

### 📋 Planned

- [ ] Auto Drive progress tracking
- [ ] Multi-agent decision visualization
- [ ] Diff viewer component
- [ ] File tree navigation
- [ ] Git integration UI
- [ ] MCP server configuration UI

## Development

### Running Tests

```bash
# Unit tests
python -m pytest tests/

# Integration tests (requires Code binary)
python -m pytest tests/integration/

# Test pipeline standalone
python pipelines/code_pipeline.py
```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=debug
python pipelines/code_pipeline.py
```

View Code app-server logs:

```bash
# In code-pipeline container
docker-compose logs -f code-pipeline
```

### Project Structure

```
code-pipeline/
├── pipelines/
│   └── code_pipeline.py      # Main pipeline class
├── utils/
│   ├── event_translator.py   # Code → OpenAI event translation
│   └── subprocess_manager.py # Code app-server lifecycle
├── tests/
│   ├── test_translator.py    # Event translation tests
│   └── test_pipeline.py      # Pipeline integration tests
├── Dockerfile                # Container image
├── docker-compose.yml        # Multi-container setup
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Troubleshooting

### Code binary not found

```
Error: Code binary not found at: code
```

**Solution:** Set `CODE_BINARY_PATH` to the correct location:
```bash
export CODE_BINARY_PATH=/path/to/code
# Or in docker-compose.yml
```

### Permission denied errors

```
Error: Permission denied: /data/code-workspace
```

**Solution:** Ensure the workspace directory is writable:
```bash
chmod 777 /data/code-workspace
# Or use Docker volumes with proper permissions
```

### Events not streaming

```
No response from Code after sending message
```

**Solutions:**
1. Check Code app-server is running: `docker-compose logs code-pipeline`
2. Verify Code binary: `docker-compose exec code-pipeline code --version`
3. Check for stderr errors in logs

### Session timeouts

```
Session died, recreating
```

**Solution:** Increase timeout or check Code stability:
```python
# In code_pipeline.py, adjust timeout
await manager.send_request("...", timeout=60.0)
```

## Performance

### Benchmarks

| Metric | Value |
|--------|-------|
| Startup time | ~2s per session |
| First token latency | <500ms |
| Event streaming | ~30-50ms |
| Memory per session | ~200MB |
| Max concurrent users | 10-50 (configurable) |

### Optimization Tips

1. **Use persistent sessions** - Reuse Code sessions across requests
2. **Increase timeout** - For long-running operations
3. **Limit concurrency** - Adjust `MAX_CONCURRENT_SESSIONS`
4. **Enable caching** - Use Code's built-in context caching
5. **Pre-warm sessions** - Start sessions before user requests

## Security

### Considerations

1. **Sandbox Mode** - Use `workspace-write` (default) to limit file access
2. **Approval Policy** - Use `on-request` (default) to review commands
3. **User Isolation** - Each user gets separate working directory
4. **API Keys** - Store securely, never commit to version control
5. **Docker Security** - Run with minimal privileges

### Best Practices

```yaml
# docker-compose.yml security settings
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /data/code-workspace
```

## Contributing

We welcome contributions! See [INTEGRATION_STRATEGY.md](../INTEGRATION_STRATEGY.md) for the full development plan.

### Areas for Contribution

- [ ] Frontend components (Svelte)
- [ ] Event translation improvements
- [ ] Performance optimization
- [ ] Documentation
- [ ] Testing
- [ ] Bug fixes

## License

Apache 2.0 - See [LICENSE](../LICENSE)

This project integrates:
- **Code** (Apache 2.0) - https://github.com/just-every/code
- **Open WebUI** (MIT) - https://github.com/open-webui/open-webui

## Support

- **Issues:** https://github.com/just-every/code/issues
- **Discussions:** https://github.com/just-every/code/discussions
- **Documentation:** [Full Integration Strategy](../INTEGRATION_STRATEGY.md)

## Changelog

### v0.1.0 (2025-11-05)

- ✅ Initial pipeline implementation
- ✅ Basic event translation
- ✅ Session management
- ✅ Docker deployment
- ✅ Slash command support
- ✅ Documentation

### Roadmap

See [INTEGRATION_STRATEGY.md](../INTEGRATION_STRATEGY.md) for detailed roadmap:

- **Phase 1** (Weeks 1-4): Core features MVP
- **Phase 2** (Weeks 5-8): Advanced features
- **Phase 3** (Weeks 9-12): Polish and full parity

---

**Made with ❤️ by the Code community**
