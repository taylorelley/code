<script lang="ts">
  /**
   * FileTree - Project file navigation with git integration
   *
   * Features:
   * - Hierarchical file tree display
   * - Fuzzy search with highlighting
   * - Git status indicators (modified, staged, untracked, deleted)
   * - Click to open file in diff viewer or editor
   * - Keyboard navigation (arrow keys, Enter, Space)
   * - Collapsible directories
   * - File icons based on type
   * - Lazy loading for large directories
   */

  import { onMount, tick } from 'svelte';
  import { writable, derived, type Writable } from 'svelte/store';

  // File node interface
  export interface FileNode {
    name: string;
    path: string;
    type: 'file' | 'directory';
    children?: FileNode[];
    gitStatus?: 'modified' | 'staged' | 'untracked' | 'deleted' | 'added';
    size?: number;
    depth: number;
  }

  // Props
  export let sessionId: string;
  export let workspacePath: string;
  export let onFileSelect: (path: string) => void = () => {};
  export let height = '100%';

  // Stores
  const fileTree: Writable<FileNode[]> = writable([]);
  const expandedDirs = writable(new Set<string>());
  const selectedFile: Writable<string | null> = writable(null);

  // UI state
  let searchQuery = '';
  let loading = false;
  let error: string | null = null;

  // Filtered and flattened tree for rendering
  $: flatTree = flattenTree($fileTree, $expandedDirs, searchQuery);

  // Load file tree
  onMount(async () => {
    await loadFileTree();

    // Subscribe to file system changes
    window.addEventListener('code:file-changed', handleFileChanged);
    window.addEventListener('code:git-status-changed', handleGitStatusChanged);

    return () => {
      window.removeEventListener('code:file-changed', handleFileChanged);
      window.removeEventListener('code:git-status-changed', handleGitStatusChanged);
    };
  });

  async function loadFileTree() {
    loading = true;
    error = null;

    try {
      const response = await fetch(`/api/code/file-tree/${sessionId}?path=${encodeURIComponent(workspacePath)}`);
      if (response.ok) {
        const data = await response.json();
        fileTree.set(data.tree || []);

        // Auto-expand root level
        expandedDirs.update((expanded) => {
          data.tree.forEach((node: FileNode) => {
            if (node.type === 'directory') {
              expanded.add(node.path);
            }
          });
          return expanded;
        });
      } else {
        error = 'Failed to load file tree';
      }
    } catch (e) {
      error = 'Failed to load file tree: ' + (e as Error).message;
    } finally {
      loading = false;
    }
  }

  function handleFileChanged(event: CustomEvent) {
    // Reload affected portion of tree
    loadFileTree();
  }

  function handleGitStatusChanged(event: CustomEvent) {
    // Update git status for changed files
    const { path, status } = event.detail;
    fileTree.update((tree) => updateGitStatus(tree, path, status));
  }

  function updateGitStatus(nodes: FileNode[], path: string, status: string): FileNode[] {
    return nodes.map((node) => {
      if (node.path === path) {
        return { ...node, gitStatus: status as FileNode['gitStatus'] };
      } else if (node.children) {
        return { ...node, children: updateGitStatus(node.children, path, status) };
      }
      return node;
    });
  }

  // Toggle directory expansion
  function toggleDir(path: string) {
    expandedDirs.update((expanded) => {
      if (expanded.has(path)) {
        expanded.delete(path);
      } else {
        expanded.add(path);
      }
      return new Set(expanded);
    });
  }

  // Select file
  function selectFile(path: string) {
    selectedFile.set(path);
    onFileSelect(path);
  }

  // Flatten tree for rendering
  function flattenTree(nodes: FileNode[], expanded: Set<string>, query: string): FileNode[] {
    const result: FileNode[] = [];

    function traverse(nodes: FileNode[], depth: number = 0) {
      for (const node of nodes) {
        // Filter by search query
        if (query && !matchesSearch(node, query)) {
          continue;
        }

        result.push({ ...node, depth });

        // Add children if directory is expanded
        if (node.type === 'directory' && node.children && expanded.has(node.path)) {
          traverse(node.children, depth + 1);
        }
      }
    }

    traverse(nodes);
    return result;
  }

  // Fuzzy search matching
  function matchesSearch(node: FileNode, query: string): boolean {
    if (!query) return true;

    const lowerQuery = query.toLowerCase();
    const lowerName = node.name.toLowerCase();
    const lowerPath = node.path.toLowerCase();

    // Simple substring match
    if (lowerName.includes(lowerQuery) || lowerPath.includes(lowerQuery)) {
      return true;
    }

    // Fuzzy match (e.g., "abc" matches "a_b_c.txt")
    let queryIndex = 0;
    for (let i = 0; i < lowerName.length && queryIndex < lowerQuery.length; i++) {
      if (lowerName[i] === lowerQuery[queryIndex]) {
        queryIndex++;
      }
    }
    if (queryIndex === lowerQuery.length) {
      return true;
    }

    // Check children
    if (node.children) {
      return node.children.some((child) => matchesSearch(child, query));
    }

    return false;
  }

  // Get file icon based on name/extension
  function getFileIcon(name: string, type: string): string {
    if (type === 'directory') {
      return '📁';
    }

    const ext = name.split('.').pop()?.toLowerCase();
    const iconMap: Record<string, string> = {
      // Code files
      ts: '🔷',
      tsx: '🔷',
      js: '🟨',
      jsx: '🟨',
      py: '🐍',
      rs: '🦀',
      go: '🐹',
      java: '☕',
      c: '🔧',
      cpp: '🔧',
      h: '🔧',
      hpp: '🔧',
      cs: '🔷',
      php: '🐘',
      rb: '💎',
      swift: '🍎',
      kt: '🟣',
      scala: '🔴',

      // Web files
      html: '🌐',
      css: '🎨',
      scss: '🎨',
      sass: '🎨',
      less: '🎨',
      vue: '💚',
      svelte: '🧡',

      // Config files
      json: '📋',
      yaml: '📋',
      yml: '📋',
      toml: '📋',
      xml: '📋',
      ini: '📋',
      conf: '📋',
      config: '📋',

      // Documentation
      md: '📝',
      mdx: '📝',
      txt: '📄',
      pdf: '📕',
      doc: '📘',
      docx: '📘',

      // Data files
      csv: '📊',
      tsv: '📊',
      sql: '🗄️',
      db: '🗄️',
      sqlite: '🗄️',

      // Images
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      gif: '🖼️',
      svg: '🖼️',
      ico: '🖼️',
      webp: '🖼️',

      // Archives
      zip: '📦',
      tar: '📦',
      gz: '📦',
      rar: '📦',
      '7z': '📦',

      // Build/Package
      lock: '🔒',
      'package.json': '📦',
      'Cargo.toml': '📦',
      'go.mod': '📦',
      'pom.xml': '📦',
      Gemfile: '💎',

      // Git
      gitignore: '🙈',
      gitattributes: '🔧',
    };

    return iconMap[ext || ''] || iconMap[name] || '📄';
  }

  // Get git status icon
  function getGitStatusIcon(status?: string): string {
    switch (status) {
      case 'modified':
        return '●';
      case 'staged':
        return '✓';
      case 'untracked':
        return '?';
      case 'deleted':
        return '✗';
      case 'added':
        return '+';
      default:
        return '';
    }
  }

  // Get git status color
  function getGitStatusColor(status?: string): string {
    switch (status) {
      case 'modified':
        return 'var(--code-warning)';
      case 'staged':
        return 'var(--code-success)';
      case 'untracked':
        return 'var(--code-info)';
      case 'deleted':
        return 'var(--code-error)';
      case 'added':
        return 'var(--code-success)';
      default:
        return 'transparent';
    }
  }

  // Format file size
  function formatSize(bytes?: number): string {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
    return `${(bytes / 1024 / 1024 / 1024).toFixed(1)}GB`;
  }

  // Keyboard navigation
  let focusedIndex = 0;

  function handleKeydown(event: KeyboardEvent) {
    const len = flatTree.length;
    if (len === 0) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        focusedIndex = Math.min(focusedIndex + 1, len - 1);
        scrollToFocused();
        break;
      case 'ArrowUp':
        event.preventDefault();
        focusedIndex = Math.max(focusedIndex - 1, 0);
        scrollToFocused();
        break;
      case 'ArrowRight': {
        event.preventDefault();
        const node = flatTree[focusedIndex];
        if (node.type === 'directory' && !$expandedDirs.has(node.path)) {
          toggleDir(node.path);
        }
        break;
      }
      case 'ArrowLeft': {
        event.preventDefault();
        const node = flatTree[focusedIndex];
        if (node.type === 'directory' && $expandedDirs.has(node.path)) {
          toggleDir(node.path);
        }
        break;
      }
      case 'Enter':
      case ' ': {
        event.preventDefault();
        const node = flatTree[focusedIndex];
        if (node.type === 'directory') {
          toggleDir(node.path);
        } else {
          selectFile(node.path);
        }
        break;
      }
    }
  }

  function scrollToFocused() {
    tick().then(() => {
      const element = document.querySelector(`[data-index="${focusedIndex}"]`);
      if (element) {
        element.scrollIntoView({ block: 'nearest' });
      }
    });
  }
