/**
 * End-to-End Tests for Code Pipeline
 *
 * Tests the full integration of Code Pipeline components in Open WebUI
 * using Playwright for browser automation.
 */

import { test, expect, type Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const WS_URL = process.env.WS_URL || 'ws://localhost:9099';

test.describe('Code Pipeline E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto(BASE_URL);

    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test.describe('WebSocket Connection', () => {
    test('should connect to WebSocket successfully', async ({ page }) => {
      // Wait for connection status indicator
      const connectionStatus = await page.waitForSelector('[data-testid="connection-status"]');
      const isConnected = await connectionStatus.getAttribute('data-connected');

      expect(isConnected).toBe('true');
    });

    test('should auto-reconnect on disconnect', async ({ page }) => {
      // Wait for connection
      await page.waitForSelector('[data-testid="connection-status"][data-connected="true"]');

      // Simulate disconnect (this would need backend support)
      // For now, just verify reconnection logic exists
      const reconnectBtn = page.locator('[data-testid="reconnect-button"]');
      if (await reconnectBtn.isVisible()) {
        await reconnectBtn.click();
        await page.waitForSelector('[data-testid="connection-status"][data-connected="true"]');
      }
    });
  });

  test.describe('Activity Cards', () => {
    test('should display tool execution cards', async ({ page }) => {
      // Send a bash command
      await page.fill('[data-testid="chat-input"]', '/bash echo "Hello World"');
      await page.click('[data-testid="send-button"]');

      // Wait for activity card to appear
      const toolCard = await page.waitForSelector('[data-testid="tool-card-bash"]');
      expect(await toolCard.isVisible()).toBe(true);

      // Verify card content
      const cardText = await toolCard.textContent();
      expect(cardText).toContain('echo "Hello World"');
    });

    test('should show tool status updates', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/bash sleep 2');
      await page.click('[data-testid="send-button"]');

      // Wait for card
      const toolCard = await page.waitForSelector('[data-testid="tool-card-bash"]');

      // Initially should be running
      const runningStatus = await toolCard.locator('[data-status="running"]');
      expect(await runningStatus.isVisible()).toBe(true);

      // Wait for completion
      await page.waitForSelector('[data-testid="tool-card-bash"] [data-status="completed"]', {
        timeout: 5000,
      });
    });

    test('should expand/collapse cards', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/bash ls -la');
      await page.click('[data-testid="send-button"]');

      const toolCard = await page.waitForSelector('[data-testid="tool-card-bash"]');

      // Click to expand
      await toolCard.click();

      // Verify details are visible
      const details = toolCard.locator('[data-testid="tool-details"]');
      expect(await details.isVisible()).toBe(true);

      // Click to collapse
      await toolCard.click();
      await page.waitForTimeout(300); // Wait for animation

      expect(await details.isVisible()).toBe(false);
    });
  });

  test.describe('Terminal Panel', () => {
    test('should render terminal emulator', async ({ page }) => {
      // Open terminal tab
      await page.click('[data-testid="terminal-tab"]');

      // Wait for xterm to load
      const terminal = await page.waitForSelector('.xterm');
      expect(await terminal.isVisible()).toBe(true);

      // Verify terminal has content
      const terminalScreen = page.locator('.xterm-screen');
      expect(await terminalScreen.isVisible()).toBe(true);
    });

    test('should accept input and display output', async ({ page }) => {
      await page.click('[data-testid="terminal-tab"]');

      const terminal = await page.waitForSelector('.xterm');

      // Type command
      await page.keyboard.type('echo test');
      await page.keyboard.press('Enter');

      // Wait for output
      await page.waitForTimeout(500);

      const terminalContent = await page.locator('.xterm-screen').textContent();
      expect(terminalContent).toContain('test');
    });

    test('should support ANSI colors', async ({ page }) => {
      await page.click('[data-testid="terminal-tab"]');

      // Run command with ANSI colors
      await page.keyboard.type('echo -e "\\033[32mGreen text\\033[0m"');
      await page.keyboard.press('Enter');

      await page.waitForTimeout(500);

      // Verify colored output exists (check for ANSI styling)
      const coloredSpan = page.locator('.xterm-screen span[style*="color"]');
      expect(await coloredSpan.count()).toBeGreaterThan(0);
    });
  });

  test.describe('Browser Panel', () => {
    test('should display screenshots', async ({ page }) => {
      // Send browser command
      await page.fill('[data-testid="chat-input"]', '/browser https://example.com');
      await page.click('[data-testid="send-button"]');

      // Wait for screenshot to appear
      const screenshot = await page.waitForSelector('[data-testid="browser-screenshot"]', {
        timeout: 10000,
      });

      expect(await screenshot.isVisible()).toBe(true);

      // Verify image loaded
      const img = screenshot.locator('img');
      expect(await img.getAttribute('src')).toContain('data:image/');
    });

    test('should show screenshot metadata', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/browser https://example.com');
      await page.click('[data-testid="send-button"]');

      const panel = await page.waitForSelector('[data-testid="browser-panel"]');

      // Check for URL display
      const url = panel.locator('[data-testid="screenshot-url"]');
      expect(await url.textContent()).toContain('example.com');

      // Check for title
      const title = panel.locator('[data-testid="screenshot-title"]');
      expect(await title.isVisible()).toBe(true);
    });

    test('should allow screenshot history navigation', async ({ page }) => {
      // Take multiple screenshots
      for (let i = 0; i < 3; i++) {
        await page.fill('[data-testid="chat-input"]', `/browser https://example.com/${i}`);
        await page.click('[data-testid="send-button"]');
        await page.waitForTimeout(2000);
      }

      // Open history sidebar
      await page.click('[data-testid="screenshot-history-toggle"]');

      // Verify history items
      const historyItems = page.locator('[data-testid="screenshot-history-item"]');
      expect(await historyItems.count()).toBe(3);

      // Click on first item
      await historyItems.first().click();

      // Verify correct screenshot is displayed
      const activeUrl = await page.locator('[data-testid="screenshot-url"]').textContent();
      expect(activeUrl).toContain('/0');
    });
  });

  test.describe('Approval Flow', () => {
    test('should show approval modal for dangerous commands', async ({ page }) => {
      // Send dangerous command
      await page.fill('[data-testid="chat-input"]', '/bash rm -rf /tmp/test');
      await page.click('[data-testid="send-button"]');

      // Wait for approval modal
      const modal = await page.waitForSelector('[data-testid="approval-modal"]');
      expect(await modal.isVisible()).toBe(true);

      // Verify command is shown
      const commandPreview = modal.locator('[data-testid="approval-command"]');
      expect(await commandPreview.textContent()).toContain('rm -rf');
    });

    test('should execute command on approval', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/bash rm -rf /tmp/test');
      await page.click('[data-testid="send-button"]');

      const modal = await page.waitForSelector('[data-testid="approval-modal"]');

      // Click approve
      await modal.locator('[data-testid="approve-button"]').click();

      // Modal should close
      await page.waitForSelector('[data-testid="approval-modal"]', { state: 'hidden' });

      // Command should execute
      const toolCard = await page.waitForSelector('[data-testid="tool-card-bash"]');
      expect(await toolCard.isVisible()).toBe(true);
    });

    test('should cancel command on rejection', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/bash rm -rf /tmp/test');
      await page.click('[data-testid="send-button"]');

      const modal = await page.waitForSelector('[data-testid="approval-modal"]');

      // Click reject
      await modal.locator('[data-testid="reject-button"]').click();

      // Modal should close
      await page.waitForSelector('[data-testid="approval-modal"]', { state: 'hidden' });

      // No tool card should appear
      const toolCard = page.locator('[data-testid="tool-card-bash"]');
      expect(await toolCard.count()).toBe(0);
    });
  });

  test.describe('Auto Drive Panel', () => {
    test('should display auto drive status', async ({ page }) => {
      // Send auto drive command
      await page.fill('[data-testid="chat-input"]', '/auto Implement user authentication');
      await page.click('[data-testid="send-button"]');

      // Wait for auto drive panel
      const panel = await page.waitForSelector('[data-testid="auto-drive-panel"]');
      expect(await panel.isVisible()).toBe(true);

      // Verify status display
      const status = panel.locator('[data-testid="auto-drive-status"]');
      expect(await status.textContent()).toMatch(/thinking|acting|reviewing/i);
    });

    test('should show progress bar', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/auto Create a simple web server');
      await page.click('[data-testid="send-button"]');

      const panel = await page.waitForSelector('[data-testid="auto-drive-panel"]');

      // Verify progress bar exists
      const progressBar = panel.locator('[data-testid="auto-drive-progress"]');
      expect(await progressBar.isVisible()).toBe(true);

      // Progress should be between 0 and 100
      const progress = await progressBar.getAttribute('aria-valuenow');
      const progressValue = parseInt(progress || '0');
      expect(progressValue).toBeGreaterThanOrEqual(0);
      expect(progressValue).toBeLessThanOrEqual(100);
    });

    test('should display decision transcript', async ({ page }) => {
      await page.fill('[data-testid="chat-input"]', '/auto Fix all type errors');
      await page.click('[data-testid="send-button"]');

      const panel = await page.waitForSelector('[data-testid="auto-drive-panel"]');

      // Wait for transcript entries
      await page.waitForTimeout(2000);

      const transcript = panel.locator('[data-testid="auto-drive-transcript"]');
      const entries = transcript.locator('[data-testid="transcript-entry"]');

      expect(await entries.count()).toBeGreaterThan(0);
    });
  });

  test.describe('Settings Panel', () => {
    test('should open settings panel', async ({ page }) => {
      // Click settings button
      await page.click('[data-testid="settings-button"]');

      // Wait for panel
      const panel = await page.waitForSelector('[data-testid="settings-panel"]');
      expect(await panel.isVisible()).toBe(true);
    });

    test('should save model settings', async ({ page }) => {
      await page.click('[data-testid="settings-button"]');

      const panel = await page.waitForSelector('[data-testid="settings-panel"]');

      // Click model tab
      await panel.locator('button:has-text("Model")').click();

      // Change provider
      await panel.locator('select[name="provider"]').selectOption('openai');

      // Save
      await panel.locator('[data-testid="save-settings-button"]').click();

      // Verify success notification
      const notification = await page.waitForSelector('.notification.success');
      expect(await notification.textContent()).toContain('saved');
    });

    test('should toggle tool settings', async ({ page }) => {
      await page.click('[data-testid="settings-button"]');

      const panel = await page.waitForSelector('[data-testid="settings-panel"]');

      // Click tools tab
      await panel.locator('button:has-text("Tools")').click();

      // Toggle bash
      const bashCheckbox = panel.locator('input[type="checkbox"][name="bash"]');
      const wasChecked = await bashCheckbox.isChecked();

      await bashCheckbox.click();

      // Verify toggled
      expect(await bashCheckbox.isChecked()).toBe(!wasChecked);

      // Save
      await panel.locator('[data-testid="save-settings-button"]').click();

      // Close and reopen to verify persistence
      await panel.locator('[data-testid="close-settings-button"]').click();
      await page.click('[data-testid="settings-button"]');

      const newPanel = await page.waitForSelector('[data-testid="settings-panel"]');
      await newPanel.locator('button:has-text("Tools")').click();

      const newBashCheckbox = newPanel.locator('input[type="checkbox"][name="bash"]');
      expect(await newBashCheckbox.isChecked()).toBe(!wasChecked);
    });
  });

  test.describe('File Tree', () => {
    test('should display project files', async ({ page }) => {
      // Open file tree
      await page.click('[data-testid="file-tree-tab"]');

      // Wait for tree
      const tree = await page.waitForSelector('[data-testid="file-tree"]');
      expect(await tree.isVisible()).toBe(true);

      // Verify files are shown
      const files = tree.locator('[role="treeitem"]');
      expect(await files.count()).toBeGreaterThan(0);
    });

    test('should expand/collapse directories', async ({ page }) => {
      await page.click('[data-testid="file-tree-tab"]');

      const tree = await page.waitForSelector('[data-testid="file-tree"]');

      // Find a directory
      const dir = tree.locator('[role="treeitem"][aria-expanded="false"]').first();

      // Expand
      await dir.click();

      // Verify expanded
      expect(await dir.getAttribute('aria-expanded')).toBe('true');

      // Collapse
      await dir.click();

      expect(await dir.getAttribute('aria-expanded')).toBe('false');
    });

    test('should search files', async ({ page }) => {
      await page.click('[data-testid="file-tree-tab"]');

      const tree = await page.waitForSelector('[data-testid="file-tree"]');

      // Type in search
      await tree.locator('input[type="text"]').fill('test');

      await page.waitForTimeout(300); // Debounce

      // Verify filtered results
      const visibleFiles = tree.locator('[role="treeitem"]:visible');
      const count = await visibleFiles.count();

      expect(count).toBeGreaterThan(0);

      // All visible files should match search
      for (let i = 0; i < count; i++) {
        const text = await visibleFiles.nth(i).textContent();
        expect(text?.toLowerCase()).toContain('test');
      }
    });
  });

  test.describe('Multi-File Diff', () => {
    test('should display file diffs', async ({ page }) => {
      // Make some changes first (this assumes a setup)
      await page.click('[data-testid="diff-view-tab"]');

      const diffView = await page.waitForSelector('[data-testid="multi-file-diff"]');

      // Verify diff tabs exist
      const tabs = diffView.locator('.diff-tabs .tab');
      const tabCount = await tabs.count();

      if (tabCount > 0) {
        // Verify first file is displayed
        expect(await diffView.locator('.diff-view').isVisible()).toBe(true);
      }
    });

    test('should switch between split and unified view', async ({ page }) => {
      await page.click('[data-testid="diff-view-tab"]');

      const diffView = await page.waitForSelector('[data-testid="multi-file-diff"]');

      // Click unified view
      await diffView.locator('button:has-text("Unified")').click();

      // Verify unified container
      expect(await diffView.locator('.unified-container').isVisible()).toBe(true);

      // Click split view
      await diffView.locator('button:has-text("Split")').click();

      // Verify split container
      expect(await diffView.locator('.split-container').isVisible()).toBe(true);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should support Ctrl+Z for undo', async ({ page }) => {
      // Get the input element
      const input = page.locator('[data-testid="chat-input"]');

      // Set initial value and record it
      const originalValue = 'Hello';
      await input.fill(originalValue);

      // Verify original value is set
      expect(await input.inputValue()).toBe(originalValue);

      // Modify the input (append text)
      await input.fill(originalValue + ' World');

      // Verify modified value
      expect(await input.inputValue()).toBe('Hello World');

      // Ensure input has focus
      await input.focus();

      // Press Ctrl+Z to undo
      await page.keyboard.press('Control+Z');

      // Wait for any DOM update
      await page.waitForTimeout(100);

      // Assert the input value reverted to original
      expect(await input.inputValue()).toBe(originalValue);
    });

    test('should support arrow key navigation in file tree', async ({ page }) => {
      await page.click('[data-testid="file-tree-tab"]');

      const tree = await page.waitForSelector('[data-testid="file-tree"]');

      // Focus tree
      await tree.click();

      // Press down arrow
      await page.keyboard.press('ArrowDown');

      // Verify focused element changed
      const focused = await page.locator(':focus');
      expect(await focused.getAttribute('role')).toBe('treeitem');
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      // Check main regions
      const chatRegion = page.locator('[role="region"][aria-label*="chat"]');
      expect(await chatRegion.count()).toBeGreaterThan(0);

      // Check buttons have labels
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i);
        const label = await button.getAttribute('aria-label');
        const text = await button.textContent();

        // Button should have either aria-label or text content
        expect(label || text).toBeTruthy();
      }
    });

    test('should be keyboard navigable', async ({ page }) => {
      // Tab through interactive elements
      await page.keyboard.press('Tab');

      // Verify focus is visible
      const focused = await page.locator(':focus');
      expect(await focused.count()).toBe(1);

      // Continue tabbing
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');

        const newFocused = await page.locator(':focus');
        expect(await newFocused.count()).toBe(1);
      }
    });

    test('should have sufficient color contrast', async ({ page }) => {
      // This would use a11y testing library
      // For now, just verify contrast CSS vars are set
      const root = page.locator('.code-theme-root');

      const bgColor = await root.evaluate((el) =>
        getComputedStyle(el).getPropertyValue('--code-bg-primary')
      );

      const textColor = await root.evaluate((el) =>
        getComputedStyle(el).getPropertyValue('--code-text-primary')
      );

      expect(bgColor).toBeTruthy();
      expect(textColor).toBeTruthy();
    });
  });

  test.describe('Performance', () => {
    test('should load within acceptable time', async ({ page }) => {
      const startTime = Date.now();

      await page.goto(BASE_URL);
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;

      // Should load in under 3 seconds
      expect(loadTime).toBeLessThan(3000);
    });

    test('should handle large terminal output efficiently', async ({ page }) => {
      await page.click('[data-testid="terminal-tab"]');

      // Generate large output
      await page.keyboard.type('for i in {1..1000}; do echo "Line $i"; done');
      await page.keyboard.press('Enter');

      // Wait for output
      await page.waitForTimeout(2000);

      // Verify terminal is still responsive
      await page.keyboard.type('echo "done"');
      await page.keyboard.press('Enter');

      await page.waitForTimeout(500);

      const content = await page.locator('.xterm-screen').textContent();
      expect(content).toContain('done');
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto(BASE_URL);

      // Verify mobile nav is visible
      const mobileNav = page.locator('[data-testid="mobile-nav"]');
      expect(await mobileNav.isVisible()).toBe(true);

      // Verify components stack vertically
      const activityCards = page.locator('[data-testid="activity-cards"]');
      const width = await activityCards.boundingBox();

      expect(width?.width).toBeLessThan(400);
    });

    test('should support touch interactions', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      // Tap on a card
      await page.fill('[data-testid="chat-input"]', '/bash ls');
      await page.click('[data-testid="send-button"]');

      const toolCard = await page.waitForSelector('[data-testid="tool-card-bash"]');

      // Simulate touch tap
      await toolCard.tap();

      // Verify card expanded
      const details = toolCard.locator('[data-testid="tool-details"]');
      expect(await details.isVisible()).toBe(true);
    });
  });
});
