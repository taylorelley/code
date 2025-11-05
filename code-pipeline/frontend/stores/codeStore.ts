/**
 * Code Pipeline Store
 *
 * Svelte store for managing Code pipeline state including:
 * - WebSocket connections
 * - Tool execution tracking
 * - Browser screenshots
 * - Terminal sessions
 * - Auto Drive progress
 * - Approval requests
 */

import { writable, derived, get } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';

// ============================================================================
// Types
// ============================================================================

export interface ToolExecution {
  id: string;
  type: 'bash' | 'file_edit' | 'mcp' | 'web_search';
  status: 'pending' | 'running' | 'completed' | 'failed';
  data: any;
  startTime: string;
  endTime?: string;
  output?: string[];
}

export interface BrowserScreenshot {
  id: string;
  data: string; // Base64 encoded image
  metadata: {
    url?: string;
    title?: string;
    timestamp?: string;
    viewport?: { width: number; height: number };
  };
  timestamp: string;
}

export interface TerminalSession {
  id: string;
  active: boolean;
  output: Array<{
    type: 'stdout' | 'stderr';
    data: string;
    timestamp: string;
  }>;
  cwd?: string;
}

export interface ApprovalRequest {
  id: string;
  type: 'command_execution' | 'file_changes';
  status: 'pending' | 'approved' | 'rejected';
  data: any;
  timestamp: string;
}

export interface AutoDriveProgress {
  status: 'starting' | 'thinking' | 'acting' | 'reviewing' | 'paused' | 'complete' | 'failed';
  progress: {
    current: number;
    total: number;
    description: string;
  };
  agents: Array<{
    name: string;
    status: string;
    output?: string;
  }>;
  transcript: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
  }>;
}

export interface CodeSession {
  id: string;
  connected: boolean;
  tools: Map<string, ToolExecution>;
  browserScreenshots: BrowserScreenshot[];
  terminalSessions: Map<string, TerminalSession>;
  approvalRequests: Map<string, ApprovalRequest>;
  autoDrive: AutoDriveProgress | null;
}

// ============================================================================
// Stores
// ============================================================================

// Active sessions
export const sessions: Writable<Map<string, CodeSession>> = writable(new Map());

// Current session ID
export const currentSessionId: Writable<string | null> = writable(null);

// WebSocket instance
export const ws: Writable<WebSocket | null> = writable(null);

// Connection state
export const isConnected: Writable<boolean> = writable(false);

// ============================================================================
// Derived Stores
// ============================================================================

// Current session
export const currentSession: Readable<CodeSession | null> = derived(
  [sessions, currentSessionId],
  ([$sessions, $currentSessionId]) => {
    if (!$currentSessionId) return null;
    return $sessions.get($currentSessionId) || null;
  }
);

// Active tools in current session
export const activeTools: Readable<ToolExecution[]> = derived(
  currentSession,
  ($currentSession) => {
    if (!$currentSession) return [];
    return Array.from($currentSession.tools.values())
      .filter(tool => tool.status === 'running' || tool.status === 'pending')
      .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime());
  }
);

// Pending approval requests
export const pendingApprovals: Readable<ApprovalRequest[]> = derived(
  currentSession,
  ($currentSession) => {
    if (!$currentSession) return [];
    return Array.from($currentSession.approvalRequests.values())
      .filter(req => req.status === 'pending')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }
);

// Latest browser screenshot
export const latestScreenshot: Readable<BrowserScreenshot | null> = derived(
  currentSession,
  ($currentSession) => {
    if (!$currentSession || $currentSession.browserScreenshots.length === 0) {
      return null;
    }
    return $currentSession.browserScreenshots[$currentSession.browserScreenshots.length - 1];
  }
);

// Active terminal sessions
export const activeTerminals: Readable<TerminalSession[]> = derived(
  currentSession,
  ($currentSession) => {
    if (!$currentSession) return [];
    return Array.from($currentSession.terminalSessions.values())
      .filter(term => term.active);
  }
);

// ============================================================================
// Actions
// ============================================================================

/**
 * Connect to Code Pipeline WebSocket
 */
export function connectWebSocket(sessionId: string, url?: string) {
  const wsUrl = url || `ws://localhost:9099/ws/${sessionId}`;

  const socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connected');
    isConnected.set(true);
    currentSessionId.set(sessionId);

    // Initialize session if it doesn't exist
    sessions.update($sessions => {
      if (!$sessions.has(sessionId)) {
        $sessions.set(sessionId, {
          id: sessionId,
          connected: true,
          tools: new Map(),
          browserScreenshots: [],
          terminalSessions: new Map(),
          approvalRequests: new Map(),
          autoDrive: null
        });
      } else {
        const session = $sessions.get(sessionId)!;
        session.connected = true;
        $sessions.set(sessionId, session);
      }
      return $sessions;
    });

    // Send ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }));
      } else {
        clearInterval(pingInterval);
      }
    }, 30000);
  };

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(sessionId, message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  socket.onclose = () => {
    console.log('WebSocket closed');
    isConnected.set(false);

    sessions.update($sessions => {
      const session = $sessions.get(sessionId);
      if (session) {
        session.connected = false;
        $sessions.set(sessionId, session);
      }
      return $sessions;
    });
  };

  ws.set(socket);
}

