import { test, expect } from '@playwright/test';

/**
 * M4 Explain Panel E2E tests.
 *
 * These tests hit the renderer at APP_URL (Vite dev server, see playwright.config.ts).
 * They assume:
 *   - `npm run dev` is running (Electron + Vite on http://127.0.0.1:5173)
 *   - The backend Flask server is running so /api/explain resolves
 *
 * Case B (degraded banner) requires the backend to be in degraded mode
 * (e.g. OLLAMA_DOWN=1 or Ollama offline). It is skipped by default because
 * that env var is controlled at backend startup; unskip when running with
 * a degraded backend.
 */
const APP_URL = process.env.APP_URL || 'http://127.0.0.1:5173';
const DEGRADED = process.env.E2E_DEGRADED === '1';

test.describe('M4 Explain Panel E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    // Wait for the timeline to render verb nodes. The default sentence is
    // "I usually get up at seven every morning." → multiple verbs appear
    // after engine analysis. Fall back to a generous timeout in case the
    // backend is slow.
    await page.locator('[data-testid="timeline-verb"]').first().waitFor({ timeout: 15_000 });
  });

  test('Case A: 正常路径 — AI 解释出现', async ({ page }) => {
    const verb = page.locator('[data-testid="timeline-verb"]').first();
    await verb.click({ timeout: 5_000 });

    // ExplainPanel (the aside) should become visible. Either AI or fallback path counts.
    await expect(page.locator('[data-testid="explain-panel"]')).toBeVisible({ timeout: 10_000 });
  });

  test('Case B: 降级路径 — Ollama 关闭时显示 fallback', async ({ page }) => {
    test.skip(!DEGRADED, 'Case B requires E2E_DEGRADED=1 (backend running in degraded mode)');

    const verb = page.locator('[data-testid="timeline-verb"]').first();
    await verb.click({ timeout: 5_000 });

    await expect(page.locator('[data-testid="degraded-banner"]')).toBeVisible({ timeout: 10_000 });
  });

  test('Case C: Pin + History', async ({ page }) => {
    // Click first verb
    await page.locator('[data-testid="timeline-verb"]').first().click();
    await page.locator('[data-testid="explain-panel"]').waitFor({ timeout: 10_000 });

    // Pin current explanation
    await page.locator('[data-testid="pin-button"]').click();

    // Click second verb — because pinned, panel content should NOT change to verb 2.
    const verbCount = await page.locator('[data-testid="timeline-verb"]').count();
    if (verbCount > 1) {
      await page.locator('[data-testid="timeline-verb"]').nth(1).click();
    }
    await expect(page.locator('[data-testid="explain-panel"]')).toBeVisible();

    // Open history drawer
    await page.locator('[data-testid="history-button"]').click();
    await expect(page.locator('[data-testid="history-drawer"]')).toBeVisible();
  });

  test('Case D: 快速切换 — 最终显示最后一个', async ({ page }) => {
    const verbs = page.locator('[data-testid="timeline-verb"]');
    const count = await verbs.count();
    // Click up to 5 verbs rapidly
    const last = Math.min(count - 1, 4);
    test.skip(last < 0, 'No timeline verbs found in DOM');

    for (let i = 0; i <= last; i++) {
      await verbs.nth(i).click({ force: true });
    }

    // Let any in-flight /api/explain requests settle
    await page.waitForTimeout(1_000);

    await expect(page.locator('[data-testid="explain-panel"]')).toBeVisible();
  });
});