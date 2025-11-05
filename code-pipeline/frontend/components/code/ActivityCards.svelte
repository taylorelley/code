<script lang="ts">
  /**
   * Activity Cards Component
   *
   * Displays active and recent tool executions as collapsible cards.
   * Shows:
   * - Bash command executions
   * - File changes
   * - MCP tool calls
   * - Web searches
   */
  import { activeTools, currentSession } from '../../stores/codeStore';
  import type { ToolExecution } from '../../stores/codeStore';

  // Expanded state for each card
  let expanded: Set<string> = new Set();

  function toggleCard(id: string) {
    if (expanded.has(id)) {
      expanded.delete(id);
    } else {
      expanded.add(id);
    }
    expanded = expanded; // Trigger reactivity
  }

  function getToolIcon(type: string): string {
    switch (type) {
      case 'bash': return '⚡';
      case 'file_edit': return '📝';
      case 'mcp': return '🔧';
      case 'web_search': return '🔍';
      default: return '🔹';
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'running': return 'border-blue-500 bg-blue-50';
      case 'completed': return 'border-green-500 bg-green-50';
      case 'failed': return 'border-red-500 bg-red-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  }

  function formatDuration(start: string, end?: string): string {
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const duration = (endTime.getTime() - startTime.getTime()) / 1000;

    if (duration < 1) return `${Math.round(duration * 1000)}ms`;
    if (duration < 60) return `${duration.toFixed(1)}s`;
    return `${Math.floor(duration / 60)}m ${Math.round(duration % 60)}s`;
  }

  function getToolTitle(tool: ToolExecution): string {
    switch (tool.type) {
      case 'bash':
        return tool.data.command || 'Command execution';
      case 'file_edit':
        const changes = tool.data.changes || [];
        return `${changes.length} file${changes.length !== 1 ? 's' : ''} changed`;
      case 'mcp':
        return `${tool.data.server}.${tool.data.tool}`;
      case 'web_search':
        return tool.data.query || 'Web search';
      default:
        return 'Tool execution';
    }
  }
</script>

<div class="activity-cards space-y-2">
  {#if $activeTools.length === 0}
    <div class="text-center text-gray-500 py-4">
      No active tools
    </div>
  {:else}
    {#each $activeTools as tool (tool.id)}
      <div
        class="card border-2 rounded-lg shadow-sm transition-all duration-200 {getStatusColor(tool.status)}"
        class:shadow-lg={expanded.has(tool.id)}
      >
        <!-- Card Header -->
        <button
          class="w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-80 transition-colors"
          on:click={() => toggleCard(tool.id)}
        >
          <div class="flex items-center space-x-3 flex-1 min-w-0">
            <!-- Icon -->
            <span class="text-2xl flex-shrink-0" aria-label={tool.type}>
              {getToolIcon(tool.type)}
            </span>

            <!-- Title -->
            <div class="flex-1 min-w-0 text-left">
              <div class="font-medium text-gray-900 truncate">
                {getToolTitle(tool)}
              </div>
              <div class="text-sm text-gray-500">
                {tool.type} • {formatDuration(tool.startTime, tool.endTime)}
              </div>
            </div>

            <!-- Status Badge -->
            <div class="flex-shrink-0">
              {#if tool.status === 'running'}
                <div class="flex items-center space-x-2">
                  <div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  <span class="text-sm text-blue-600">Running</span>
                </div>
              {:else if tool.status === 'completed'}
                <span class="text-sm text-green-600">✓ Completed</span>
              {:else if tool.status === 'failed'}
                <span class="text-sm text-red-600">✗ Failed</span>
              {/if}
            </div>
          </div>

          <!-- Expand Icon -->
          <svg
            class="ml-3 h-5 w-5 text-gray-400 transition-transform duration-200 flex-shrink-0"
            class:rotate-180={expanded.has(tool.id)}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Card Body (Expanded) -->
        {#if expanded.has(tool.id)}
          <div class="px-4 pb-4 border-t border-gray-200">
            <div class="mt-3 space-y-2">
              {#if tool.type === 'bash'}
                <!-- Bash Command Details -->
                <div>
                  <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Command</div>
                  <pre class="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">{tool.data.command}</pre>
                </div>

                {#if tool.data.exit_code !== undefined}
                  <div>
                    <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Exit Code</div>
                    <div class="text-sm {tool.data.exit_code === 0 ? 'text-green-600' : 'text-red-600'}">
                      {tool.data.exit_code}
                    </div>
                  </div>
                {/if}

                {#if tool.output && tool.output.length > 0}
                  <div>
                    <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Output</div>
                    <pre class="bg-gray-800 text-white p-3 rounded text-sm overflow-x-auto max-h-64 overflow-y-auto">{tool.output.join('\n')}</pre>
                  </div>
                {/if}

              {:else if tool.type === 'file_edit'}
                <!-- File Changes Details -->
                <div>
                  <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Files Changed</div>
                  <ul class="space-y-1">
                    {#each tool.data.changes as change}
                      <li class="text-sm flex items-center space-x-2">
                        {#if change.kind === 'add'}
                          <span class="text-green-600">+</span>
                        {:else if change.kind === 'delete'}
                          <span class="text-red-600">-</span>
                        {:else}
                          <span class="text-blue-600">~</span>
                        {/if}
                        <code class="bg-gray-100 px-2 py-1 rounded">{change.path}</code>
                      </li>
                    {/each}
                  </ul>
                </div>

              {:else if tool.type === 'mcp'}
                <!-- MCP Tool Details -->
                <div>
                  <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Server</div>
                  <div class="text-sm font-mono">{tool.data.server}</div>
                </div>
                <div>
                  <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Tool</div>
                  <div class="text-sm font-mono">{tool.data.tool}</div>
                </div>
                {#if tool.data.arguments}
                  <div>
                    <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Arguments</div>
                    <pre class="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{JSON.stringify(tool.data.arguments, null, 2)}</pre>
                  </div>
                {/if}

              {:else if tool.type === 'web_search'}
                <!-- Web Search Details -->
                <div>
                  <div class="text-xs font-semibold text-gray-700 uppercase mb-1">Query</div>
                  <div class="text-sm">{tool.data.query}</div>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  .activity-cards {
    max-height: 600px;
    overflow-y: auto;
  }

  .card {
    transition: all 0.2s ease;
  }

  .card:hover {
    transform: translateY(-2px);
  }

  /* Scrollbar styling */
  .activity-cards::-webkit-scrollbar {
    width: 8px;
  }

  .activity-cards::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }

  .activity-cards::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
  }

  .activity-cards::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
</style>