</script>

<div
  class="file-tree"
  style="height: {height}"
  data-testid="file-tree"
  on:keydown={handleKeydown}
  tabindex="0"
  role="tree"
  aria-label="Project file tree"
>
  <!-- Header -->
  <div class="tree-header">
    <h3>📁 {workspacePath.split('/').pop() || 'Files'}</h3>
    <button class="btn-refresh" on:click={loadFileTree} aria-label="Refresh" title="Refresh">
      {#if loading}
        <span class="spinning">⟳</span>
      {:else}
        ⟳
      {/if}
    </button>
  </div>

  <!-- Search bar -->
  <div class="search-bar">
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search files..."
      aria-label="Search files"
    />
  </div>

  <!-- Tree view -->
  <div class="tree-view" role="group">
    {#if loading && flatTree.length === 0}
      <div class="loading-state">
        <span class="spinning">⟳</span>
        <p>Loading files...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
        <button class="btn" on:click={loadFileTree}>Retry</button>
      </div>
    {:else if flatTree.length === 0}
      <div class="empty-state">
        <p>No files found</p>
        {#if searchQuery}
          <p class="help-text">Try a different search query</p>
        {/if}
      </div>
    {:else}
      {#each flatTree as node, i (node.path)}
        <div
          class="tree-node"
          class:selected={$selectedFile === node.path}
          class:focused={focusedIndex === i}
          style="padding-left: {node.depth * 20}px"
          data-index={i}
          role="treeitem"
          aria-selected={$selectedFile === node.path}
          aria-expanded={node.type === 'directory' ? $expandedDirs.has(node.path) : undefined}
          tabindex="-1"
        >
          {#if node.type === 'directory'}
            <button
              class="dir-toggle"
              on:click={() => toggleDir(node.path)}
              on:keydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  toggleDir(node.path);
                }
              }}
              aria-label={$expandedDirs.has(node.path)
                ? `Collapse ${node.name}`
                : `Expand ${node.name}`}
            >
              {$expandedDirs.has(node.path) ? '▼' : '▶'}
            </button>
            <span class="node-icon">{getFileIcon(node.name, node.type)}</span>
            <span class="node-name">{node.name}</span>
          {:else}
            <button
              class="file-button"
              on:click={() => selectFile(node.path)}
              on:keydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  selectFile(node.path);
                }
              }}
              aria-label={`Open ${node.name}`}
            >
              <span class="node-icon">{getFileIcon(node.name, node.type)}</span>
              <span class="node-name">{node.name}</span>
              {#if node.size}
                <span class="node-size">{formatSize(node.size)}</span>
              {/if}
              {#if node.gitStatus}
                <span
                  class="git-status"
                  style="color: {getGitStatusColor(node.gitStatus)}"
                  title={node.gitStatus}
                >
                  {getGitStatusIcon(node.gitStatus)}
                </span>
              {/if}
            </button>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .file-tree {
    display: flex;
    flex-direction: column;
    background-color: var(--code-bg-primary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-md);
    overflow: hidden;
  }

  .file-tree:focus {
    outline: 2px solid var(--code-accent);
    outline-offset: -2px;
  }

  .tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .tree-header h3 {
    margin: 0;
    font-size: var(--code-font-lg);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .btn-refresh {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: var(--code-text-secondary);
    padding: 0.25rem;
  }

  .btn-refresh:hover {
    color: var(--code-text-primary);
  }

  .search-bar {
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .search-bar input {
    width: 100%;
    padding: var(--code-spacing-sm);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    background-color: var(--code-bg-secondary);
    color: var(--code-text-primary);
  }

  .tree-view {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .tree-node {
    display: flex;
    align-items: center;
    padding-right: var(--code-spacing-sm);
    min-height: 28px;
    border-bottom: 1px solid transparent;
  }

  .tree-node:hover {
    background-color: var(--code-bg-hover);
  }

  .tree-node.selected {
    background-color: var(--code-bg-active);
  }

  .tree-node.focused {
    border: 1px solid var(--code-accent);
    border-radius: var(--code-radius-sm);
  }

  .dir-toggle {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--code-text-secondary);
    font-size: 0.75rem;
    padding: 0.25rem;
    margin-right: 0.25rem;
  }

  .node-icon {
    margin-right: 0.5rem;
    font-size: 1rem;
  }

  .node-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--code-text-primary);
    font-size: var(--code-font-sm);
  }

  .node-size {
    margin-left: 0.5rem;
    font-size: var(--code-font-xs);
    color: var(--code-text-muted);
  }

  .git-status {
    margin-left: 0.5rem;
    font-weight: bold;
  }

  .file-button {
    display: flex;
    align-items: center;
    width: 100%;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    padding: 0.25rem;
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--code-spacing-lg);
    text-align: center;
    color: var(--code-text-muted);
  }

  .loading-state p,
  .error-state p,
  .empty-state p {
    margin: 0.5rem 0;
  }

  @media (max-width: 768px) {
    .tree-node {
      min-height: 36px;
    }

    .node-icon {
      font-size: 1.25rem;
    }

    .node-name {
      font-size: var(--code-font-base);
    }
  }
</style>
