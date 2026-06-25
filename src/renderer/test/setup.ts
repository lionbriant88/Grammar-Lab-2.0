import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import type { ElectronAPI } from '../../preload';

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Tests stub electronAPI as needed. We declare a partial because individual tests
// only override the methods they exercise; the remaining methods are unused stubs.
type ElectronAPIStub = Pick<
  ElectronAPI,
  'analyzeSentence' | 'analyzeAnatomy' | 'analyzeExpansion' | 'applyExpansion'
>;
const electronAPIStub: ElectronAPIStub = {
  analyzeSentence: vi.fn(),
  analyzeAnatomy: vi.fn(),
  analyzeExpansion: vi.fn(),
  applyExpansion: vi.fn(),
};
Object.assign(window, { electronAPI: electronAPIStub });

// Mock crypto.randomUUID for consistent testing
if (typeof crypto === 'undefined') {
  (global as any).crypto = {
    randomUUID: () => `test-uuid-${Date.now()}-${Math.random()}`,
  };
}
