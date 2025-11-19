# Code Pipeline for Open WebUI

> 🚀 **Bring agentic AI coding to your web interface**

Transform [Open WebUI](https://github.com/open-webui/open-webui) into a powerful agentic coding environment by integrating the [Code](https://github.com/just-every/code) assistant. Get all the power of Code's TUI features through an intuitive web interface.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code](https://img.shields.io/badge/Code-Latest-green.svg)](https://github.com/just-every/code)

## ✨ Features

### 🤖 Agentic AI Capabilities
- **Multi-agent orchestration** - Plan, solve, and implement with `/plan`, `/solve`, `/code` commands
- **Auto Drive automation** - Fully automated multi-step task execution with `/auto`
- **Real-time streaming** - Watch your code being written in real-time
- **Session management** - Isolated workspaces per user

### 🔧 Development Tools
- **Browser integration** - Screenshot capture and web interaction
- **Terminal sessions** - Execute commands with approval workflows
- **File operations** - Edit files with diff preview and approval
- **MCP tool support** - Extend with Model Context Protocol tools

### 🏗️ Enterprise Ready
- **Docker deployment** - Containerized for easy scaling
- **Security controls** - Sandbox modes and approval policies
- **Resource limits** - Configurable session concurrency
- **Error recovery** - Robust subprocess management

---

## 📋 Table of Contents

- [Quick Start](#🚀-quick-start)
- [Installation](#📦-installation)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Manual Installation](#manual-installation)
  - [Development Setup](#development-setup)
- [Architecture](#🏗️-architecture)
- [Configuration](#⚙️-configuration)
- [Usage Guide](#📖-usage-guide)
- [Implementation Details](#🔬-implementation-details)
- [Troubleshooting](#🐛-troubleshooting)
- [Development](#🛠️-development)
- [Contributing](#🤝-contributing)

---

## 🚀 Quick Start

Get up and running with automatic configuration and automatic build from source:

```bash
# 1. Clone repository
git clone https://github.com/just-every/code.git
cd code/code-pipeline

# 2. Set up environment (auto-generates .env with defaults)
./scripts/setup-env.sh

# 3. Add your API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
# OR
echo "OPENAI_API_KEY=sk-..." >> .env

# 4. Build and start services (automatically builds Code from source!)
docker-compose build --no-cache code-pipeline  # First build: 5-10 minutes
docker-compose up -d

# 5. Access Open WebUI
open http://localhost:3000
```

That's it! The build process:
- ✅ **Automatically clones** the Code repository
- ✅ **Automatically builds** Code from source (Node.js + Rust)
- ✅ **Automatically configures** Open WebUI with code-pipeline
- ✅ **Ready to use** - Just sign up and start chatting!

---

## 📦 Installation

### Prerequisites

Before installing, ensure you have:

1. **Docker & Docker Compose** (v3.8+)
   ```bash
   docker --version  # Should be 20.10+
   docker-compose --version  # Should be 1.29+
   ```

2. **LLM API Key** - At least one of:
   - OpenAI API key (`OPENAI_API_KEY`)
   - Anthropic API key (`ANTHROPIC_API_KEY`)
   - Google AI API key (`GOOGLE_API_KEY`)

3. **Code Binary** (built during Docker setup, or install manually):
   ```bash
   # Option A: Install via npm
   npm install -g @just-every/code

   # Option B: Build from source
   git clone https://github.com/just-every/code.git
   cd code
   npm install
   npm run build
   ```

### Docker Compose (Recommended)

The easiest way to deploy is using Docker Compose:

#### Step 1: Clone Repository

```bash
git clone https://github.com/just-every/code.git
cd code/code-pipeline
```

#### Step 2: Configure Environment

Create your configuration file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required: At least one LLM API key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Customize paths
CODE_BINARY_PATH=/usr/local/bin/code
CODE_WORKING_DIR=/data/code-workspace

# Optional: Server settings
PIPELINES_PORT=9099
LOG_LEVEL=info

# Optional: Security settings
SANDBOX_MODE=workspace-write
APPROVAL_POLICY=on-request
```

#### Step 3: Start Services

```bash
# Start in background (with auto-configuration)
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

The services will automatically:
- ✅ Wait for code-pipeline to be healthy before starting Open WebUI
- ✅ Configure Open WebUI to use the code-pipeline
- ✅ Enable signup for easy onboarding
- ✅ Set up health checks for reliability

#### Step 4: Access Open WebUI

1. Open browser to http://localhost:3000
2. Create an account (first user becomes admin)
3. The code-pipeline model is already configured - just select it and start chatting!

#### Step 5: Verify Installation

Test that Code is working:

```bash
# Check Code binary
docker-compose exec code-pipeline code --version

# Check pipeline logs
docker-compose logs code-pipeline | tail -20

# Test health endpoint
curl http://localhost:9099/health
```

### Manual Installation

For development or custom deployments:

#### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify Python version (3.11+ required)
python --version
```

#### Step 2: Install Code Binary

```bash
# Install Code globally
npm install -g @just-every/code

# Verify installation
code --version
```

#### Step 3: Configure Environment

```bash
# Set environment variables
export CODE_BINARY_PATH=$(which code)
export CODE_WORKING_DIR=$HOME/.code-workspace
export OPENAI_API_KEY=sk-...

# Create workspace directory
mkdir -p $CODE_WORKING_DIR
```

#### Step 4: Install Pipeline in Open WebUI

```bash
# Copy pipeline to Open WebUI
mkdir -p ~/.open-webui/pipelines
cp -r pipelines ~/.open-webui/pipelines/code_pipeline
cp -r utils ~/.open-webui/pipelines/code_pipeline/

# Or symlink for development
ln -s $(pwd)/pipelines ~/.open-webui/pipelines/code_pipeline
```

#### Step 5: Start Open WebUI

```bash
# If using standalone Open WebUI installation
cd /path/to/open-webui
docker-compose up -d

# Or start Open WebUI with environment
OPENAI_API_BASE_URLS=http://localhost:9099/v1 \
OPENAI_API_KEYS=dummy \
docker run -d -p 3000:8080 \
  -v ~/.open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

### Development Setup

For active development on the pipeline:

```bash
# 1. Clone with submodules
git clone --recurse-submodules https://github.com/just-every/code.git
cd code/code-pipeline

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install dev dependencies
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests
python -m pytest tests/ -v

# 6. Start development server
python pipelines/code_pipeline.py
```

---

## ⚡ Automatic Configuration

Open WebUI is automatically configured and ready to use after running `docker compose up -d`. Here's what happens automatically:

### 🔄 Auto-Configuration Features

1. **Health Checks**
   - Code-pipeline has a health endpoint at `/health`
   - Open WebUI waits for code-pipeline to be healthy before starting
   - Ensures proper startup order and reliability

2. **Pre-configured Environment**
   - Code-pipeline endpoint: `http://code-pipeline:9099/v1`
   - OpenAI-compatible API format
   - Dummy API key (no auth required between containers)

3. **Service Dependencies**
   - Docker Compose ensures code-pipeline starts first
   - Open WebUI won't start until code-pipeline is healthy
   - Automatic retry on service failures

4. **Default Settings**
   - Signup enabled for easy onboarding
   - WebUI name set to "Code WebUI"
   - Pipeline automatically available in model dropdown

### 🛠️ Setup Script

Use the provided setup script to auto-generate your .env file:

```bash
# Run the setup script
./scripts/setup-env.sh

# This creates .env with sensible defaults:
# - CODE_BINARY_PATH=/usr/local/bin/code
# - CODE_WORKING_DIR=/data/code-workspace
# - PIPELINES_PORT=9099
# - LOG_LEVEL=info
# - SANDBOX_MODE=workspace-write
# - APPROVAL_POLICY=on-request
```

Then just add your API key:

```bash
# For Anthropic (recommended)
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env

# For OpenAI
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# For Google AI
echo "GOOGLE_API_KEY=your-key-here" >> .env
```

### 🚀 Zero-Configuration Startup

After setting your API key, simply run:

```bash
docker-compose up -d
```

And you're done! Open WebUI is ready at http://localhost:3000 with:
- ✅ Code-pipeline automatically configured
- ✅ Model selection ready
- ✅ All features enabled (browser, auto drive, MCP tools)
- ✅ Secure defaults (workspace sandbox, approval workflows)

### 🔍 Verification

Check that everything is configured correctly:

```bash
# Check service health
curl http://localhost:9099/health
# Should return: {"status":"healthy","service":"code-pipeline","version":"1.0.0"}

# Check Open WebUI health
curl http://localhost:3000/health
# Should return healthy status

# View service logs
docker-compose logs code-pipeline
docker-compose logs open-webui

# Check service status
docker-compose ps
# Both services should show "Up (healthy)"
```

---

## 🏗️ Architecture

Understanding the architecture helps with troubleshooting and customization.

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI (Port 3000)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ Svelte UI   │  │  FastAPI    │  │  Pipeline Router │   │
│  │  - Chat     │←→│  - Auth     │←→│  - Load plugins  │   │
│  │  - Settings │  │  - Models   │  │  - Route msgs    │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/SSE (OpenAI API format)
┌───────────────────────────▼─────────────────────────────────┐
│              Code Pipeline (Python - Port 9099)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Pipeline Class (pipelines/code_pipeline.py)          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │   Session    │  │    Event     │  │  Request    │ │ │
│  │  │  Management  │  │  Translator  │  │   Handler   │ │ │
│  │  │  - Per-user  │  │  JSON-RPC →  │  │  - Chat     │ │ │
│  │  │  - Isolation │  │  OpenAI SSE  │  │  - Slash    │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CodeServerManager (utils/subprocess_manager.py)      │ │
│  │  - Spawn/manage code app-server subprocess            │ │
│  │  - JSON-RPC over stdio                                │ │
│  │  - Request/response matching                          │ │
│  │  - Event queue distribution (prevents race condition) │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ JSON-RPC (stdio)
┌───────────────────────────▼─────────────────────────────────┐
│            code app-server (Rust subprocess)                │
│  - Bidirectional JSON-RPC protocol                         │
│  - Event streaming (notifications)                         │
│  - Session state management                                │
│  - Tool execution coordination                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Code Core Engine (Rust)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Multi-Agent  │  │   Browser    │  │   LLM Provider   │  │
│  │ Orchestrator │  │  Automation  │  │   Integration    │  │
│  │  - /plan     │  │  - Playwright│  │  - OpenAI        │  │
│  │  - /solve    │  │  - CDP       │  │  - Anthropic     │  │
│  │  - /code     │  │  - Screenshot│  │  - Google        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Tool       │  │     File     │  │    Terminal      │  │
│  │  Execution   │  │  Operations  │  │   Execution      │  │
│  │  - MCP       │  │  - Read/Edit │  │  - Command run   │  │
│  │  - Functions │  │  - Approval  │  │  - Output stream │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

#### 1. User Message Flow

```
User types message in Open WebUI
  ↓
Open WebUI → POST /v1/chat/completions (OpenAI format)
  ↓
Code Pipeline receives request
  ↓
Pipeline.pipe() extracts message
  ↓
Get or create user session (session_id = "session_{user_id}")
  ↓
Send to CodeServerManager.send_user_message()
  ↓
Write JSON-RPC request to code app-server stdin
  {
    "jsonrpc": "2.0",
    "id": "123",
    "method": "sendUserMessage",
    "params": { "conversationId": "...", "params": { ... } }
  }
  ↓
code app-server processes message
  ↓
code app-server streams events to stdout (JSON lines)
  ↓
Background event reader reads stdout → pushes to event_queue
  ↓
_handle_chat reads from event_queue
  ↓
EventTranslator converts Code events → OpenAI SSE format
  ↓
Yield SSE events back to Open WebUI
  ↓
Open WebUI displays streaming response
```

#### 2. Event Queue Architecture (Race Condition Fix)

**Problem:** Multiple consumers of `stream_events()` caused race conditions.

**Solution:** Single reader with queue distribution:

```
┌─────────────────────────────────────────────────────┐
│       code app-server stdout (JSON lines)          │
└──────────────────┬──────────────────────────────────┘
                   │ Single reader (no race!)
┌──────────────────▼──────────────────────────────────┐
│    Background Event Reader (_background_event_reader)│
│    - ONLY task reading from stdout                  │
│    - Resolves JSON-RPC response futures             │
│    - Pushes notification events to queue            │
└──────────────────┬──────────────────────────────────┘
                   │ asyncio.Queue
        ┌──────────┴──────────┬──────────────────┐
        ▼                     ▼                  ▼
  ┌──────────┐         ┌──────────┐      ┌──────────┐
  │_handle   │         │_handle   │      │ Future   │
  │_chat     │         │_slash_   │      │ handlers │
  │          │         │command   │      │          │
  └──────────┘         └──────────┘      └──────────┘
   Multiple consumers read from queue (no race!)
```

### Key Components

#### Pipeline Class (`pipelines/code_pipeline.py`)

The main entry point implementing Open WebUI's Pipe protocol:

- **`pipe()`** - Main request handler (OpenAI API compatible)
- **`_get_or_create_session()`** - Session management with per-user isolation
- **`_handle_chat()`** - Regular chat message handling
- **`_handle_slash_command()`** - Slash command routing
- **`_background_event_reader()`** - Critical event distribution task

#### CodeServerManager (`utils/subprocess_manager.py`)

Manages the code app-server subprocess lifecycle:

- **`start()`/`stop()`** - Process lifecycle management
- **`send_request()`** - JSON-RPC request with response awaiting
- **`send_notification()`** - One-way JSON-RPC notification
- **`stream_events()`** - Async generator for stdout events
- **`initialize_session()`** - Initialize Code session
- **`new_conversation()`** - Create conversation context
- **`send_user_message()`** - Send user message to Code

#### EventTranslator (`utils/event_translator.py`)

Translates between Code's rich event protocol and OpenAI's SSE format:

- **`translate()`** - Main translation dispatcher
- **`reset_buffers()`** - Memory leak prevention
- Event handlers for: session, task, message, tool execution, errors
- Buffer size limits to prevent unbounded memory growth

---

## ⚙️ Configuration

### Pipeline Settings (Valves)

Configure through Open WebUI's admin panel (`Settings > Admin > Pipelines`):

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `CODE_BINARY_PATH` | string | `code` | Path to Code binary executable |
| `ENABLE_BROWSER` | boolean | `true` | Enable browser integration features |
| `ENABLE_AUTO_DRIVE` | boolean | `true` | Enable Auto Drive multi-agent mode |
| `MAX_CONCURRENT_SESSIONS` | integer | `10` | Maximum concurrent user sessions |
| `DEFAULT_WORKING_DIR` | string | `/tmp/code-workspace` | Base workspace directory |
| `APPROVAL_POLICY` | enum | `on-request` | Command approval policy |
| `SANDBOX_MODE` | enum | `workspace-write` | File system access mode |
| `MODEL` | string | `gpt-4` | Default LLM model |

#### Approval Policy Options

- **`untrusted`** - Approve all untrusted commands
- **`on-failure`** - Approve commands that previously failed
- **`on-request`** - Always request approval (recommended)
- **`never`** - Never request approval (dangerous)

#### Sandbox Mode Options

- **`read-only`** - No file writes allowed (safest)
- **`workspace-write`** - Can write within workspace only (recommended)
- **`danger-full-access`** - Full filesystem access (dangerous)

### Environment Variables

Set in `.env` file or Docker environment:

```bash
# Code Binary
CODE_BINARY_PATH=/usr/local/bin/code

# Workspace (user directories created within)
CODE_WORKING_DIR=/data/code-workspace

# Pipeline Server
PIPELINES_PORT=9099
LOG_LEVEL=info  # debug, info, warning, error

# LLM Provider API Keys (passed to Code)
# At least one required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Open WebUI
WEBUI_NAME=Code WebUI
ENABLE_SIGNUP=true

# Security
SANDBOX_MODE=workspace-write
APPROVAL_POLICY=on-request

# Performance
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT=3600  # seconds
```

### Docker Compose Configuration

Customize `docker-compose.yml` for your deployment:

```yaml
services:
  code-pipeline:
    environment:
      # Increase memory limit
      - DOCKER_MEMORY_LIMIT=4g

      # Custom Code binary location
      - CODE_BINARY_PATH=/usr/local/bin/code

      # Enable debug logging
      - LOG_LEVEL=debug

      # Set API keys from host environment
      - OPENAI_API_KEY=${OPENAI_API_KEY}

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

    # Security
    security_opt:
      - no-new-privileges:true

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9099/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 📖 Usage Guide

### Basic Chat

Simply chat with Code like any LLM:

```
You: Write a Python function to calculate Fibonacci numbers

Code: I'll create a Fibonacci function for you with tests.
[Shows code being written]
[Runs tests]
✅ Done! Created fibonacci.py with tests passing.
```

### Slash Commands

Unlock advanced multi-agent features with slash commands:

#### `/plan <task>` - Multi-Agent Planning

Get consensus from multiple AI models on the best approach:

```
You: /plan Implement user authentication with JWT tokens

Code: I'll consult multiple agents for the best approach...

Agent 1 (Claude): Recommends using FastAPI with JWT middleware
Agent 2 (GPT-4): Suggests adding refresh token rotation
Agent 3 (Gemini): Proposes integration with OAuth providers

Synthesized Plan:
1. Install PyJWT and passlib dependencies
2. Create authentication middleware
3. Implement token generation and validation
4. Add refresh token rotation for security
5. Include OAuth integration for flexibility
6. Write comprehensive tests

Shall I proceed with implementation?
```

#### `/solve <problem>` - Competitive Problem Solving

Race multiple agents to solve a problem first:

```
You: /solve Why is my API returning 500 errors only on POST requests?

Code: Starting parallel investigation with 3 agents...

Agent 1: Checking request payload validation...
Agent 2: Analyzing middleware stack...
Agent 3: ✅ Found it! Missing CSRF token in POST handler

Solution: Your POST endpoint is missing CSRF exemption.
Add @csrf_exempt decorator or include CSRF token in requests.

[Shows fix and applies it]
```

#### `/code <feature>` - Multi-Agent Implementation

Generate and review code with multiple agents:

```
You: /code Add dark mode toggle to the settings page

Code: I'll implement this with multi-agent review...

Implementation Agent: Creating dark mode component...
Review Agent: Checking accessibility standards...
Test Agent: Writing E2E tests...

✅ Implementation complete:
- Added DarkModeToggle component
- Integrated with theme context
- Passes WCAG accessibility tests
- E2E tests passing

Ready to apply? Type 'yes' to continue.
```

#### `/auto <task>` - Full Auto Drive

Let Code handle everything autonomously:

```
You: /auto Refactor the authentication module, add proper error handling, and write unit tests

Code: Starting Auto Drive coordinator...

Step 1/5: Analyzing current authentication code...
Step 2/5: Planning refactoring strategy...
Step 3/5: Refactoring authentication module...
Step 4/5: Adding error handling and logging...
Step 5/5: Writing comprehensive test suite...

✅ Auto Drive complete!
- Refactored 3 files
- Added 15 tests (100% coverage)
- All tests passing
- No breaking changes detected
```

#### `/browser <url>` - Browser Integration

Interact with websites programmatically:

```
You: /browser https://github.com/trending

Code: Launching browser...
📸 Screenshot captured
Current page: GitHub Trending Repositories

I can see the trending projects. What would you like to know?
```

### Approval Workflows

When Code requests approval (with `APPROVAL_POLICY=on-request`):

```
Code: I need to run this command:
  $ npm install express

This will:
- Install express package
- Modify package.json
- Update package-lock.json

Approve? (yes/no)

You: yes

Code: ✅ Approved. Installing express...
```

### File Operations

Code can read and modify files with approval:

```
You: Update the API endpoint to handle pagination

Code: I need to modify src/api/users.js:

Diff:
  @@ -10,6 +10,10 @@
   app.get('/api/users', async (req, res) => {
  +  const page = parseInt(req.query.page) || 1;
  +  const limit = parseInt(req.query.limit) || 10;
  +  const offset = (page - 1) * limit;
  +
  -  const users = await User.findAll();
  +  const users = await User.findAll({ limit, offset });
     res.json(users);
   });

Apply these changes? (yes/no)

You: yes

Code: ✅ Changes applied successfully.
```

### Advanced Examples

#### Example 1: Full Stack Feature

```
You: /auto Create a blog post feature with:
- Backend API (FastAPI)
- Database models (SQLAlchemy)
- Frontend components (React)
- Full test coverage

Code: [Auto Drive coordinates all steps autonomously]
✅ Complete! Created 12 files, 2000+ lines of code, 95% test coverage.
```

#### Example 2: Bug Investigation

```
You: /solve My React app crashes when users click the logout button

Code:
Agent 1: Checking event handlers...
Agent 2: ✅ Found! State update after unmount in useEffect
Agent 3: Confirming async cleanup issue...

Fix applied:
- Added cleanup function to useEffect
- Added mounted ref to prevent state updates
- Added error boundary
```

#### Example 3: Code Review

```
You: Review my authentication implementation for security issues

Code: Analyzing code for security vulnerabilities...

⚠️ Found 3 issues:
1. Password stored in plaintext (CRITICAL)
2. No rate limiting on login endpoint (HIGH)
3. JWT secret hardcoded (HIGH)

Shall I fix these? Type 'yes' to proceed.
```

---

## 🔬 Implementation Details

### Session Management

Each user gets an isolated session:

```python
# Session structure
sessions[session_id] = {
    "manager": CodeServerManager,      # Subprocess manager
    "translator": CodeEventTranslator, # Event translator
    "conversation_id": str,            # Code conversation ID
    "user_id": str,                    # User identifier
    "working_dir": str,                # Isolated workspace
    "event_queue": asyncio.Queue,      # Event distribution
    "event_reader_task": Task          # Background reader
}
```

**Isolation guarantees:**
- Separate working directories: `/data/code-workspace/user_{user_id}/`
- Independent code app-server processes
- No cross-contamination between users

### Event Translation

Code events are translated to OpenAI SSE format:

```python
# Code event (JSON-RPC notification)
{
  "jsonrpc": "2.0",
  "method": "notification",
  "params": {
    "msg": {
      "type": "agent_message_delta",
      "delta": "Hello "
    }
  }
}

# Translated to OpenAI SSE
event: thread.message.delta
data: {
  "id": "msg_abc123",
  "object": "thread.message.delta",
  "delta": {
    "role": "assistant",
    "content": [{"type": "text", "text": {"value": "Hello "}}]
  }
}
```

**Event mapping:**
- `session_configured` → `thread.created`
- `task_started` → `thread.run.created`
- `agent_message_delta` → `thread.message.delta`
- `task_complete` → `thread.run.completed` + `done`
- `exec_command_begin` → Function call (bash)
- `patch_apply_begin` → Function call (file_edit)

### Memory Management

To prevent memory leaks in long-lived sessions:

1. **Buffer limits** - Max 10K items, 1M characters
2. **Task-based clearing** - Buffers reset at task start/end
3. **Session cleanup** - Full cleanup on session destruction

```python
# Buffer enforcement
if len(self.message_buffer) < MAX_BUFFER_SIZE:
    total_chars = sum(len(s) for s in self.message_buffer)
    if total_chars + len(delta) < MAX_BUFFER_CHARS:
        self.message_buffer.append(delta)
```

### Error Recovery

The pipeline handles various failure modes:

- **Process crash** - Automatic session recreation
- **JSON parse errors** - Logged but don't crash pipeline
- **Timeout** - Configurable per request
- **Graceful shutdown** - All sessions cleaned up properly

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Code binary not found

**Error:**
```
RuntimeError: Code binary not found at: code
```

**Solutions:**
```bash
# Check if Code is installed
which code

# Install Code
npm install -g @just-every/code

# Or set explicit path in .env
CODE_BINARY_PATH=/usr/local/bin/code

# In Docker, rebuild image
docker-compose build --no-cache code-pipeline
```

#### 2. Permission denied on workspace

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/data/code-workspace'
```

**Solutions:**
```bash
# Create directory with correct permissions
sudo mkdir -p /data/code-workspace
sudo chown -R $(whoami) /data/code-workspace
chmod 755 /data/code-workspace

# Or use Docker volume (recommended)
# Already configured in docker-compose.yml
```

#### 3. Events not streaming

**Error:**
```
No response from Code after sending message
```

**Solutions:**
```bash
# Check if code-pipeline container is running
docker-compose ps

# Check logs for errors
docker-compose logs code-pipeline | tail -50

# Verify Code binary works
docker-compose exec code-pipeline code --version

# Check for stderr output
docker-compose logs code-pipeline | grep -i error

# Restart pipeline
docker-compose restart code-pipeline
```

#### 4. API key errors

**Error:**
```
Error: No LLM provider API key found
```

**Solutions:**
```bash
# Check environment variables
docker-compose exec code-pipeline env | grep API_KEY

# Set in .env file
echo "OPENAI_API_KEY=sk-..." >> .env
docker-compose up -d --force-recreate

# Or pass via command line
OPENAI_API_KEY=sk-... docker-compose up -d
```

#### 5. Session timeouts

**Error:**
```
Session died, recreating
asyncio.TimeoutError: Request timed out
```

**Solutions:**
```python
# Increase timeout in code_pipeline.py
await manager.send_request("...", timeout=120.0)  # 2 minutes

# Or configure in environment
SESSION_TIMEOUT=120
REQUEST_TIMEOUT=60
```

#### 6. Memory issues

**Error:**
```
MemoryError: Cannot allocate memory
```

**Solutions:**
```bash
# Check memory usage
docker stats code-pipeline

# Increase Docker memory limit
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Reduce concurrent sessions
MAX_CONCURRENT_SESSIONS=5

# Enable memory monitoring
LOG_LEVEL=debug
```

#### 7. Race condition / lost events

**Error:**
```
Events arriving out of order
Missing agent responses
```

**Solution:**
This was fixed in v0.2.0 (commit 72a9e3f). Update to latest version:

```bash
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

### Debugging Tips

#### Enable Debug Logging

```bash
# Set in .env
LOG_LEVEL=debug

# Or environment variable
docker-compose stop
LOG_LEVEL=debug docker-compose up

# View debug logs
docker-compose logs -f code-pipeline | grep DEBUG
```

#### Test Pipeline Standalone

```bash
# Run pipeline directly (without Open WebUI)
cd code-pipeline
python pipelines/code_pipeline.py
```

#### Check JSON-RPC Communication

```bash
# Monitor stdin/stdout
docker-compose exec code-pipeline strace -e read,write -p $(pgrep code)

# Or use custom logging
# Edit subprocess_manager.py to log all JSON-RPC messages
```

#### Verify Network Connectivity

```bash
# Test pipeline endpoint
curl http://localhost:9099/health

# Test from Open WebUI container
docker-compose exec open-webui curl http://code-pipeline:9099/health

# Check docker network
docker network inspect code-pipeline_webui-network
```

### Getting Help

If you're still stuck:

1. **Check the logs** - Most issues show up in logs
   ```bash
   docker-compose logs code-pipeline --tail=100
   ```

2. **Search existing issues** - Someone may have hit this before
   https://github.com/just-every/code/issues

3. **Open an issue** - Provide:
   - Error message and full stack trace
   - Docker logs: `docker-compose logs`
   - Environment: `docker-compose config`
   - Steps to reproduce

4. **Join discussions** - Ask the community
   https://github.com/just-every/code/discussions

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_pipeline.py -v

# Run with coverage
python -m pytest tests/ --cov=pipelines --cov=utils --cov-report=html

# Run integration tests (requires Code binary)
python -m pytest tests/integration/ -v --integration
```

### Project Structure

```
code-pipeline/
├── pipelines/
│   └── code_pipeline.py          # Main Pipeline class
├── backend/
│   ├── enhanced_pipeline.py       # WebSocket-enhanced pipeline
│   ├── websocket_handler.py       # WebSocket event management
│   ├── file_tree_service.py       # File tree operations
│   └── settings_manager.py        # Pipeline settings management
├── utils/
│   ├── event_translator.py        # JSON-RPC ↔ OpenAI translation
│   └── subprocess_manager.py      # code app-server lifecycle
├── tests/
│   ├── test_pipeline.py           # Pipeline tests
│   ├── test_translator.py         # Translation tests
│   ├── test_subprocess.py         # Subprocess manager tests
│   └── e2e/
│       └── code-pipeline.spec.ts  # End-to-end tests
├── frontend/                       # (Phase 2-3) Web components
├── docker-compose.yml             # Multi-container setup
├── Dockerfile                     # Pipeline container image
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Dev dependencies
├── .env.example                   # Example configuration
├── FIXES_SUMMARY.md              # Recent bug fixes
└── README.md                      # This file
```

### Code Architecture

```
Pipeline Flow:
  pipe() → _get_or_create_session() → _handle_chat()
                                    ↓
                          _background_event_reader()
                                    ↓
                            EventTranslator.translate()
                                    ↓
                              Yield SSE events

Session Lifecycle:
  Create session → Start CodeServerManager
      ↓
  Start background event reader (critical!)
      ↓
  Initialize Code session (JSON-RPC)
      ↓
  Create conversation
      ↓
  Ready for messages
```

### Adding New Event Types

1. Add handler to `EventTranslator`:
```python
def _handle_new_event(self, msg: Dict[str, Any]) -> List[OpenAIEvent]:
    """Handle new_event_type"""
    return [
        OpenAIEvent(
            EventType.THREAD_MESSAGE_DELTA,
            {"id": "...", "delta": {...}}
        )
    ]
```

2. Register in event map:
```python
handler_map = {
    # ...
    "new_event_type": self._handle_new_event,
}
```

3. Add test:
```python
def test_new_event_translation():
    translator = CodeEventTranslator()
    code_event = {"msg": {"type": "new_event_type", ...}}
    events = translator.translate(code_event)
    assert len(events) == 1
    assert events[0].event_type == "thread.message.delta"
```

### Performance Profiling

```bash
# Profile pipeline
python -m cProfile -o profile.stats pipelines/code_pipeline.py

# View results
python -m pstats profile.stats
> sort cumtime
> stats 20

# Memory profiling
pip install memory_profiler
python -m memory_profiler pipelines/code_pipeline.py

# Async profiling
pip install pyinstrument
pyinstrument pipelines/code_pipeline.py
```

### Building Docker Images

```bash
# Build pipeline image
docker build -t code-pipeline:latest .

# Build with specific Code version
docker build --build-arg CODE_VERSION=0.1.0 -t code-pipeline:latest .

# Build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t code-pipeline:latest .

# Push to registry
docker tag code-pipeline:latest your-registry/code-pipeline:latest
docker push your-registry/code-pipeline:latest
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Areas for Contribution

#### High Priority
- [ ] Frontend components (Svelte) for browser screenshots
- [ ] Terminal UI component with ANSI support
- [ ] Approval flow UI with diff viewer
- [ ] Settings panel integration
- [ ] E2E test coverage

#### Medium Priority
- [ ] Auto Drive progress visualization
- [ ] Multi-agent decision comparison UI
- [ ] File tree navigation component
- [ ] Performance optimizations
- [ ] Documentation improvements

#### Low Priority
- [ ] MCP server configuration UI
- [ ] Git integration UI
- [ ] Theme customization
- [ ] Metrics and monitoring

### Development Workflow

1. **Fork and clone**
   ```bash
   git clone https://github.com/your-username/code.git
   cd code/code-pipeline
   ```

2. **Create branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   ```bash
   # Edit files
   # Run tests
   python -m pytest tests/ -v
   ```

4. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add browser screenshot display"
   # or
   git commit -m "fix: resolve race condition in event streaming"
   # or
   git commit -m "docs: update installation instructions"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Open PR on GitHub
   ```

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Formatting, missing semicolons, etc.
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `perf:` - Performance improvement
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Testing Requirements

All PRs must include:
- Unit tests for new functionality
- Integration tests if applicable
- Updated documentation
- Passing CI checks

---

## 📄 License

Apache 2.0 - See [LICENSE](../LICENSE)

This project integrates:
- **Code** (Apache 2.0) - https://github.com/just-every/code
- **Open WebUI** (MIT) - https://github.com/open-webui/open-webui

---

## 📞 Support

- **Issues:** https://github.com/just-every/code/issues
- **Discussions:** https://github.com/just-every/code/discussions
- **Documentation:** [INTEGRATION_STRATEGY.md](../INTEGRATION_STRATEGY.md)
- **Development Guide:** [DEVELOPMENT.md](DEVELOPMENT.md)

---

## 📝 Changelog

### v0.2.0 (2025-11-05) - Critical Fixes

**🐛 Bug Fixes:**
- Fixed critical race condition in event streaming (event queue architecture)
- Fixed import path issues in enhanced_pipeline.py
- Fixed memory leaks in event translator (buffer size limits)
- Improved error recovery and subprocess management

**📚 Documentation:**
- Comprehensive README overhaul with detailed implementation instructions
- Added troubleshooting guide
- Added architecture diagrams
- Added FIXES_SUMMARY.md

See [FIXES_SUMMARY.md](FIXES_SUMMARY.md) for technical details.

### v0.1.0 (2025-11-05) - Initial Release

**✨ Features:**
- Basic pipeline implementation
- Event streaming (SSE)
- Session management (per-user isolation)
- JSON-RPC ↔ OpenAI event translation
- Subprocess lifecycle management
- Error handling and recovery
- Slash command routing (`/plan`, `/solve`, `/code`, `/auto`, `/browser`)
- Docker deployment

**📋 Planned:**
- Phase 2: WebSocket support, browser UI, terminal UI
- Phase 3: Auto Drive visualization, settings panel, full feature parity

See [INTEGRATION_STRATEGY.md](../INTEGRATION_STRATEGY.md) for full roadmap.

---

## 🗺️ Roadmap

### Phase 1: Foundation ✅ Complete
- [x] Core pipeline implementation
- [x] Basic event translation
- [x] Session management
- [x] Docker deployment
- [x] Slash command support

### Phase 2: Enhancement 🚧 In Progress
- [ ] WebSocket real-time communication
- [ ] Browser screenshot display
- [ ] Terminal session UI
- [ ] Approval flow UI
- [ ] File diff viewer

### Phase 3: Polish 📋 Planned
- [ ] Auto Drive progress tracking
- [ ] Multi-agent visualization
- [ ] Settings panel integration
- [ ] Performance optimization
- [ ] Comprehensive testing

See [INTEGRATION_STRATEGY.md](../INTEGRATION_STRATEGY.md) for detailed roadmap.

---

<div align="center">

**Made with ❤️ by the Code community**

[⭐ Star on GitHub](https://github.com/just-every/code) · [🐛 Report Bug](https://github.com/just-every/code/issues) · [💡 Request Feature](https://github.com/just-every/code/issues)

</div>
