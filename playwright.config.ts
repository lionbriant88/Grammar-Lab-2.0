import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E config for Grammar Lab M4 Explain Panel.
 *
 * The Electron dev server runs at Vite's default port 5173.
 * In CI the user sets APP_URL=http://127.0.0.1:5173 and starts:
 *   1. `npm run dev` (Electron + Vite)
 *   2. backend (separate process, see task-26 brief)
 *
 * These tests assume the renderer is reachable at APP_URL via plain HTTP,
 * which is how `electron-vite dev` exposes the Vite dev server.
 */
const APP_URL = process.env.APP_URL || 'http://127.0.0.1:5173';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: APP_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});