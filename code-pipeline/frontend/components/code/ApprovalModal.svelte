<script lang="ts">
  /**
   * Approval Modal Component
   *
   * Interactive modal for approving/rejecting Code requests:
   * - Command execution approvals
   * - File change approvals
   * - Shows details and allows user decision
   */
  import { pendingApprovals, sendApprovalResponse } from '../../stores/codeStore';
  import type { ApprovalRequest } from '../../stores/codeStore';

  export let show = false;
  export let onClose: () => void = () => {};

  let selectedRequest: ApprovalRequest | null = null;
  let processing = false;

  $: if ($pendingApprovals.length > 0 && !selectedRequest) {
    selectedRequest = $pendingApprovals[0];
    show = true;
  }

  $: if ($pendingApprovals.length === 0) {
    selectedRequest = null;
    show = false;
  }

  async function handleDecision(decision: 'approved' | 'rejected') {
    if (!selectedRequest || processing) return;

    processing = true;

    try {
      sendApprovalResponse(selectedRequest.id, decision);

      // Move to next approval if available
      const nextApprovals = $pendingApprovals.filter(r => r.id !== selectedRequest!.id);
      if (nextApprovals.length > 0) {
        selectedRequest = nextApprovals[0];
      } else {
        selectedRequest = null;
        show = false;
        onClose();
      }
    } catch (error) {
      console.error('Error handling approval:', error);
    } finally {
      processing = false;
    }
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget && !processing) {
      // Don't close on backdrop click for approvals
      // User must explicitly approve or reject
    }
  }
</script>

{#if show && selectedRequest}
  <div
    class="fixed inset-0 z-50 overflow-y-auto"
    aria-labelledby="approval-modal-title"
    role="dialog"
    aria-modal="true"
  >
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
      on:click={handleBackdropClick}
    ></div>

    <!-- Modal -->
    <div class="flex min-h-full items-center justify-center p-4">
      <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 id="approval-modal-title" class="text-lg font-semibold text-gray-900">
              {#if selectedRequest.type === 'command_execution'}
                ⚠️ Command Execution Approval Required
              {:else}
                📝 File Changes Approval Required
              {/if}
            </h3>

            {#if $pendingApprovals.length > 1}
              <span class="text-sm text-gray-500">
                {$pendingApprovals.indexOf(selectedRequest) + 1} of {$pendingApprovals.length}
              </span>
            {/if}
          </div>
        </div>

        <!-- Content -->
        <div class="px-6 py-4 max-h-96 overflow-y-auto">
          {#if selectedRequest.type === 'command_execution'}
            <!-- Command Execution Details -->
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Command</label>
                <pre class="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">{selectedRequest.data.command}</pre>
              </div>

              {#if selectedRequest.data.cwd}
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Working Directory</label>
                  <code class="bg-gray-100 px-3 py-2 rounded text-sm block">{selectedRequest.data.cwd}</code>
                </div>
              {/if}

              {#if selectedRequest.data.reason}
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                  <p class="text-sm text-gray-600">{selectedRequest.data.reason}</p>
                </div>
              {/if}

              <!-- Warning -->
              <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div class="flex">
                  <svg class="h-5 w-5 text-yellow-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-yellow-800">Security Check</h3>
                    <div class="mt-2 text-sm text-yellow-700">
                      <p>Review this command carefully before approving. Malicious commands can harm your system.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          {:else}
            <!-- File Changes Details -->
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Files to be Modified</label>
                <ul class="space-y-2">
                  {#each selectedRequest.data.changes as change}
                    <li class="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                      {#if change.kind === 'add'}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          ADD
                        </span>
                      {:else if change.kind === 'delete'}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          DELETE
                        </span>
                      {:else}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          MODIFY
                        </span>
                      {/if}
                      <code class="text-sm">{change.path}</code>
                    </li>
                  {/each}
                </ul>
              </div>

              {#if selectedRequest.data.diff}
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Diff Preview</label>
                  <pre class="bg-gray-800 text-white p-3 rounded text-xs overflow-x-auto max-h-48 overflow-y-auto">{selectedRequest.data.diff}</pre>
                </div>
              {/if}

              <!-- Info -->
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex">
                  <svg class="h-5 w-5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                  </svg>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-blue-800">Review Changes</h3>
                    <div class="mt-2 text-sm text-blue-700">
                      <p>Code will apply these changes to your workspace. Review the diff carefully.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <div class="flex items-center justify-end space-x-3">
            <button
              on:click={() => handleDecision('rejected')}
              disabled={processing}
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Reject
            </button>

            <button
              on:click={() => handleDecision('approved')}
              disabled={processing}
              class="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {#if processing}
                <span class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Approving...
                </span>
              {:else}
                Approve & Execute
              {/if}
            </button>
          </div>

          {#if $pendingApprovals.length > 1}
            <div class="mt-3 text-center text-sm text-gray-500">
              {$pendingApprovals.length - 1} more approval{$pendingApprovals.length > 2 ? 's' : ''} pending
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Modal animations */
  .fixed {
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Scrollbar styling for diff preview */
  pre::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  pre::-webkit-scrollbar-track {
    background: #2d2d2d;
  }

  pre::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 3px;
  }

  pre::-webkit-scrollbar-thumb:hover {
    background: #777;
  }
</style>
