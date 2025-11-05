# Frontend Integration Guide - Code Pipeline Phase 2

Complete guide for integrating Code Pipeline Svelte components into Open WebUI.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Component Integration](#component-integration)
5. [Store Setup](#store-setup)
6. [WebSocket Configuration](#websocket-configuration)
7. [Usage Examples](#usage-examples)
8. [Customization](#customization)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Phase 2 adds rich UI components to enhance the Code Pipeline experience:

- **ActivityCards.svelte** - Display tool executions (bash, file edits, MCP, web search)
- **BrowserPanel.svelte** - Show browser screenshots and interaction history
- **TerminalPanel.svelte** - Web-based terminal emulator with xterm.js
- **AutoDrivePanel.svelte** - Auto Drive orchestration progress dashboard
- **ApprovalModal.svelte** - Interactive approval flow for commands and file changes
- **codeStore.ts** - Svelte store for state management
- **Enhanced Backend** - WebSocket support for real-time updates

---

## Prerequisites

### Software Requirements

- Node.js 20+ (for Open WebUI)
- pnpm 9+ (package manager)
- Code Pipeline backend running (from Phase 1)
- Open WebUI frontend codebase

### Dependencies

Add to Open WebUI's `package.json`:

```json
{
  "dependencies": {
    "xterm": "^5.3.0",
    "xterm-addon-fit": "^0.8.0",
    "xterm-addon-web-links": "^0.9.0"
  }
}
```

Install:

```bash
cd /path/to/open-webui
pnpm install xterm xterm-addon-fit xterm-addon-web-links
```

---

## Installation

### Step 1: Copy Components

Copy the Code Pipeline components to Open WebUI:

```bash
# From code-pipeline directory
cp -r frontend/components/code /path/to/open-webui/src/lib/components/
cp -r frontend/stores/codeStore.ts /path/to/open-webui/src/lib/stores/
```

Your Open WebUI structure should now have:

```
open-webui/src/lib/
├── components/
│   ├── code/
│   │   ├── ActivityCards.svelte
│   │   ├── BrowserPanel.svelte
│   │   ├── TerminalPanel.svelte
│   │   ├── AutoDrivePanel.svelte
│   │   └── ApprovalModal.svelte
│   └── ... (other components)
└── stores/
    ├── codeStore.ts
    └── ... (other stores)
```

### Step 2: Update Backend

Replace the base pipeline with the enhanced version:

```bash
# In code-pipeline directory
cp backend/enhanced_pipeline.py pipelines/code_pipeline.py
cp backend/websocket_handler.py backend/
cp utils/enhanced_event_translator.py utils/
```

Update `requirements.txt`:

```txt
# Add WebSocket support
websockets>=12.0
```

Reinstall:

```bash
pip install -r requirements.txt
```

---

## Component Integration

### Main Chat Component

Integrate Code components into Open WebUI's main chat view:

**File:** `/path/to/open-webui/src/routes/+page.svelte`

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    connectWebSocket,
    disconnectWebSocket,
    currentSession,
    pendingApprovals
  } from '$lib/stores/codeStore';

  // Import Code components
  import ActivityCards from '$lib/components/code/ActivityCards.svelte';
  import BrowserPanel from '$lib/components/code/BrowserPanel.svelte';
  import TerminalPanel from '$lib/components/code/TerminalPanel.svelte';
  import AutoDrivePanel from '$lib/components/code/AutoDrivePanel.svelte';
  import ApprovalModal from '$lib/components/code/ApprovalModal.svelte';

  // Your existing code...
  let sessionId = 'user-session-123'; // Get from your session management
  let showBrowser = false;
  let showTerminal = false;
  let showAutoDrive = false;

  onMount(() => {
    // Connect WebSocket when component mounts
    connectWebSocket(sessionId, 'ws://localhost:9099/ws/' + sessionId);
  });

  onDestroy(() => {
    // Disconnect when component unmounts
    disconnectWebSocket();
  });
</script>

<!-- Your existing chat UI -->
<div class="chat-container">
  <!-- Chat messages... -->

  <!-- Code Pipeline Components -->
  <div class="code-panels grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
    <!-- Activity Cards (always visible) -->
    <div>
      <h3 class="text-lg font-semibold mb-2">Active Tools</h3>
      <ActivityCards />
    </div>

    <!-- Browser Panel (conditional) -->
    {#if showBrowser}
      <div>
        <h3 class="text-lg font-semibold mb-2">Browser</h3>
        <BrowserPanel />
      </div>
    {/if}

    <!-- Terminal Panel (conditional) -->
    {#if showTerminal}
      <div class="col-span-full">
        <h3 class="text-lg font-semibold mb-2">Terminal</h3>
        <TerminalPanel terminalId="default" autoFocus={true} />
      </div>
    {/if}

    <!-- Auto Drive Panel (conditional) -->
    {#if showAutoDrive || $currentSession?.autoDrive}
      <div class="col-span-full">
        <h3 class="text-lg font-semibold mb-2">Auto Drive</h3>
        <AutoDrivePanel />
      </div>
    {/if}
  </div>
</div>

<!-- Approval Modal (global) -->
<ApprovalModal show={$pendingApprovals.length > 0} />

<style>
  .code-panels {
    max-width: 1400px;
    margin: 0 auto;
  }
</style>
```

---

## Store Setup

### Initializing the Store

The Code store is already set up, but you need to connect it to your session:

```typescript
// In your session initialization code
import { connectWebSocket } from '$lib/stores/codeStore';

function initializeCodeSession(userId: string) {
  const sessionId = `session_${userId}`;
  const wsUrl = `ws://localhost:9099/ws/${sessionId}`;

  connectWebSocket(sessionId, wsUrl);
}
```

### Accessing Store Data

```typescript
import {
  currentSession,
  activeTools,
  pendingApprovals,
  latestScreenshot,
  activeTerminals
} from '$lib/stores/codeStore';

// Use in Svelte components:
$: console.log('Active tools:', $activeTools);
$: console.log('Pending approvals:', $pendingApprovals.length);
```

---

## WebSocket Configuration

### Backend WebSocket Endpoint

The enhanced backend provides a WebSocket endpoint. Add to your FastAPI app:

**File:** `backend/main.py` (in code-pipeline)

```python
from fastapi import FastAPI, WebSocket
from backend.websocket_handler import websocket_endpoint

app = FastAPI()

@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    await websocket_endpoint(websocket, session_id)
```

### Client-Side Connection

The `codeStore.ts` handles WebSocket connection automatically:

```typescript
// Automatic reconnection on disconnect
export function connectWebSocket(sessionId: string, url?: string) {
  // ... connection logic with auto-reconnect
}
```

---

## Usage Examples

### Example 1: Simple Chat with Activity Cards

```svelte
<script lang="ts">
  import ActivityCards from '$lib/components/code/ActivityCards.svelte';
  import { currentSession } from '$lib/stores/codeStore';
</script>

<div class="chat-view">
  <div class="messages">
    <!-- Your chat messages -->
  </div>

  <!-- Show activity cards if there are running tools -->
  {#if $currentSession && $currentSession.tools.size > 0}
    <div class="activity-section mt-4">
      <ActivityCards />
    </div>
  {/if}
</div>
```

### Example 2: Browser Integration

```svelte
<script lang="ts">
  import BrowserPanel from '$lib/components/code/BrowserPanel.svelte';
  import { latestScreenshot } from '$lib/stores/codeStore';
</script>

<!-- Show browser panel when screenshot is available -->
{#if $latestScreenshot}
  <div class="browser-view">
    <BrowserPanel />
  </div>
{/if}
```

### Example 3: Terminal Session

```svelte
<script lang="ts">
  import TerminalPanel from '$lib/components/code/TerminalPanel.svelte';
  import { activeTerminals } from '$lib/stores/codeStore';
</script>

<!-- Show terminal for each active session -->
{#each $activeTerminals as terminal (terminal.id)}
  <div class="terminal-container mb-4">
    <TerminalPanel terminalId={terminal.id} autoFocus={false} />
  </div>
{/each}
```

### Example 4: Auto Drive Dashboard

```svelte
<script lang="ts">
  import AutoDrivePanel from '$lib/components/code/AutoDrivePanel.svelte';
  import { currentSession } from '$lib/stores/codeStore';
</script>

<!-- Show Auto Drive panel when active -->
{#if $currentSession?.autoDrive}
  <div class="auto-drive-view">
    <AutoDrivePanel />
  </div>
{/if}
```

### Example 5: Approval Flow

```svelte
<script lang="ts">
  import ApprovalModal from '$lib/components/code/ApprovalModal.svelte';
  import { pendingApprovals } from '$lib/stores/codeStore';

  let showApprovalModal = false;

  $: showApprovalModal = $pendingApprovals.length > 0;
</script>

<!-- Approval modal shows automatically when needed -->
<ApprovalModal
  show={showApprovalModal}
  onClose={() => showApprovalModal = false}
/>
```

---

## Customization

### Styling

All components use Tailwind CSS classes. Customize by modifying the Svelte files or overriding with custom CSS:

```css
/* Custom styles for Code components */
.activity-cards {
  /* Override activity card styles */
}

.browser-panel {
  /* Override browser panel styles */
}

.terminal-panel {
  /* Override terminal styles */
}
```

### Theme Integration

Components support dark/light themes via Tailwind's dark mode:

```svelte
<!-- Add dark mode class to parent -->
<div class="dark">
  <ActivityCards />
</div>
```

### Configuring xterm.js

Customize terminal appearance in `TerminalPanel.svelte`:

```typescript
terminal = new Terminal({
  cursorBlink: true,
  fontSize: 14,
  fontFamily: 'Menlo, Monaco, "Courier New", monospace',
  theme: {
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    // ... customize colors
  },
  scrollback: 1000,
  convertEol: true
});
```

---

## Troubleshooting

### WebSocket Connection Failed

**Problem:** Components show "Not connected" or events don't update.

**Solutions:**

1. Check backend is running:
   ```bash
   # Should show WebSocket endpoint
   curl http://localhost:9099/health
   ```

2. Check WebSocket URL in browser console:
   ```javascript
   // Should connect without errors
   const ws = new WebSocket('ws://localhost:9099/ws/test');
   ```

3. Verify CORS settings in backend:
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### xterm.js Not Rendering

**Problem:** Terminal shows blank or doesn't render.

**Solutions:**

1. Ensure xterm CSS is loaded:
   ```svelte
   <svelte:head>
     <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
   </svelte:head>
   ```

2. Check container has dimensions:
   ```css
   .terminal-container {
     width: 100%;
     height: 400px; /* Must have explicit height */
   }
   ```

3. Call fitAddon after mount:
   ```typescript
   onMount(() => {
     terminal.open(container);
     setTimeout(() => fitAddon.fit(), 0);
   });
   ```

### Images Not Displaying

**Problem:** Browser screenshots don't show.

**Solutions:**

1. Check image data format:
   ```typescript
   // Must be data URL
   assert(screenshot.data.startsWith('data:image/'));
   ```

2. Verify base64 encoding in backend:
   ```python
   image_data = f"data:image/png;base64,{base64.b64encode(bytes).decode()}"
   ```

3. Check CSP headers allow data URLs:
   ```html
   <meta http-equiv="Content-Security-Policy" content="img-src 'self' data:;">
   ```

### Store Not Updating

**Problem:** UI doesn't react to store changes.

**Solutions:**

1. Use reactive statements:
   ```svelte
   $: console.log('Tools changed:', $activeTools);
   ```

2. Ensure store is imported correctly:
   ```typescript
   import { activeTools } from '$lib/stores/codeStore';
   // NOT: import activeTools from '...';
   ```

3. Check WebSocket is connected:
   ```typescript
   import { isConnected } from '$lib/stores/codeStore';
   $: console.log('Connected:', $isConnected);
   ```

---

## Performance Optimization

### Lazy Loading

Load terminal component only when needed:

```svelte
<script lang="ts">
  let TerminalPanel;
  let showTerminal = false;

  async function loadTerminal() {
    TerminalPanel = (await import('$lib/components/code/TerminalPanel.svelte')).default;
    showTerminal = true;
  }
</script>

{#if showTerminal}
  <svelte:component this={TerminalPanel} terminalId="default" />
{:else}
  <button on:click={loadTerminal}>Open Terminal</button>
{/if}
```

### Debouncing Updates

For high-frequency events, debounce updates:

```typescript
import { debounce } from 'lodash-es';

const debouncedUpdate = debounce((data) => {
  // Update UI
}, 100);
```

### Virtual Scrolling

For long lists (e.g., terminal output), use virtual scrolling:

```bash
pnpm install svelte-virtual-list
```

```svelte
<script>
  import VirtualList from 'svelte-virtual-list';

  let terminalLines = [...];
</script>

<VirtualList items={terminalLines} let:item>
  <div class="terminal-line">{item}</div>
</VirtualList>
```

---

## Advanced Integration

### Custom Events

Emit custom events from components:

```svelte
<!-- In component -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function handleToolClick(tool) {
    dispatch('toolSelected', { tool });
  }
</script>

<!-- In parent -->
<ActivityCards
  on:toolSelected={(e) => console.log('Tool selected:', e.detail.tool)}
/>
```

### SSR Considerations

Components use browser-only APIs (WebSocket, xterm.js). Handle SSR:

```svelte
<script lang="ts">
  import { browser } from '$app/environment';

  let component;

  $: if (browser) {
    import('$lib/components/code/TerminalPanel.svelte')
      .then(m => component = m.default);
  }
</script>

{#if browser && component}
  <svelte:component this={component} />
{/if}
```

---

## Next Steps

1. ✅ Copy components to Open WebUI
2. ✅ Install dependencies (xterm.js)
3. ✅ Update backend with WebSocket support
4. ✅ Test WebSocket connection
5. ✅ Integrate components into chat view
6. ✅ Test with real Code session
7. ✅ Customize styling to match Open WebUI theme

---

## Support

- **Issues:** https://github.com/just-every/code/issues
- **Documentation:** See `DEVELOPMENT.md` for more details
- **Examples:** See `tests/test_integration.py` for usage examples

---

**Integration complete! 🎉**

You now have a fully functional web-based Code Pipeline with rich UI components.
