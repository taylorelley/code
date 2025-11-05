<script lang="ts">
  /**
   * Auto Drive Panel Component
   *
   * Displays Auto Drive orchestration progress including:
   * - Current status
   * - Progress tracking
   * - Agent execution status
   * - Decision transcript
   * - Timeline view
   */
  import { currentSession } from '../../stores/codeStore';
  import type { AutoDriveProgress } from '../../stores/codeStore';

  $: autoDrive = $currentSession?.autoDrive;

  function getStatusColor(status: string): string {
    switch (status) {
      case 'thinking': return 'bg-blue-500';
      case 'acting': return 'bg-green-500';
      case 'reviewing': return 'bg-yellow-500';
      case 'complete': return 'bg-green-600';
      case 'failed': return 'bg-red-500';
      case 'paused': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'starting': return '🚀';
      case 'thinking': return '🤔';
      case 'acting': return '⚡';
      case 'reviewing': return '👁️';
      case 'complete': return '✅';
      case 'failed': return '❌';
      case 'paused': return '⏸️';
      default: return '⏳';
    }
  }

  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }
</script>

<div class="auto-drive-panel bg-white rounded-lg shadow-lg border border-gray-200">
  {#if !autoDrive}
    <div class="p-8 text-center text-gray-500">
      <div class="text-6xl mb-4">🤖</div>
      <p class="text-lg font-medium">Auto Drive Not Active</p>
      <p class="mt-2 text-sm">Use <code class="bg-gray-100 px-2 py-1 rounded">/auto &lt;task&gt;</code> to start autonomous task execution</p>
    </div>
  {:else}
    <!-- Header -->
    <div class="p-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <!-- Status Icon -->
          <div class="text-3xl">
            {getStatusIcon(autoDrive.status)}
          </div>

          <div>
            <h3 class="text-lg font-semibold text-gray-900">
              Auto Drive
            </h3>
            <div class="flex items-center space-x-2 mt-1">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(autoDrive.status)} text-white">
                {autoDrive.status.toUpperCase()}
              </span>
              {#if autoDrive.progress.description}
                <span class="text-sm text-gray-600">
                  {autoDrive.progress.description}
                </span>
              {/if}
            </div>
          </div>
        </div>

        <!-- Progress -->
        {#if autoDrive.progress.total > 0}
          <div class="text-right">
            <div class="text-sm text-gray-600">
              Step {autoDrive.progress.current} of {autoDrive.progress.total}
            </div>
            <div class="mt-1 w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full {getStatusColor(autoDrive.status)} transition-all duration-300"
                style="width: {(autoDrive.progress.current / autoDrive.progress.total) * 100}%"
              ></div>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <div class="p-4 space-y-4">
      <!-- Active Agents -->
      {#if autoDrive.agents.length > 0}
        <div>
          <h4 class="text-sm font-semibold text-gray-900 mb-2">Active Agents</h4>
          <div class="space-y-2">
            {#each autoDrive.agents as agent}
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center space-x-3">
                  <div class="flex-shrink-0">
                    {#if agent.status === 'running'}
                      <div class="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                    {:else if agent.status === 'completed'}
                      <svg class="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                    {:else}
                      <div class="h-5 w-5 border-2 border-gray-300 rounded-full"></div>
                    {/if}
                  </div>

                  <div>
                    <div class="font-medium text-gray-900">{agent.name}</div>
                    {#if agent.output}
                      <div class="text-sm text-gray-600 mt-1">{agent.output}</div>
                    {/if}
                  </div>
                </div>

                <span class="text-xs text-gray-500 uppercase">{agent.status}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Transcript -->
      {#if autoDrive.transcript.length > 0}
        <div>
          <h4 class="text-sm font-semibold text-gray-900 mb-2">Decision Transcript</h4>
          <div class="space-y-2 max-h-96 overflow-y-auto">
            {#each autoDrive.transcript as entry}
              <div class="flex space-x-3 p-3 rounded-lg {entry.role === 'user' ? 'bg-blue-50' : entry.role === 'assistant' ? 'bg-green-50' : 'bg-gray-50'}">
                <div class="flex-shrink-0">
                  {#if entry.role === 'user'}
                    <div class="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                      U
                    </div>
                  {:else if entry.role === 'assistant'}
                    <div class="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center text-white font-medium">
                      A
                    </div>
                  {:else}
                    <div class="h-8 w-8 rounded-full bg-gray-500 flex items-center justify-center text-white font-medium">
                      S
                    </div>
                  {/if}
                </div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-900 capitalize">{entry.role}</span>
                    <span class="text-xs text-gray-500">{formatTimestamp(entry.timestamp)}</span>
                  </div>
                  <div class="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                    {entry.content}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .auto-drive-panel {
    max-height: 800px;
    overflow: hidden;
  }

  /* Scrollbar styling */
  .overflow-y-auto::-webkit-scrollbar {
    width: 6px;
  }

  .overflow-y-auto::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 3px;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
</style>
