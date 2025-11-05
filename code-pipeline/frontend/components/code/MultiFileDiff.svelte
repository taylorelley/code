<script lang="ts">
  /**
   * MultiFileDiff - Multi-file diff viewer with syntax highlighting
   *
   * Features:
   * - Split view (side-by-side comparison)
   * - Unified view (inline diff)
   * - Syntax highlighting
   * - Line-by-line navigation
   * - Accept/reject individual hunks
   * - Multiple file tabs
   * - Keyboard navigation
   */

  import { onMount } from 'svelte';
  import { writable, type Writable } from 'svelte/store';

  // Diff interfaces
  export interface DiffLine {
    type: 'add' | 'remove' | 'context';
    content: string;
    oldLineNum?: number;
    newLineNum?: number;
  }

  export interface DiffHunk {
    oldStart: number;
    oldLines: number;
    newStart: number;
    newLines: number;
    lines: DiffLine[];
    header: string;
  }

  export interface FileDiff {
    path: string;
    oldPath?: string;
    language: string;
    hunks: DiffHunk[];
    additions: number;
    deletions: number;
    status: 'modified' | 'added' | 'deleted' | 'renamed';
  }

  // Props
  export let sessionId: string;
  export let diffs: FileDiff[] = [];
  export let onApplyHunk: (filePath: string, hunkIndex: number) => void = () => {};
  export let onRejectHunk: (filePath: string, hunkIndex: number) => void = () => {};

  // State
  let activeTab = 0;
  let viewMode: 'split' | 'unified' = 'split';
  let showLineNumbers = true;
  let wrapLines = false;

  // Load diffs if not provided via props
  onMount(async () => {
    if (diffs.length === 0) {
      await loadDiffs();
    }
  });

  async function loadDiffs() {
    try {
      const response = await fetch(`/api/code/diffs/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        diffs = data.diffs || [];
      }
    } catch (error) {
      console.error('Failed to load diffs:', error);
    }
  }

  // Get active file
  $: activeFile = diffs[activeTab];

  // Count changes
  function countAdditions(file: FileDiff): number {
    return file.additions;
  }

  function countDeletions(file: FileDiff): number {
    return file.deletions;
  }

  // Get file status icon
  function getStatusIcon(status: string): string {
    switch (status) {
      case 'added':
        return '+';
      case 'deleted':
        return '✗';
      case 'renamed':
        return '→';
      case 'modified':
      default:
        return '●';
    }
  }

  // Get file status color
  function getStatusColor(status: string): string {
    switch (status) {
      case 'added':
        return 'var(--code-success)';
      case 'deleted':
        return 'var(--code-error)';
      case 'renamed':
        return 'var(--code-info)';
      case 'modified':
      default:
        return 'var(--code-warning)';
    }
  }

  // Simple syntax highlighting based on language
  function highlightSyntax(content: string, language: string): string {
    // This is a simplified version - in production, use a library like highlight.js or Prism
    const keywords: Record<string, string[]> = {
      typescript: ['const', 'let', 'var', 'function', 'class', 'interface', 'type', 'import', 'export', 'async', 'await'],
      javascript: ['const', 'let', 'var', 'function', 'class', 'import', 'export', 'async', 'await'],
      python: ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'return', 'async', 'await'],
      rust: ['fn', 'let', 'mut', 'struct', 'impl', 'trait', 'use', 'pub', 'async', 'await'],
    };

    const langKeywords = keywords[language.toLowerCase()] || [];
    let highlighted = content;

    // Escape HTML
    highlighted = highlighted.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Highlight keywords
    langKeywords.forEach((keyword) => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      highlighted = highlighted.replace(
        regex,
        `<span class="keyword">${keyword}</span>`
      );
    });

    // Highlight strings
    highlighted = highlighted.replace(
      /(["'`])((?:\\.|(?!\1).)*?)\1/g,
      '<span class="string">$1$2$1</span>'
    );

    // Highlight comments
    highlighted = highlighted.replace(
      /(\/\/.*$)/gm,
      '<span class="comment">$1</span>'
    );
    highlighted = highlighted.replace(
      /(\/\*[\s\S]*?\*\/)/g,
      '<span class="comment">$1</span>'
    );

    return highlighted;
  }

  // Navigate between files
  function previousFile() {
    if (activeTab > 0) {
      activeTab--;
    }
  }

  function nextFile() {
    if (activeTab < diffs.length - 1) {
      activeTab++;
    }
  }

  // Keyboard shortcuts
  function handleKeydown(event: KeyboardEvent) {
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case '[':
          event.preventDefault();
          previousFile();
          break;
        case ']':
          event.preventDefault();
          nextFile();
          break;
      }
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="multi-file-diff" data-testid="multi-file-diff">
  <!-- Tabs -->
  <div class="diff-tabs" role="tablist">
    {#if diffs.length === 0}
      <div class="empty-tabs">No file changes</div>
    {:else}
      {#each diffs as file, i (file.path)}
        <button
          class="tab"
          class:active={activeTab === i}
          on:click={() => (activeTab = i)}
          role="tab"
          aria-selected={activeTab === i}
          title={file.path}
        >
          <span
            class="status-icon"
            style="color: {getStatusColor(file.status)}"
            aria-label={file.status}
          >
            {getStatusIcon(file.status)}
          </span>
          <span class="file-path">{file.path.split('/').pop()}</span>
          <span class="change-count">
            {#if file.additions > 0}
              <span class="additions">+{file.additions}</span>
            {/if}
            {#if file.deletions > 0}
              <span class="deletions">-{file.deletions}</span>
            {/if}
          </span>
        </button>
      {/each}
    {/if}
  </div>

  <!-- Toolbar -->
  {#if activeFile}
    <div class="diff-toolbar">
      <div class="toolbar-group">
        <button
          class="btn-toolbar"
          class:active={viewMode === 'split'}
          on:click={() => (viewMode = 'split')}
          title="Split view (Ctrl+1)"
        >
          ⫦ Split
        </button>
        <button
          class="btn-toolbar"
          class:active={viewMode === 'unified'}
          on:click={() => (viewMode = 'unified')}
          title="Unified view (Ctrl+2)"
        >
          ▤ Unified
        </button>
      </div>

      <div class="toolbar-group">
        <label class="toolbar-checkbox">
          <input type="checkbox" bind:checked={showLineNumbers} />
          <span>Line numbers</span>
        </label>
        <label class="toolbar-checkbox">
          <input type="checkbox" bind:checked={wrapLines} />
          <span>Wrap lines</span>
        </label>
      </div>

      <div class="toolbar-group">
        <button
          class="btn-toolbar"
          on:click={previousFile}
          disabled={activeTab === 0}
          title="Previous file (Ctrl+[)"
        >
          ← Prev
        </button>
        <button
          class="btn-toolbar"
          on:click={nextFile}
          disabled={activeTab === diffs.length - 1}
          title="Next file (Ctrl+])"
        >
          Next →
        </button>
      </div>
    </div>

    <!-- File info -->
    <div class="file-info">
      <div class="file-path-full">{activeFile.path}</div>
      {#if activeFile.oldPath && activeFile.oldPath !== activeFile.path}
        <div class="file-renamed">
          Renamed from <code>{activeFile.oldPath}</code>
        </div>
      {/if}
    </div>

    <!-- Diff view -->
    <div class="diff-view {viewMode}" class:wrap-lines={wrapLines}>
      {#if viewMode === 'split'}
        <!-- Split view -->
        <div class="split-container">
          <div class="split-side old-side">
            <div class="side-header">Before</div>
            <div class="side-content">
              {#each activeFile.hunks as hunk, hunkIdx}
                <div class="hunk">
                  <div class="hunk-header">{hunk.header}</div>
                  {#each hunk.lines as line, lineIdx}
                    {#if line.type !== 'add'}
                      <div
                        class="diff-line {line.type}"
                        data-line-num={line.oldLineNum}
                      >
                        {#if showLineNumbers}
                          <span class="line-num">{line.oldLineNum ?? ''}</span>
                        {/if}
                        <span class="line-marker">
                          {line.type === 'remove' ? '-' : ' '}
                        </span>
                        <pre class="line-content">{@html highlightSyntax(
                          line.content,
                          activeFile.language
                        )}</pre>
                      </div>
                    {/if}
                  {/each}
                </div>
              {/each}
            </div>
          </div>

          <div class="split-side new-side">
            <div class="side-header">After</div>
            <div class="side-content">
              {#each activeFile.hunks as hunk, hunkIdx}
                <div class="hunk">
                  <div class="hunk-header">
                    <button
                      class="btn-hunk-action apply"
                      on:click={() => onApplyHunk(activeFile.path, hunkIdx)}
                      title="Apply this hunk"
                    >
                      ✓
                    </button>
                    <button
                      class="btn-hunk-action reject"
                      on:click={() => onRejectHunk(activeFile.path, hunkIdx)}
                      title="Reject this hunk"
                    >
                      ✗
                    </button>
                    {hunk.header}
                  </div>
                  {#each hunk.lines as line, lineIdx}
                    {#if line.type !== 'remove'}
                      <div
                        class="diff-line {line.type}"
                        data-line-num={line.newLineNum}
                      >
                        {#if showLineNumbers}
                          <span class="line-num">{line.newLineNum ?? ''}</span>
                        {/if}
                        <span class="line-marker">
                          {line.type === 'add' ? '+' : ' '}
                        </span>
                        <pre class="line-content">{@html highlightSyntax(
                          line.content,
                          activeFile.language
                        )}</pre>
                      </div>
                    {/if}
                  {/each}
                </div>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <!-- Unified view -->
        <div class="unified-container">
          {#each activeFile.hunks as hunk, hunkIdx}
            <div class="hunk">
              <div class="hunk-header">
                <button
                  class="btn-hunk-action apply"
                  on:click={() => onApplyHunk(activeFile.path, hunkIdx)}
                  title="Apply this hunk"
                >
                  ✓ Apply
                </button>
                <button
                  class="btn-hunk-action reject"
                  on:click={() => onRejectHunk(activeFile.path, hunkIdx)}
                  title="Reject this hunk"
                >
                  ✗ Reject
                </button>
                <span class="hunk-info">
                  @@ -{hunk.oldStart},{hunk.oldLines} +{hunk.newStart},{hunk.newLines} @@
                </span>
              </div>
              {#each hunk.lines as line, lineIdx}
                <div
                  class="diff-line {line.type}"
                  data-old-line={line.oldLineNum}
                  data-new-line={line.newLineNum}
                >
                  {#if showLineNumbers}
                    <span class="line-num old">{line.oldLineNum ?? ''}</span>
                    <span class="line-num new">{line.newLineNum ?? ''}</span>
                  {/if}
                  <span class="line-marker">
                    {line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' '}
                  </span>
                  <pre class="line-content">{@html highlightSyntax(
                    line.content,
                    activeFile.language
                  )}</pre>
                </div>
              {/each}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .multi-file-diff {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--code-bg-primary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-md);
    overflow: hidden;
  }

  .diff-tabs {
    display: flex;
    gap: 0.25rem;
    padding: var(--code-spacing-sm);
    border-bottom: 1px solid var(--code-border);
    overflow-x: auto;
    background-color: var(--code-bg-secondary);
  }

  .empty-tabs {
    padding: var(--code-spacing-md);
    color: var(--code-text-muted);
    text-align: center;
    width: 100%;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border: none;
    background: none;
    color: var(--code-text-secondary);
    cursor: pointer;
    border-radius: var(--code-radius-sm);
    white-space: nowrap;
    transition: all 0.2s;
    max-width: 250px;
  }

  .tab:hover {
    background-color: var(--code-bg-hover);
    color: var(--code-text-primary);
  }

  .tab.active {
    background-color: var(--code-bg-primary);
    color: var(--code-text-primary);
    border: 1px solid var(--code-border);
  }

  .status-icon {
    font-weight: bold;
  }

  .file-path {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .change-count {
    display: flex;
    gap: 0.25rem;
    font-size: var(--code-font-xs);
  }

  .additions {
    color: var(--code-success);
  }

  .deletions {
    color: var(--code-error);
  }

  .diff-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
    background-color: var(--code-bg-secondary);
    flex-wrap: wrap;
    gap: var(--code-spacing-sm);
  }

  .toolbar-group {
    display: flex;
    align-items: center;
    gap: var(--code-spacing-sm);
  }

  .btn-toolbar {
    padding: 0.25rem 0.75rem;
    border: 1px solid var(--code-border);
    background-color: var(--code-bg-primary);
    color: var(--code-text-primary);
    border-radius: var(--code-radius-sm);
    cursor: pointer;
    font-size: var(--code-font-sm);
  }

  .btn-toolbar:hover:not(:disabled) {
    background-color: var(--code-bg-hover);
  }

  .btn-toolbar.active {
    background-color: var(--code-accent);
    color: white;
    border-color: var(--code-accent);
  }

  .btn-toolbar:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .toolbar-checkbox {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: var(--code-font-sm);
    cursor: pointer;
  }

  .file-info {
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
    background-color: var(--code-bg-tertiary);
  }

  .file-path-full {
    font-family: monospace;
    font-size: var(--code-font-sm);
    color: var(--code-text-primary);
  }

  .file-renamed {
    font-size: var(--code-font-xs);
    color: var(--code-text-muted);
    margin-top: 0.25rem;
  }

  .diff-view {
    flex: 1;
    overflow: auto;
    background-color: var(--code-bg-primary);
  }

  .split-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--code-border);
    height: 100%;
  }

  .split-side {
    background-color: var(--code-bg-primary);
    overflow: auto;
  }

  .side-header {
    position: sticky;
    top: 0;
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    background-color: var(--code-bg-secondary);
    border-bottom: 1px solid var(--code-border);
    font-weight: 600;
    z-index: 10;
  }

  .side-content {
    font-family: monospace;
    font-size: var(--code-font-sm);
  }

  .unified-container {
    font-family: monospace;
    font-size: var(--code-font-sm);
  }

  .hunk {
    margin-bottom: var(--code-spacing-md);
  }

  .hunk-header {
    display: flex;
    align-items: center;
    gap: var(--code-spacing-sm);
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    background-color: var(--code-bg-tertiary);
    border-top: 1px solid var(--code-border);
    border-bottom: 1px solid var(--code-border);
    color: var(--code-text-muted);
    font-size: var(--code-font-xs);
  }

  .hunk-info {
    flex: 1;
  }

  .btn-hunk-action {
    padding: 0.125rem 0.5rem;
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    cursor: pointer;
    font-size: var(--code-font-xs);
    font-weight: 600;
  }

  .btn-hunk-action.apply {
    background-color: var(--code-success);
    color: white;
    border-color: var(--code-success);
  }

  .btn-hunk-action.reject {
    background-color: var(--code-error);
    color: white;
    border-color: var(--code-error);
  }

  .diff-line {
    display: flex;
    align-items: flex-start;
    min-height: 20px;
  }

  .diff-line.add {
    background-color: var(--code-diff-add-bg);
    border-left: 3px solid var(--code-diff-add-border);
  }

  .diff-line.remove {
    background-color: var(--code-diff-remove-bg);
    border-left: 3px solid var(--code-diff-remove-border);
  }

  .line-num {
    display: inline-block;
    width: 4rem;
    padding: 0 var(--code-spacing-sm);
    text-align: right;
    color: var(--code-text-muted);
    user-select: none;
    flex-shrink: 0;
  }

  .line-marker {
    display: inline-block;
    width: 2rem;
    text-align: center;
    color: var(--code-text-muted);
    user-select: none;
    flex-shrink: 0;
  }

  .line-content {
    flex: 1;
    margin: 0;
    padding: 0 var(--code-spacing-sm);
    white-space: pre;
    overflow-x: auto;
  }

  .diff-view.wrap-lines .line-content {
    white-space: pre-wrap;
    word-break: break-all;
  }

  /* Syntax highlighting */
  .line-content :global(.keyword) {
    color: var(--code-syntax-keyword);
    font-weight: 600;
  }

  .line-content :global(.string) {
    color: var(--code-syntax-string);
  }

  .line-content :global(.comment) {
    color: var(--code-syntax-comment);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .split-container {
      grid-template-columns: 1fr;
    }

    .diff-toolbar {
      flex-direction: column;
      align-items: stretch;
    }

    .toolbar-group {
      justify-content: space-between;
    }
  }
</style>
