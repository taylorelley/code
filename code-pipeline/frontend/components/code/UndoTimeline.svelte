<script lang="ts">
  /**
   * UndoTimeline - Visualize and navigate code change history
   *
   * Features:
   * - Timeline visualization of all changes
   * - Undo/redo functionality
   * - Diff preview for each change
   * - Branch visualization for Auto Drive
   * - Time travel debugging
   */

  import { onMount, onDestroy } from 'svelte';
  import { writable, derived, type Writable } from 'svelte/store';

  // Change event interface
  export interface ChangeEvent {
    id: string;
    timestamp: number;
    type: 'file_edit' | 'bash' | 'browser_action' | 'mcp_call';
    description: string;
    files: string[];
    diff?: string;
    reversible: boolean;
    metadata?: Record<string, any>;
    parentId?: string; // For branching
    children?: string[]; // Child change IDs
  }

  // Props
  export let sessionId: string;

  // Stores
  const undoStack: Writable<ChangeEvent[]> = writable([]);
  const currentIndex: Writable<number> = writable(-1);

  // Derived stores
  const canUndo = derived(currentIndex, ($currentIndex) => $currentIndex > 0);
  const canRedo = derived(
    [currentIndex, undoStack],
    ([$currentIndex, $undoStack]) => $currentIndex < $undoStack.length - 1
  );

  // UI state
  let selectedEvent: ChangeEvent | null = null;
  let showDiff = false;
  let viewMode: 'linear' | 'tree' = 'linear';
  let autoScroll = true;

  // Filter options
  let filterType: 'all' | 'file_edit' | 'bash' | 'browser_action' | 'mcp_call' = 'all';
  let searchQuery = '';

  // Filtered events
  $: filteredEvents = $undoStack.filter((event) => {
    const matchesType = filterType === 'all' || event.type === filterType;
    const matchesSearch =
      searchQuery === '' ||
      event.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.files.some((file) => file.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesType && matchesSearch;
  });

  // Load change history
  onMount(async () => {
    try {
      const response = await fetch(`/api/code/undo-stack/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        undoStack.set(data.stack || []);
        currentIndex.set(data.currentIndex ?? -1);
      }
    } catch (error) {
      console.error('Failed to load undo stack:', error);
    }

    // Subscribe to real-time updates via WebSocket
    // (assumes WebSocket connection is managed elsewhere)
    window.addEventListener('code:change-recorded', handleChangeRecorded);
    window.addEventListener('code:undo-performed', handleUndoPerformed);
    window.addEventListener('code:redo-performed', handleRedoPerformed);

    return () => {
      window.removeEventListener('code:change-recorded', handleChangeRecorded);
      window.removeEventListener('code:undo-performed', handleUndoPerformed);
      window.removeEventListener('code:redo-performed', handleRedoPerformed);
    };
  });

  // Handle real-time events
  function handleChangeRecorded(event: CustomEvent) {
    const change = event.detail as ChangeEvent;
    undoStack.update((stack) => {
      // Truncate stack if not at end
      const newStack = stack.slice(0, $currentIndex + 1);
      newStack.push(change);
      return newStack;
    });
    currentIndex.update((i) => i + 1);

    if (autoScroll) {
      scrollToLatest();
    }
  }

  function handleUndoPerformed(event: CustomEvent) {
    currentIndex.update((i) => Math.max(0, i - 1));
  }

  function handleRedoPerformed(event: CustomEvent) {
    currentIndex.update((i) => Math.min($undoStack.length - 1, i + 1));
  }

  // Undo/redo actions
  async function undo() {
    if (!$canUndo) return;

    try {
      const response = await fetch(`/api/code/undo/${sessionId}`, {
        method: 'POST',
      });

      if (response.ok) {
        currentIndex.update((i) => i - 1);
      }
    } catch (error) {
      console.error('Undo failed:', error);
    }
  }

  async function redo() {
    if (!$canRedo) return;

    try {
      const response = await fetch(`/api/code/redo/${sessionId}`, {
        method: 'POST',
      });

      if (response.ok) {
        currentIndex.update((i) => i + 1);
      }
    } catch (error) {
      console.error('Redo failed:', error);
    }
  }

  // Jump to specific point in history
  async function jumpToEvent(index: number) {
    const delta = index - $currentIndex;
    if (delta === 0) return;

    try {
      const response = await fetch(`/api/code/jump/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetIndex: index }),
      });

      if (response.ok) {
        currentIndex.set(index);
      }
    } catch (error) {
      console.error('Jump failed:', error);
    }
  }

  // Select event for diff preview
  function selectEvent(event: ChangeEvent) {
    selectedEvent = event;
    showDiff = true;
  }

  // Scroll to latest change
  function scrollToLatest() {
    setTimeout(() => {
      const timeline = document.querySelector('.timeline-track');
      if (timeline) {
        timeline.scrollTop = timeline.scrollHeight;
      }
    }, 100);
  }

  // Format timestamp
  function formatTime(timestamp: number): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) {
      // < 1 minute
      return 'Just now';
    } else if (diff < 3600000) {
      // < 1 hour
      const mins = Math.floor(diff / 60000);
      return `${mins}m ago`;
    } else if (diff < 86400000) {
      // < 1 day
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    } else {
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
  }

  // Get event icon
  function getEventIcon(type: string): string {
    switch (type) {
      case 'file_edit':
        return '📝';
      case 'bash':
        return '⚡';
      case 'browser_action':
        return '🌐';
      case 'mcp_call':
        return '🔧';
      default:
        return '•';
    }
  }

  // Get event color
  function getEventColor(type: string): string {
    switch (type) {
      case 'file_edit':
        return 'var(--code-info)';
      case 'bash':
        return 'var(--code-warning)';
      case 'browser_action':
        return 'var(--code-accent)';
      case 'mcp_call':
        return 'var(--code-success)';
      default:
        return 'var(--code-text-muted)';
    }
  }

  // Keyboard shortcuts
  function handleKeydown(event: KeyboardEvent) {
    if (event.ctrlKey || event.metaKey) {
      if (event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        undo();
      } else if ((event.key === 'z' && event.shiftKey) || event.key === 'y') {
        event.preventDefault();
        redo();
      }
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="undo-timeline" data-testid="undo-timeline">
  <!-- Header -->
  <div class="timeline-header">
    <h3>⏱️ Change History</h3>
    <div class="header-controls">
      <button
        class="btn-icon"
        class:active={viewMode === 'linear'}
        on:click={() => (viewMode = 'linear')}
        aria-label="Linear view"
        title="Linear view"
      >
        ═
      </button>
      <button
        class="btn-icon"
        class:active={viewMode === 'tree'}
        on:click={() => (viewMode = 'tree')}
        aria-label="Tree view"
        title="Tree view (shows branches)"
      >
        ⋔
      </button>
      <label class="auto-scroll-toggle">
        <input type="checkbox" bind:checked={autoScroll} />
        <span>Auto-scroll</span>
      </label>
    </div>
  </div>

  <!-- Controls -->
  <div class="timeline-controls">
    <button
      class="btn"
      on:click={undo}
      disabled={!$canUndo}
      aria-label="Undo"
      title="Undo (Ctrl+Z)"
    >
      ⏪ Undo
    </button>
    <div class="change-counter">
      {$currentIndex + 1} / {$undoStack.length}
    </div>
    <button
      class="btn"
      on:click={redo}
      disabled={!$canRedo}
      aria-label="Redo"
      title="Redo (Ctrl+Shift+Z)"
    >
      Redo ⏩
    </button>
  </div>

  <!-- Filters -->
  <div class="timeline-filters">
    <select bind:value={filterType} aria-label="Filter by type">
      <option value="all">All Changes</option>
      <option value="file_edit">File Edits</option>
      <option value="bash">Bash Commands</option>
      <option value="browser_action">Browser Actions</option>
      <option value="mcp_call">MCP Calls</option>
    </select>
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search changes..."
      aria-label="Search changes"
    />
  </div>

  <!-- Timeline Track -->
  <div class="timeline-track" role="list" aria-label="Change history timeline">
    {#if filteredEvents.length === 0}
      <div class="empty-state">
        <p>No changes yet</p>
        <p class="help-text">Changes will appear here as you work</p>
      </div>
    {:else}
      {#each filteredEvents as event, i (event.id)}
        {@const eventIndex = $undoStack.indexOf(event)}
        {@const isCurrent = eventIndex === $currentIndex}
        {@const isPast = eventIndex <= $currentIndex}
        {@const isFuture = eventIndex > $currentIndex}

        <div
          class="timeline-event"
          class:active={isCurrent}
          class:past={isPast && !isCurrent}
          class:future={isFuture}
          on:click={() => jumpToEvent(eventIndex)}
          on:keydown={(e) => e.key === 'Enter' && jumpToEvent(eventIndex)}
          role="listitem"
          tabindex="0"
          aria-label={`${event.description} at ${formatTime(event.timestamp)}`}
        >
          <!-- Event marker -->
          <div class="event-marker" style="background-color: {getEventColor(event.type)}">
            {#if isCurrent}
              <div class="current-indicator" />
            {/if}
          </div>

          <!-- Event line (vertical connector) -->
          <div
            class="event-line"
            class:active={isPast}
            style="border-color: {getEventColor(event.type)}"
          />

          <!-- Event content -->
          <div class="event-content">
            <div class="event-header">
              <span class="event-icon">{getEventIcon(event.type)}</span>
              <span class="event-description">{event.description}</span>
              {#if isCurrent}
                <span class="current-badge">Current</span>
              {/if}
            </div>

            <div class="event-metadata">
              <span class="event-time">{formatTime(event.timestamp)}</span>
              {#if event.files.length > 0}
                <span class="event-files">
                  {event.files.length} file{event.files.length !== 1 ? 's' : ''}
                </span>
              {/if}
              {#if !event.reversible}
                <span class="non-reversible-badge" title="This change cannot be undone">
                  ⚠️ Non-reversible
                </span>
              {/if}
            </div>

            {#if event.files.length > 0}
              <details class="event-files-list">
                <summary>Files ({event.files.length})</summary>
                <ul>
                  {#each event.files as file}
                    <li>{file}</li>
                  {/each}
                </ul>
              </details>
            {/if}

            {#if event.diff}
              <button class="btn-view-diff" on:click|stopPropagation={() => selectEvent(event)}>
                👁️ View Diff
              </button>
            {/if}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Diff Preview Modal -->
  {#if showDiff && selectedEvent}
    <div class="diff-modal" on:click={() => (showDiff = false)}>
      <div class="diff-modal-content" on:click|stopPropagation>
        <div class="diff-modal-header">
          <h4>{selectedEvent.description}</h4>
          <button class="btn-close" on:click={() => (showDiff = false)}>✕</button>
        </div>
        <div class="diff-modal-body">
          <pre class="diff-preview"><code>{selectedEvent.diff}</code></pre>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .undo-timeline {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--code-bg-primary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-md);
    overflow: hidden;
  }

  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .timeline-header h3 {
    margin: 0;
    font-size: var(--code-font-lg);
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: var(--code-spacing-sm);
  }

  .btn-icon {
    background: none;
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    padding: 0.25rem 0.5rem;
    cursor: pointer;
    color: var(--code-text-secondary);
    font-size: 1.25rem;
  }

  .btn-icon:hover {
    background-color: var(--code-bg-hover);
  }

  .btn-icon.active {
    background-color: var(--code-accent);
    color: white;
    border-color: var(--code-accent);
  }

  .auto-scroll-toggle {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: var(--code-font-sm);
    color: var(--code-text-secondary);
    cursor: pointer;
  }

  .timeline-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .change-counter {
    font-weight: 500;
    color: var(--code-text-primary);
  }

  .timeline-filters {
    display: flex;
    gap: var(--code-spacing-sm);
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .timeline-filters select {
    flex: 0 0 auto;
  }

  .timeline-filters input {
    flex: 1;
  }

  .timeline-track {
    flex: 1;
    overflow-y: auto;
    padding: var(--code-spacing-md);
    position: relative;
  }

  .timeline-event {
    position: relative;
    display: flex;
    gap: var(--code-spacing-md);
    padding: var(--code-spacing-md);
    margin-bottom: var(--code-spacing-sm);
    border-radius: var(--code-radius-md);
    cursor: pointer;
    transition: all 0.2s;
  }

  .timeline-event:hover {
    background-color: var(--code-bg-hover);
  }

  .timeline-event.active {
    background-color: var(--code-bg-active);
    border: 2px solid var(--code-accent);
  }

  .timeline-event.past {
    opacity: 1;
  }

  .timeline-event.future {
    opacity: 0.5;
  }

  .event-marker {
    position: relative;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 0.25rem;
  }

  .current-indicator {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8px;
    height: 8px;
    background-color: white;
    border-radius: 50%;
    animation: code-pulse 2s infinite;
  }

  .event-line {
    position: absolute;
    left: 19px;
    top: 32px;
    bottom: -8px;
    width: 2px;
    border-left: 2px dashed var(--code-border);
  }

  .event-line.active {
    border-left-style: solid;
  }

  .timeline-event:last-child .event-line {
    display: none;
  }

  .event-content {
    flex: 1;
  }

  .event-header {
    display: flex;
    align-items: center;
    gap: var(--code-spacing-sm);
    margin-bottom: 0.25rem;
  }

  .event-icon {
    font-size: 1.25rem;
  }

  .event-description {
    flex: 1;
    font-weight: 500;
    color: var(--code-text-primary);
  }

  .current-badge {
    padding: 0.125rem 0.5rem;
    background-color: var(--code-accent);
    color: white;
    border-radius: var(--code-radius-sm);
    font-size: var(--code-font-xs);
    font-weight: 600;
  }

  .event-metadata {
    display: flex;
    gap: var(--code-spacing-sm);
    font-size: var(--code-font-sm);
    color: var(--code-text-muted);
  }

  .event-files {
    padding: 0.125rem 0.375rem;
    background-color: var(--code-bg-tertiary);
    border-radius: var(--code-radius-sm);
  }

  .non-reversible-badge {
    padding: 0.125rem 0.375rem;
    background-color: var(--code-warning);
    color: white;
    border-radius: var(--code-radius-sm);
    font-size: var(--code-font-xs);
  }

  .event-files-list {
    margin-top: 0.5rem;
    font-size: var(--code-font-sm);
  }

  .event-files-list summary {
    cursor: pointer;
    color: var(--code-text-secondary);
  }

  .event-files-list ul {
    margin: 0.5rem 0 0 1rem;
    padding: 0;
    list-style: none;
  }

  .event-files-list li {
    padding: 0.25rem;
    color: var(--code-text-muted);
    font-family: monospace;
  }

  .btn-view-diff {
    margin-top: 0.5rem;
    padding: 0.25rem 0.75rem;
    background-color: var(--code-bg-secondary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    cursor: pointer;
    font-size: var(--code-font-sm);
    color: var(--code-text-primary);
  }

  .btn-view-diff:hover {
    background-color: var(--code-bg-hover);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: var(--code-text-muted);
  }

  .empty-state p {
    margin: 0.25rem 0;
  }

  .diff-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: code-fade-in 0.2s;
  }

  .diff-modal-content {
    background-color: var(--code-bg-primary);
    border-radius: var(--code-radius-lg);
    width: 90%;
    max-width: 900px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px var(--code-shadow);
  }

  .diff-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .diff-modal-header h4 {
    margin: 0;
    font-size: var(--code-font-lg);
  }

  .btn-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--code-text-secondary);
    padding: 0.25rem 0.5rem;
  }

  .btn-close:hover {
    color: var(--code-text-primary);
  }

  .diff-modal-body {
    flex: 1;
    overflow: auto;
    padding: var(--code-spacing-md);
  }

  .diff-preview {
    background-color: var(--code-bg-secondary);
    padding: var(--code-spacing-md);
    border-radius: var(--code-radius-md);
    overflow-x: auto;
    font-size: var(--code-font-sm);
    line-height: 1.5;
  }

  @media (max-width: 768px) {
    .timeline-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--code-spacing-sm);
    }

    .timeline-controls {
      flex-direction: column;
      gap: var(--code-spacing-sm);
    }

    .timeline-filters {
      flex-direction: column;
    }
  }
</style>
