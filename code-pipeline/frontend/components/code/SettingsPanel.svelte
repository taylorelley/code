<script lang="ts">
  /**
   * SettingsPanel - Configuration UI for Code Pipeline
   *
   * Provides a comprehensive settings interface matching all Code TUI options:
   * - Model selection (Claude, GPT-4, Gemini)
   * - Reasoning effort level
   * - Enabled tools (Bash, Browser, MCP, Computer)
   * - MCP server configuration
   * - Auto Drive settings
   * - Browser configuration
   * - Terminal preferences
   */

  import { onMount } from 'svelte';
  import { writable, derived, type Writable } from 'svelte/store';

  // Settings interface
  export interface Settings {
    model: {
      provider: 'anthropic' | 'openai' | 'google';
      name: string;
      apiKey?: string;
      reasoningEffort: 'low' | 'medium' | 'high';
      maxTokens: number;
      temperature: number;
    };
    tools: {
      bash: boolean;
      browser: boolean;
      mcp: boolean;
      computer: boolean;
      webSearch: boolean;
    };
    mcpServers: Array<{
      id: string;
      name: string;
      command: string[];
      env?: Record<string, string>;
      enabled: boolean;
    }>;
    autoDrive: {
      enabled: boolean;
      maxSteps: number;
      requireApproval: boolean;
      maxParallelAgents: number;
    };
    browser: {
      headless: boolean;
      viewport: {
        width: number;
        height: number;
      };
      userAgent?: string;
    };
    terminal: {
      shell: string;
      fontSize: number;
      fontFamily: string;
      theme: 'dark' | 'light' | 'custom';
      cursorBlink: boolean;
      scrollback: number;
    };
    workspace: {
      path: string;
      gitEnabled: boolean;
      autoSave: boolean;
    };
  }

  // Props
  export let sessionId: string;
  export let onClose: () => void = () => {};

  // Settings store
  const settings: Writable<Settings> = writable({
    model: {
      provider: 'anthropic',
      name: 'claude-sonnet-4-20250514',
      reasoningEffort: 'medium',
      maxTokens: 8192,
      temperature: 0.7,
    },
    tools: {
      bash: true,
      browser: true,
      mcp: true,
      computer: false,
      webSearch: true,
    },
    mcpServers: [],
    autoDrive: {
      enabled: true,
      maxSteps: 10,
      requireApproval: true,
      maxParallelAgents: 3,
    },
    browser: {
      headless: true,
      viewport: {
        width: 1920,
        height: 1080,
      },
    },
    terminal: {
      shell: '/bin/bash',
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: 'dark',
      cursorBlink: true,
      scrollback: 1000,
    },
    workspace: {
      path: '',
      gitEnabled: true,
      autoSave: true,
    },
  });

  // Active tab
  let activeTab: 'model' | 'tools' | 'mcp' | 'autoDrive' | 'browser' | 'terminal' | 'workspace' =
    'model';

  // Model options
  const modelOptions = {
    anthropic: [
      { value: 'claude-sonnet-4-20250514', label: 'Claude 4 Sonnet (Latest)' },
      { value: 'claude-opus-4-20250514', label: 'Claude 4 Opus' },
      { value: 'claude-3-7-sonnet-20250219', label: 'Claude 3.7 Sonnet' },
      { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    ],
    openai: [
      { value: 'gpt-4-turbo-2024-04-09', label: 'GPT-4 Turbo' },
      { value: 'gpt-4-0125-preview', label: 'GPT-4' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    ],
    google: [
      { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (Experimental)' },
      { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
      { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    ],
  };

  // Derived model list
  $: availableModels = modelOptions[$settings.model.provider] || [];

  // Validate and update model name when provider changes
  $: if (availableModels.length > 0) {
    const currentModelExists = availableModels.some(
      (model) => model.value === $settings.model.name
    );
    if (!currentModelExists) {
      settings.update((s) => ({
        ...s,
        model: {
          ...s.model,
          name: availableModels[0].value,
        },
      }));
    }
  }

  // New MCP server form
  let newMCPServer = {
    name: '',
    command: '',
    env: '',
  };

  // Load settings on mount
  onMount(async () => {
    try {
      const response = await fetch(`/api/code/settings/${sessionId}`);
      if (response.ok) {
        const loadedSettings = await response.json();
        settings.set(loadedSettings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      showNotification('Failed to load settings — showing defaults', 'warning');
    }
  });

  // Save settings
  async function saveSettings() {
    try {
      const response = await fetch(`/api/code/settings/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify($settings),
      });

      if (response.ok) {
        showNotification('Settings saved successfully', 'success');
      } else {
        // Extract error details from server response
        let errorMessage = 'Failed to save settings';
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json();
            errorMessage = errorData.message || errorData.error || errorMessage;
          } else {
            const errorText = await response.text();
            if (errorText) {
              errorMessage = errorText.substring(0, 100); // Trim long messages
            }
          }
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }
        console.error('Save settings failed:', errorMessage);
        showNotification(errorMessage, 'error');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      const errorMessage = error.message
        ? `Failed to save settings: ${error.message}`
        : 'Failed to save settings';
      showNotification(errorMessage, 'error');
    }
  }

  // Add MCP server
  function addMCPServer() {
    if (!newMCPServer.name || !newMCPServer.command) {
      showNotification('Please fill in all fields', 'warning');
      return;
    }

    const server = {
      id: `mcp_${Date.now()}`,
      name: newMCPServer.name,
      command: newMCPServer.command.split(' ').filter((s) => s.length > 0),
      env: newMCPServer.env
        ? Object.fromEntries(
            newMCPServer.env
              .split('\n')
              .filter((line) => line.trim().length > 0)
              .map((line) => {
                const [key, ...value] = line.split('=');
                return [key.trim(), value.join('=').trim()];
              })
          )
        : {},
      enabled: true,
    };

    settings.update((s) => ({
      ...s,
      mcpServers: [...s.mcpServers, server],
    }));

    // Reset form
    newMCPServer = { name: '', command: '', env: '' };
  }

  // Remove MCP server
  function removeMCPServer(id: string) {
    settings.update((s) => ({
      ...s,
      mcpServers: s.mcpServers.filter((server) => server.id !== id),
    }));
  }

  // Toggle MCP server
  function toggleMCPServer(id: string) {
    settings.update((s) => ({
      ...s,
      mcpServers: s.mcpServers.map((server) =>
        server.id === id ? { ...server, enabled: !server.enabled } : server
      ),
    }));
  }

  // Show notification
  let notification = { show: false, message: '', type: 'info' };
  let notificationTimeoutId: number | null = null;

  function showNotification(message: string, type: 'success' | 'error' | 'warning' | 'info') {
    // Clear any pending timeout to prevent earlier timers from hiding this toast
    if (notificationTimeoutId !== null) {
      clearTimeout(notificationTimeoutId);
    }

    notification = { show: true, message, type };

    // Set new timeout and track its ID
    notificationTimeoutId = setTimeout(() => {
      notification = { ...notification, show: false };
      notificationTimeoutId = null;
    }, 3000);
  }

  // Reset to defaults
  function resetToDefaults() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      settings.set({
        model: {
          provider: 'anthropic',
          name: 'claude-sonnet-4-20250514',
          reasoningEffort: 'medium',
          maxTokens: 8192,
          temperature: 0.7,
        },
        tools: {
          bash: true,
          browser: true,
          mcp: true,
          computer: false,
          webSearch: true,
        },
        mcpServers: [],
        autoDrive: {
          enabled: true,
          maxSteps: 10,
          requireApproval: true,
          maxParallelAgents: 3,
        },
        browser: {
          headless: true,
          viewport: { width: 1920, height: 1080 },
        },
        terminal: {
          shell: '/bin/bash',
          fontSize: 14,
          fontFamily: 'Menlo, Monaco, "Courier New", monospace',
          theme: 'dark',
          cursorBlink: true,
          scrollback: 1000,
        },
        workspace: {
          path: '',
          gitEnabled: true,
          autoSave: true,
        },
      });
    }
  }
</script>

<div class="settings-panel" data-testid="settings-panel">
  <!-- Header -->
  <div class="panel-header">
    <h2>⚙️ Code Pipeline Settings</h2>
    <button class="btn-close" on:click={onClose} aria-label="Close settings">✕</button>
  </div>

  <!-- Tabs -->
  <div class="tabs" role="tablist">
    <button
      class="tab"
      class:active={activeTab === 'model'}
      on:click={() => (activeTab = 'model')}
      role="tab"
      aria-selected={activeTab === 'model'}
    >
      🤖 Model
    </button>
    <button
      class="tab"
      class:active={activeTab === 'tools'}
      on:click={() => (activeTab = 'tools')}
      role="tab"
      aria-selected={activeTab === 'tools'}
    >
      🔧 Tools
    </button>
    <button
      class="tab"
      class:active={activeTab === 'mcp'}
      on:click={() => (activeTab = 'mcp')}
      role="tab"
      aria-selected={activeTab === 'mcp'}
    >
      🔌 MCP Servers
    </button>
    <button
      class="tab"
      class:active={activeTab === 'autoDrive'}
      on:click={() => (activeTab = 'autoDrive')}
      role="tab"
      aria-selected={activeTab === 'autoDrive'}
    >
      🚗 Auto Drive
    </button>
    <button
      class="tab"
      class:active={activeTab === 'browser'}
      on:click={() => (activeTab = 'browser')}
      role="tab"
      aria-selected={activeTab === 'browser'}
    >
      🌐 Browser
    </button>
    <button
      class="tab"
      class:active={activeTab === 'terminal'}
      on:click={() => (activeTab = 'terminal')}
      role="tab"
      aria-selected={activeTab === 'terminal'}
    >
      ⚡ Terminal
    </button>
    <button
      class="tab"
      class:active={activeTab === 'workspace'}
      on:click={() => (activeTab = 'workspace')}
      role="tab"
      aria-selected={activeTab === 'workspace'}
    >
      📁 Workspace
    </button>
  </div>

  <!-- Content -->
  <div class="panel-content" role="tabpanel">
    {#if activeTab === 'model'}
      <div class="setting-group">
        <h3>Model Configuration</h3>

        <label>
          <span>Provider</span>
          <select bind:value={$settings.model.provider}>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="openai">OpenAI (GPT)</option>
            <option value="google">Google (Gemini)</option>
          </select>
        </label>

        <label>
          <span>Model</span>
          <select bind:value={$settings.model.name}>
            {#each availableModels as model}
              <option value={model.value}>{model.label}</option>
            {/each}
          </select>
        </label>

        <label>
          <span>Reasoning Effort</span>
          <div class="slider-container">
            <input
              type="range"
              min="0"
              max="2"
              step="1"
              value={$settings.model.reasoningEffort === 'low'
                ? 0
                : $settings.model.reasoningEffort === 'medium'
                  ? 1
                  : 2}
              on:input={(e) => {
                const val = parseInt(e.currentTarget.value);
                $settings.model.reasoningEffort = val === 0 ? 'low' : val === 1 ? 'medium' : 'high';
              }}
            />
            <span class="slider-label">{$settings.model.reasoningEffort}</span>
          </div>
          <p class="help-text">Higher effort = deeper thinking, slower responses</p>
        </label>

        <label>
          <span>Max Tokens</span>
          <input type="number" bind:value={$settings.model.maxTokens} min="1024" max="32768" step="1024" />
          <p class="help-text">Maximum length of model response</p>
        </label>

        <label>
          <span>Temperature</span>
          <input
            type="range"
            bind:value={$settings.model.temperature}
            min="0"
            max="1"
            step="0.1"
          />
          <span class="slider-label">{$settings.model.temperature.toFixed(1)}</span>
          <p class="help-text">Higher = more creative, lower = more focused</p>
        </label>
      </div>
    {:else if activeTab === 'tools'}
      <div class="setting-group">
        <h3>Enabled Tools</h3>
        <p class="help-text">Select which tools the AI can use</p>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.tools.bash} />
          <span>⚡ Bash - Execute shell commands</span>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.tools.browser} />
          <span>🌐 Browser - Web browsing and screenshots</span>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.tools.mcp} />
          <span>🔌 MCP - Model Context Protocol servers</span>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.tools.computer} />
          <span>🖥️ Computer Use - Desktop automation (experimental)</span>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.tools.webSearch} />
          <span>🔍 Web Search - Search the internet</span>
        </label>
      </div>
    {:else if activeTab === 'mcp'}
      <div class="setting-group">
        <h3>MCP Servers</h3>
        <p class="help-text">Configure Model Context Protocol servers</p>

        <!-- Existing MCP servers -->
        {#if $settings.mcpServers.length > 0}
          <div class="mcp-servers-list">
            {#each $settings.mcpServers as server (server.id)}
              <div class="mcp-server-card">
                <div class="server-header">
                  <label class="checkbox-label">
                    <input
                      type="checkbox"
                      checked={server.enabled}
                      on:change={() => toggleMCPServer(server.id)}
                    />
                    <span class="server-name">{server.name}</span>
                  </label>
                  <button
                    class="btn-remove"
                    on:click={() => removeMCPServer(server.id)}
                    aria-label="Remove {server.name}"
                  >
                    🗑️
                  </button>
                </div>
                <div class="server-details">
                  <code>{server.command.join(' ')}</code>
                  {#if server.env && Object.keys(server.env).length > 0}
                    <details>
                      <summary>Environment Variables</summary>
                      <pre>{Object.entries(server.env)
                          .map(([k, v]) => `${k}=${v}`)
                          .join('\n')}</pre>
                    </details>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="empty-state">No MCP servers configured</p>
        {/if}

        <!-- Add new MCP server -->
        <div class="add-mcp-server">
          <h4>Add MCP Server</h4>
          <label>
            <span>Name</span>
            <input
              type="text"
              bind:value={newMCPServer.name}
              placeholder="e.g., GitHub MCP"
            />
          </label>
          <label>
            <span>Command</span>
            <input
              type="text"
              bind:value={newMCPServer.command}
              placeholder="e.g., npx @modelcontextprotocol/server-github"
            />
          </label>
          <label>
            <span>Environment Variables (optional)</span>
            <textarea
              bind:value={newMCPServer.env}
              placeholder="KEY=value&#10;ANOTHER_KEY=another_value"
              rows="3"
            />
          </label>
          <button class="btn btn-primary" on:click={addMCPServer}>➕ Add Server</button>
        </div>
      </div>
    {:else if activeTab === 'autoDrive'}
      <div class="setting-group">
        <h3>Auto Drive Configuration</h3>
        <p class="help-text">Configure multi-agent autonomous coding</p>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.autoDrive.enabled} />
          <span>Enable Auto Drive</span>
        </label>

        <label>
          <span>Max Steps</span>
          <input
            type="number"
            bind:value={$settings.autoDrive.maxSteps}
            min="1"
            max="100"
          />
          <p class="help-text">Maximum number of autonomous steps</p>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.autoDrive.requireApproval} />
          <span>Require Approval for Commands</span>
        </label>

        <label>
          <span>Max Parallel Agents</span>
          <input
            type="number"
            bind:value={$settings.autoDrive.maxParallelAgents}
            min="1"
            max="10"
          />
          <p class="help-text">Number of agents that can run simultaneously</p>
        </label>
      </div>
    {:else if activeTab === 'browser'}
      <div class="setting-group">
        <h3>Browser Configuration</h3>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.browser.headless} />
          <span>Headless Mode</span>
          <p class="help-text">Run browser in the background (no UI)</p>
        </label>

        <label>
          <span>Viewport Width</span>
          <input
            type="number"
            bind:value={$settings.browser.viewport.width}
            min="320"
            max="3840"
          />
        </label>

        <label>
          <span>Viewport Height</span>
          <input
            type="number"
            bind:value={$settings.browser.viewport.height}
            min="240"
            max="2160"
          />
        </label>

        <label>
          <span>User Agent (optional)</span>
          <input
            type="text"
            bind:value={$settings.browser.userAgent}
            placeholder="Default browser user agent"
          />
        </label>
      </div>
    {:else if activeTab === 'terminal'}
      <div class="setting-group">
        <h3>Terminal Preferences</h3>

        <label>
          <span>Shell</span>
          <select bind:value={$settings.terminal.shell}>
            <option value="/bin/bash">Bash</option>
            <option value="/bin/zsh">Zsh</option>
            <option value="/bin/sh">Sh</option>
            <option value="/bin/fish">Fish</option>
          </select>
        </label>

        <label>
          <span>Font Size</span>
          <input
            type="range"
            bind:value={$settings.terminal.fontSize}
            min="10"
            max="24"
          />
          <span class="slider-label">{$settings.terminal.fontSize}px</span>
        </label>

        <label>
          <span>Font Family</span>
          <input type="text" bind:value={$settings.terminal.fontFamily} />
        </label>

        <label>
          <span>Theme</span>
          <select bind:value={$settings.terminal.theme}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="custom">Custom</option>
          </select>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.terminal.cursorBlink} />
          <span>Cursor Blink</span>
        </label>

        <label>
          <span>Scrollback Lines</span>
          <input
            type="number"
            bind:value={$settings.terminal.scrollback}
            min="100"
            max="10000"
          />
        </label>
      </div>
    {:else if activeTab === 'workspace'}
      <div class="setting-group">
        <h3>Workspace Settings</h3>

        <label>
          <span>Workspace Path</span>
          <input
            type="text"
            bind:value={$settings.workspace.path}
            placeholder="/path/to/workspace"
          />
          <p class="help-text">Default directory for Code operations</p>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.workspace.gitEnabled} />
          <span>Git Integration</span>
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={$settings.workspace.autoSave} />
          <span>Auto-save Files</span>
        </label>
      </div>
    {/if}
  </div>

  <!-- Footer -->
  <div class="panel-footer">
    <button class="btn" on:click={resetToDefaults}>Reset to Defaults</button>
    <div class="footer-actions">
      <button class="btn" on:click={onClose}>Cancel</button>
      <button class="btn btn-primary" on:click={saveSettings}>💾 Save Settings</button>
    </div>
  </div>

  <!-- Notification -->
  {#if notification.show}
    <div class="notification {notification.type}" role="alert">
      {notification.message}
    </div>
  {/if}
</div>

<style>
  .settings-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--code-bg-primary);
    color: var(--code-text-primary);
    border-radius: var(--code-radius-lg);
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
  }

  .panel-header h2 {
    margin: 0;
    font-size: var(--code-font-xl);
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

  .tabs {
    display: flex;
    gap: 0.5rem;
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-bottom: 1px solid var(--code-border);
    overflow-x: auto;
  }

  .tab {
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border: none;
    background: none;
    color: var(--code-text-secondary);
    cursor: pointer;
    border-radius: var(--code-radius-sm);
    white-space: nowrap;
    transition: all 0.2s;
  }

  .tab:hover {
    background-color: var(--code-bg-hover);
    color: var(--code-text-primary);
  }

  .tab.active {
    background-color: var(--code-accent);
    color: white;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--code-spacing-lg);
  }

  .setting-group {
    display: flex;
    flex-direction: column;
    gap: var(--code-spacing-md);
  }

  .setting-group h3 {
    margin: 0 0 var(--code-spacing-sm) 0;
    font-size: var(--code-font-lg);
    color: var(--code-text-primary);
  }

  .setting-group h4 {
    margin: var(--code-spacing-md) 0 var(--code-spacing-sm) 0;
    font-size: var(--code-font-base);
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  label > span:first-child {
    font-weight: 500;
    color: var(--code-text-primary);
  }

  input[type='text'],
  input[type='number'],
  select,
  textarea {
    padding: var(--code-spacing-sm);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    background-color: var(--code-bg-secondary);
    color: var(--code-text-primary);
    font-size: var(--code-font-base);
  }

  input[type='range'] {
    width: 100%;
  }

  .slider-container {
    display: flex;
    align-items: center;
    gap: var(--code-spacing-sm);
  }

  .slider-label {
    min-width: 4rem;
    text-align: center;
    font-weight: 500;
  }

  .checkbox-label {
    flex-direction: row;
    align-items: center;
    gap: var(--code-spacing-sm);
    cursor: pointer;
  }

  .checkbox-label input[type='checkbox'] {
    width: 1.25rem;
    height: 1.25rem;
  }

  .help-text {
    font-size: var(--code-font-sm);
    color: var(--code-text-muted);
    margin: 0.25rem 0 0 0;
  }

  .mcp-servers-list {
    display: flex;
    flex-direction: column;
    gap: var(--code-spacing-sm);
  }

  .mcp-server-card {
    padding: var(--code-spacing-md);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-md);
    background-color: var(--code-bg-secondary);
  }

  .server-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .server-name {
    font-weight: 500;
  }

  .btn-remove {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.25rem;
    padding: 0.25rem;
  }

  .server-details {
    margin-top: var(--code-spacing-sm);
  }

  .server-details code {
    display: block;
    padding: var(--code-spacing-sm);
    background-color: var(--code-bg-tertiary);
    border-radius: var(--code-radius-sm);
    font-size: var(--code-font-sm);
  }

  .add-mcp-server {
    margin-top: var(--code-spacing-lg);
    padding: var(--code-spacing-md);
    border: 1px dashed var(--code-border);
    border-radius: var(--code-radius-md);
  }

  .empty-state {
    text-align: center;
    color: var(--code-text-muted);
    padding: var(--code-spacing-lg);
  }

  .panel-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--code-spacing-md);
    border-top: 1px solid var(--code-border);
  }

  .footer-actions {
    display: flex;
    gap: var(--code-spacing-sm);
  }

  .notification {
    position: fixed;
    bottom: var(--code-spacing-lg);
    right: var(--code-spacing-lg);
    padding: var(--code-spacing-md);
    border-radius: var(--code-radius-md);
    box-shadow: 0 4px 6px var(--code-shadow);
    animation: code-fade-in 0.3s ease;
    z-index: 1000;
  }

  .notification.success {
    background-color: var(--code-success);
    color: white;
  }

  .notification.error {
    background-color: var(--code-error);
    color: white;
  }

  .notification.warning {
    background-color: var(--code-warning);
    color: white;
  }

  .notification.info {
    background-color: var(--code-info);
    color: white;
  }

  @media (max-width: 768px) {
    .tabs {
      flex-wrap: wrap;
    }

    .panel-footer {
      flex-direction: column;
      gap: var(--code-spacing-sm);
    }

    .footer-actions {
      width: 100%;
      justify-content: space-between;
    }
  }
</style>
