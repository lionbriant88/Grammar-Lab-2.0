import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/renderer/test/setup.ts'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.{idea,git,cache,output,temp}/**',
      '.worktrees/**',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        '**/node_modules/**',
        '**/dist/**',
        '**/.{idea,git,cache,output,temp}/**',
        '.worktrees/**',
        // M3a orphan: 50-step history features incomplete on main, full coverage lands with feature/m3a-plus-1 merge
        'src/renderer/state/**',
        // Test files
        '**/*.test.{ts,tsx}',
        // Type definitions
        '**/types/**',
        // Test setup
        'src/renderer/test/**',
        // Main/preload (Node side, not part of renderer coverage)
        'src/main/**',
        'src/preload/**',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
