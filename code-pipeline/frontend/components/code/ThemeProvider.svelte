<script lang="ts">
  /**
   * ThemeProvider - Integrates Code Pipeline components with Open WebUI theme system
   *
   * This component wraps all Code components and provides theme context through CSS variables.
   * It automatically adapts to Open WebUI's theme changes (dark/light mode, custom colors).
   *
   * Usage:
   *   <ThemeProvider>
   *     <ActivityCards />
   *     <TerminalPanel />
   *     <!-- other Code components -->
   *   </ThemeProvider>
   */

  import { getContext, onMount } from 'svelte';
  import { writable, type Writable } from 'svelte/store';

  // Theme interface matching Open WebUI theme structure
  interface Theme {
    mode: 'light' | 'dark';
    colors: {
      bg: {
        primary: string;
        secondary: string;
        tertiary: string;
      };
      text: {
        primary: string;
        secondary: string;
        muted: string;
      };
      accent: string;
      border: string;
      error: string;
      warning: string;
      success: string;
      info: string;
    };
    spacing: {
      sm: string;
      md: string;
      lg: string;
    };
    borderRadius: {
      sm: string;
      md: string;
      lg: string;
    };
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
    };
  }

  // Props
  export let customTheme: Partial<Theme> | null = null;
  export let className = '';

  // Try to get Open WebUI theme from context (if available)
  let openWebUITheme: Theme | null = null;
  try {
    openWebUITheme = getContext('theme');
  } catch (e) {
    // No theme context available, will use defaults
  }

  // Default theme (used as fallback)
  const defaultTheme: Theme = {
    mode: 'dark',
    colors: {
      bg: {
        primary: '#1e1e1e',
        secondary: '#2d2d2d',
        tertiary: '#3c3c3c',
      },
      text: {
        primary: '#e0e0e0',
        secondary: '#b0b0b0',
        muted: '#808080',
      },
      accent: '#007acc',
      border: '#404040',
      error: '#f44336',
      warning: '#ff9800',
      success: '#4caf50',
      info: '#2196f3',
    },
    spacing: {
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
    },
    borderRadius: {
      sm: '0.25rem',
      md: '0.5rem',
      lg: '0.75rem',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
    },
  };

  // Merge themes: custom > OpenWebUI > default
  $: activeTheme = {
    ...defaultTheme,
    ...(openWebUITheme || {}),
    ...(customTheme || {}),
  };

  // Generate CSS variables from active theme
  $: cssVars = {
    // Background colors
    '--code-bg-primary': activeTheme.colors.bg.primary,
    '--code-bg-secondary': activeTheme.colors.bg.secondary,
    '--code-bg-tertiary': activeTheme.colors.bg.tertiary,

    // Text colors
    '--code-text-primary': activeTheme.colors.text.primary,
    '--code-text-secondary': activeTheme.colors.text.secondary,
    '--code-text-muted': activeTheme.colors.text.muted,

    // Status colors
    '--code-accent': activeTheme.colors.accent,
    '--code-border': activeTheme.colors.border,
    '--code-error': activeTheme.colors.error,
    '--code-warning': activeTheme.colors.warning,
    '--code-success': activeTheme.colors.success,
    '--code-info': activeTheme.colors.info,

    // Spacing
    '--code-spacing-sm': activeTheme.spacing.sm,
    '--code-spacing-md': activeTheme.spacing.md,
    '--code-spacing-lg': activeTheme.spacing.lg,

    // Border radius
    '--code-radius-sm': activeTheme.borderRadius.sm,
    '--code-radius-md': activeTheme.borderRadius.md,
    '--code-radius-lg': activeTheme.borderRadius.lg,

    // Font sizes
    '--code-font-xs': activeTheme.fontSize.xs,
    '--code-font-sm': activeTheme.fontSize.sm,
    '--code-font-base': activeTheme.fontSize.base,
    '--code-font-lg': activeTheme.fontSize.lg,
    '--code-font-xl': activeTheme.fontSize.xl,

    // Derived colors (with opacity)
    '--code-bg-hover': `${activeTheme.colors.bg.secondary}cc`,
    '--code-bg-active': `${activeTheme.colors.bg.tertiary}dd`,
    '--code-shadow': activeTheme.mode === 'dark' ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.15)',

    // Terminal specific colors
    '--code-terminal-bg': activeTheme.mode === 'dark' ? '#1e1e1e' : '#ffffff',
    '--code-terminal-fg': activeTheme.mode === 'dark' ? '#d4d4d4' : '#333333',
    '--code-terminal-cursor': activeTheme.colors.accent,
    '--code-terminal-selection': activeTheme.mode === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',

    // Code syntax highlighting colors
    '--code-syntax-keyword': activeTheme.mode === 'dark' ? '#569cd6' : '#0000ff',
    '--code-syntax-string': activeTheme.mode === 'dark' ? '#ce9178' : '#a31515',
    '--code-syntax-comment': activeTheme.mode === 'dark' ? '#6a9955' : '#008000',
    '--code-syntax-function': activeTheme.mode === 'dark' ? '#dcdcaa' : '#795e26',
    '--code-syntax-variable': activeTheme.mode === 'dark' ? '#9cdcfe' : '#001080',

    // Diff colors
    '--code-diff-add-bg': activeTheme.mode === 'dark' ? 'rgba(0, 255, 0, 0.15)' : 'rgba(0, 255, 0, 0.1)',
    '--code-diff-remove-bg': activeTheme.mode === 'dark' ? 'rgba(255, 0, 0, 0.15)' : 'rgba(255, 0, 0, 0.1)',
    '--code-diff-add-border': activeTheme.mode === 'dark' ? '#00ff0066' : '#00ff0044',
    '--code-diff-remove-border': activeTheme.mode === 'dark' ? '#ff000066' : '#ff000044',
  };

  // Convert CSS vars object to style string
  $: styleString = Object.entries(cssVars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');

  // Detect system theme changes
  let prefersDark = false;
  onMount(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    prefersDark = mediaQuery.matches;

    const handler = (e: MediaQueryListEvent) => {
      prefersDark = e.matches;
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  });

  // Auto-detect mode if not explicitly set
  $: if (!customTheme?.mode && !openWebUITheme?.mode) {
    activeTheme.mode = prefersDark ? 'dark' : 'light';
  }
</script>

<div
  class="code-theme-root {className}"
  class:dark={activeTheme.mode === 'dark'}
  class:light={activeTheme.mode === 'light'}
  style={styleString}
  data-theme={activeTheme.mode}
>
  <slot />
</div>

<style>
  .code-theme-root {
    /* Base styles */
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu',
      'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: var(--code-text-primary);
    background-color: var(--code-bg-primary);
  }

  /* Global styles for Code components */
  .code-theme-root :global(*) {
    box-sizing: border-box;
  }

  /* Scrollbar styling */
  .code-theme-root :global(::-webkit-scrollbar) {
    width: 12px;
    height: 12px;
  }

  .code-theme-root :global(::-webkit-scrollbar-track) {
    background: var(--code-bg-secondary);
    border-radius: var(--code-radius-sm);
  }

  .code-theme-root :global(::-webkit-scrollbar-thumb) {
    background: var(--code-border);
    border-radius: var(--code-radius-sm);
  }

  .code-theme-root :global(::-webkit-scrollbar-thumb:hover) {
    background: var(--code-text-muted);
  }

  /* Focus visible styles for accessibility */
  .code-theme-root :global(:focus-visible) {
    outline: 2px solid var(--code-accent);
    outline-offset: 2px;
  }

  /* Selection color */
  .code-theme-root :global(::selection) {
    background-color: var(--code-accent);
    color: var(--code-bg-primary);
  }

  /* Links */
  .code-theme-root :global(a) {
    color: var(--code-accent);
    text-decoration: none;
  }

  .code-theme-root :global(a:hover) {
    text-decoration: underline;
  }

  /* Code blocks */
  .code-theme-root :global(pre),
  .code-theme-root :global(code) {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: var(--code-font-sm);
  }

  .code-theme-root :global(pre) {
    background-color: var(--code-bg-secondary);
    padding: var(--code-spacing-md);
    border-radius: var(--code-radius-md);
    overflow-x: auto;
  }

  /* Buttons */
  .code-theme-root :global(.btn) {
    padding: var(--code-spacing-sm) var(--code-spacing-md);
    border-radius: var(--code-radius-md);
    font-size: var(--code-font-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid var(--code-border);
    background-color: var(--code-bg-secondary);
    color: var(--code-text-primary);
  }

  .code-theme-root :global(.btn:hover) {
    background-color: var(--code-bg-hover);
  }

  .code-theme-root :global(.btn:active) {
    background-color: var(--code-bg-active);
  }

  .code-theme-root :global(.btn-primary) {
    background-color: var(--code-accent);
    color: white;
    border-color: var(--code-accent);
  }

  .code-theme-root :global(.btn-primary:hover) {
    opacity: 0.9;
  }

  .code-theme-root :global(.btn-danger) {
    background-color: var(--code-error);
    color: white;
    border-color: var(--code-error);
  }

  .code-theme-root :global(.btn-success) {
    background-color: var(--code-success);
    color: white;
    border-color: var(--code-success);
  }

  /* Cards */
  .code-theme-root :global(.card) {
    background-color: var(--code-bg-secondary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-md);
    padding: var(--code-spacing-md);
  }

  /* Inputs */
  .code-theme-root :global(input),
  .code-theme-root :global(textarea),
  .code-theme-root :global(select) {
    background-color: var(--code-bg-secondary);
    border: 1px solid var(--code-border);
    border-radius: var(--code-radius-sm);
    padding: var(--code-spacing-sm);
    color: var(--code-text-primary);
    font-size: var(--code-font-base);
  }

  .code-theme-root :global(input:focus),
  .code-theme-root :global(textarea:focus),
  .code-theme-root :global(select:focus) {
    border-color: var(--code-accent);
    outline: none;
  }

  /* Animations */
  @keyframes :global(code-fade-in) {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes :global(code-spin) {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes :global(code-pulse) {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Utility classes */
  .code-theme-root :global(.fade-in) {
    animation: code-fade-in 0.3s ease;
  }

  .code-theme-root :global(.spinning) {
    animation: code-spin 1s linear infinite;
  }

  .code-theme-root :global(.pulsing) {
    animation: code-pulse 2s ease-in-out infinite;
  }
</style>
