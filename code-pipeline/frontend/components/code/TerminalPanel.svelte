<script lang="ts">
  /**
   * Terminal Panel Component
   *
   * Web-based terminal emulator using xterm.js
   * Features:
   * - Real-time output streaming
   * - Interactive input
   * - Multi-terminal support
   * - Resizable
   */
  import { onMount, onDestroy } from 'svelte';
  import { activeTerminals, sendTerminalInput } from '../../stores/codeStore';
  import type { TerminalSession } from '../../stores/codeStore';

  // Import xterm.js (needs to be installed: npm install xterm)
  // @ts-ignore
  import { Terminal } from 'xterm';
  // @ts-ignore
  import { FitAddon } from 'xterm-addon-fit';
  // @ts-ignore
  import { WebLinksAddon } from 'xterm-addon-web-links';

  export let terminalId: string;
  export let autoFocus = false;

  let container: HTMLDivElement;
  let terminal: any = null;
  let fitAddon: any = null;
  let resizeObserver: ResizeObserver | null = null;

  // Track last output index to avoid duplicates
  let lastOutputIndex = 0;

  $: terminalSession = $activeTerminals.find(t => t.id === terminalId);

  onMount(() => {
    // Initialize xterm.js
    terminal = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#ffffff',
        cursorAccent: '#000000',
        selectionBackground: '#3a3d41',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      scrollback: 1000,
      convertEol: true
    });

    // Add fit addon
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    // Add web links addon
    terminal.loadAddon(new WebLinksAddon());

    // Open terminal in container
    terminal.open(container);

    // Fit terminal to container
    setTimeout(() => fitAddon.fit(), 0);

    // Handle input
    terminal.onData((data: string) => {
      sendTerminalInput(terminalId, data);
    });

    // Auto focus
    if (autoFocus) {
      terminal.focus();
    }

    // Setup resize observer
    resizeObserver = new ResizeObserver(() => {
      if (fitAddon) {
        fitAddon.fit();
      }
    });

    resizeObserver.observe(container);

    // Write welcome message
    terminal.writeln('\x1b[1;32mCode Pipeline Terminal\x1b[0m');
    terminal.writeln('Connected to Code session\n');
  });

  onDestroy(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
    }

    if (terminal) {
      terminal.dispose();
    }
  });

  // Watch for new output
  $: if (terminalSession && terminal) {
    const output = terminalSession.output;

    // Write new output lines
    for (let i = lastOutputIndex; i < output.length; i++) {
      const line = output[i];

      if (line.type === 'stderr') {
        terminal.write('\x1b[31m'); // Red color for stderr
      }

      terminal.write(line.data);

      if (line.type === 'stderr') {
        terminal.write('\x1b[0m'); // Reset color
      }
    }

    lastOutputIndex = output.length;
  }

  function clear() {
    if (terminal) {
      terminal.clear();
      lastOutputIndex = terminalSession?.output.length ?? 0;
    }
  }

  function copySelection() {
    if (terminal) {
      const selection = terminal.getSelection();
      if (selection) {
        navigator.clipboard.writeText(selection);
      }
    }
  }
</script>

<!-- Import xterm.js CSS -->
<svelte:head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
</svelte:head>

<div class="terminal-panel bg-gray-900 rounded-lg shadow-lg overflow-hidden">
  <!-- Header -->
  <div class="terminal-header flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
    <div class="flex items-center space-x-2">
      <div class="flex space-x-1.5">
        <div class="w-3 h-3 bg-red-500 rounded-full"></div>
        <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
        <div class="w-3 h-3 bg-green-500 rounded-full"></div>
      </div>

      <span class="text-sm text-gray-400 ml-3">
        Terminal {terminalId}
      </span>

      {#if terminalSession?.cwd}
        <span class="text-xs text-gray-500">
          • {terminalSession.cwd}
        </span>
      {/if}
    </div>

    <div class="flex items-center space-x-2">
      <button
        on:click={copySelection}
        class="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
        title="Copy selection"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </button>

      <button
        on:click={clear}
        class="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
        title="Clear terminal"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>

  <!-- Terminal Container -->
  <div
    bind:this={container}
    class="terminal-container"
  ></div>
</div>

<style>
  .terminal-panel {
    height: 100%;
    min-height: 400px;
    display: flex;
    flex-direction: column;
  }

  .terminal-container {
    flex: 1;
    padding: 8px;
    overflow: hidden;
  }

  /* Override xterm.js styles for better appearance */
  :global(.xterm) {
    height: 100%;
  }

  :global(.xterm-viewport) {
    overflow-y: auto !important;
  }

  :global(.xterm-screen) {
    height: 100% !important;
  }
</style>