/**
 * Disconnect WebSocket
 */
export function disconnectWebSocket() {
  const socket = get(ws);
  if (socket) {
    socket.close();
    ws.set(null);
    isConnected.set(false);
  }
}

/**
 * Handle incoming WebSocket message
 */
function handleWebSocketMessage(sessionId: string, message: any) {
  const { type } = message;

  sessions.update($sessions => {
    const session = $sessions.get(sessionId);
    if (!session) return $sessions;

    switch (type) {
      case 'tool_execution':
        handleToolExecution(session, message);
        break;

      case 'browser_screenshot':
        handleBrowserScreenshot(session, message);
        break;

      case 'terminal_output':
        handleTerminalOutput(session, message);
        break;

      case 'approval_request':
        handleApprovalRequest(session, message);
        break;

      case 'approval_response':
        handleApprovalResponse(session, message);
        break;

      case 'auto_drive_update':
        handleAutoDriveUpdate(session, message);
        break;

      case 'pong':
        // Heartbeat response
        break;

      default:
        console.warn('Unknown message type:', type);
    }

    $sessions.set(sessionId, session);
    return $sessions;
  });
}

/**
 * Handle tool execution event
 */
function handleToolExecution(session: CodeSession, message: any) {
  const { tool_id, tool_type, status, data } = message;

  const existingTool = session.tools.get(tool_id);

  if (existingTool) {
    existingTool.status = status;
    existingTool.data = { ...existingTool.data, ...data };
    if (status === 'completed' || status === 'failed') {
      existingTool.endTime = new Date().toISOString();
    }
    session.tools.set(tool_id, existingTool);
  } else {
    session.tools.set(tool_id, {
      id: tool_id,
      type: tool_type,
      status,
      data,
      startTime: new Date().toISOString()
    });
  }
}

/**
 * Handle browser screenshot event
 */
function handleBrowserScreenshot(session: CodeSession, message: any) {
  const { data, metadata, timestamp } = message;

  session.browserScreenshots.push({
    id: `screenshot-${Date.now()}`,
    data,
    metadata: metadata || {},
    timestamp: timestamp || new Date().toISOString()
  });

  // Keep only last 10 screenshots
  if (session.browserScreenshots.length > 10) {
    session.browserScreenshots = session.browserScreenshots.slice(-10);
  }
}

/**
 * Handle terminal output event
 */
function handleTerminalOutput(session: CodeSession, message: any) {
  const { terminal_id, data, is_stderr, timestamp } = message;

  let terminal = session.terminalSessions.get(terminal_id);

  if (!terminal) {
    terminal = {
      id: terminal_id,
      active: true,
      output: []
    };
    session.terminalSessions.set(terminal_id, terminal);
  }

  terminal.output.push({
    type: is_stderr ? 'stderr' : 'stdout',
    data,
    timestamp: timestamp || new Date().toISOString()
  });

  // Keep only last 1000 lines
  if (terminal.output.length > 1000) {
    terminal.output = terminal.output.slice(-1000);
  }
}

/**
 * Handle approval request event
 */
function handleApprovalRequest(session: CodeSession, message: any) {
  const { request_id, request_type, data } = message;

  session.approvalRequests.set(request_id, {
    id: request_id,
    type: request_type,
    status: 'pending',
    data,
    timestamp: new Date().toISOString()
  });
}

/**
 * Handle approval response event
 */
function handleApprovalResponse(session: CodeSession, message: any) {
  const { request_id, decision } = message;

  const request = session.approvalRequests.get(request_id);
  if (request) {
    request.status = decision === 'approved' ? 'approved' : 'rejected';
    session.approvalRequests.set(request_id, request);
  }
}

/**
 * Handle Auto Drive update event
 */
function handleAutoDriveUpdate(session: CodeSession, message: any) {
  const { status, progress, agents, transcript } = message;

  session.autoDrive = {
    status,
    progress: progress || { current: 0, total: 0, description: '' },
    agents: agents || [],
    transcript: transcript || []
  };
}

/**
 * Send terminal input
 */
export function sendTerminalInput(terminalId: string, input: string) {
  const socket = get(ws);
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected');
    return;
  }

  socket.send(JSON.stringify({
    type: 'terminal_input',
    terminal_id: terminalId,
    data: input
  }));
}

/**
 * Send approval response
 */
export function sendApprovalResponse(
  requestId: string,
  decision: 'approved' | 'rejected',
  userData?: any
) {
  const socket = get(ws);
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected');
    return;
  }

  socket.send(JSON.stringify({
    type: 'approval_response',
    request_id: requestId,
    decision,
    user_data: userData
  }));
}

/**
 * Clear session data
 */
export function clearSession(sessionId: string) {
  sessions.update($sessions => {
    $sessions.delete(sessionId);
    return $sessions;
  });

  if (get(currentSessionId) === sessionId) {
    currentSessionId.set(null);
  }
}
