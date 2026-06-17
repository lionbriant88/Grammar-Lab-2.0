import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Mock Electron API
global.window = global.window || {};
(global.window as any).electronAPI = {
  analyzeSentence: vi.fn(),
  analyzeAnatomy: vi.fn(),
  analyzeExpansion: vi.fn(),
  applyExpansion: vi.fn(),
};

// Mock crypto.randomUUID for consistent testing
if (typeof crypto === 'undefined') {
  (global as any).crypto = {
    randomUUID: () => `test-uuid-${Date.now()}-${Math.random()}`,
  };
}
