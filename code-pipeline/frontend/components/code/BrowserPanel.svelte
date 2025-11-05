<script lang="ts">
  /**
   * Browser Panel Component
   *
   * Displays browser screenshots and interaction history.
   * Shows:
   * - Latest screenshot
   * - URL and page title
   * - Screenshot history
   * - Viewport information
   */
  import { latestScreenshot, currentSession } from '../../stores/codeStore';
  import type { BrowserScreenshot } from '../../stores/codeStore';

  let selectedScreenshot: BrowserScreenshot | null = null;
  let showHistory = false;

  $: if ($latestScreenshot && !selectedScreenshot) {
    selectedScreenshot = $latestScreenshot;
  }

  function selectScreenshot(screenshot: BrowserScreenshot) {
    selectedScreenshot = screenshot;
  }

  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }

  function copyUrl() {
    if (selectedScreenshot?.metadata.url) {
      navigator.clipboard.writeText(selectedScreenshot.metadata.url);
    }
  }
</script>

<div class="browser-panel bg-white rounded-lg shadow-lg border border-gray-200">
  {#if !$latestScreenshot}
    <div class="p-8 text-center text-gray-500">
      <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
      <p class="mt-4 text-lg font-medium">No browser session</p>
      <p class="mt-2 text-sm">Use <code class="bg-gray-100 px-2 py-1 rounded">/browser</code> or <code class="bg-gray-100 px-2 py-1 rounded">/chrome</code> to start</p>
    </div>
  {:else}
    <!-- Header -->
    <div class="p-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex-1 min-w-0">
          <!-- Page Title -->
          {#if selectedScreenshot?.metadata.title}
            <h3 class="text-lg font-medium text-gray-900 truncate">
              {selectedScreenshot.metadata.title}
            </h3>
          {/if}

          <!-- URL -->
          {#if selectedScreenshot?.metadata.url}
            <div class="mt-1 flex items-center space-x-2">
              <a
                href={selectedScreenshot.metadata.url}
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm text-blue-600 hover:text-blue-800 truncate flex-1"
              >
                {selectedScreenshot.metadata.url}
              </a>
              <button
                on:click={copyUrl}
                class="flex-shrink-0 p-1 hover:bg-gray-100 rounded"
                title="Copy URL"
              >
                <svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          {/if}
        </div>

        <!-- History Toggle -->
        <button
          on:click={() => showHistory = !showHistory}
          class="ml-4 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {showHistory ? 'Hide' : 'Show'} History
        </button>
      </div>

      <!-- Viewport Info -->
      {#if selectedScreenshot?.metadata.viewport}
        <div class="mt-2 text-xs text-gray-500">
          {selectedScreenshot.metadata.viewport.width} × {selectedScreenshot.metadata.viewport.height}
        </div>
      {/if}
    </div>

    <div class="flex">
      <!-- Main Screenshot Display -->
      <div class="flex-1 p-4">
        {#if selectedScreenshot}
          <div class="screenshot-container bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={selectedScreenshot.data}
              alt="Browser screenshot"
              class="w-full h-auto"
            />
          </div>

          <div class="mt-2 text-xs text-gray-500 text-center">
            Captured at {formatTimestamp(selectedScreenshot.timestamp)}
          </div>
        {/if}
      </div>

      <!-- History Sidebar -->
      {#if showHistory}
        <div class="w-64 border-l border-gray-200 p-4 overflow-y-auto max-h-[600px]">
          <h4 class="text-sm font-semibold text-gray-900 mb-3">Screenshot History</h4>

          <div class="space-y-2">
            {#each $currentSession?.browserScreenshots || [] as screenshot (screenshot.id)}
              <button
                on:click={() => selectScreenshot(screenshot)}
                class="w-full text-left p-2 rounded-lg hover:bg-gray-100 transition-colors border-2"
                class:border-blue-500={selectedScreenshot?.id === screenshot.id}
                class:border-transparent={selectedScreenshot?.id !== screenshot.id}
              >
                <!-- Thumbnail -->
                <img
                  src={screenshot.data}
                  alt="Screenshot thumbnail"
                  class="w-full h-24 object-cover rounded mb-2"
                />

                <!-- Info -->
                <div class="text-xs text-gray-600 truncate">
                  {screenshot.metadata.title || 'Untitled'}
                </div>
                <div class="text-xs text-gray-400 mt-1">
                  {formatTimestamp(screenshot.timestamp)}
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .browser-panel {
    max-height: 800px;
    overflow: hidden;
  }

  .screenshot-container {
    max-height: 600px;
    overflow: auto;
  }

  /* Smooth scrolling */
  .screenshot-container,
  .overflow-y-auto {
    scroll-behavior: smooth;
  }
</style>
