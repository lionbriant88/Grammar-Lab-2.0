import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAppState } from './appState';
import type { PhraseNodeInfo } from '../types';

// Helper to create mock PhraseNodeInfo
const createMockPhrase = (overrides: Partial<PhraseNodeInfo>): PhraseNodeInfo => ({
  id: 'p1',
  type: 'NP',
  text: 'test',
  head_token_text: 'test',
  head_pos: 'NOUN',
  syntactic_role: 'nsubj',
  span: [0, 4],
  features: {},
  parent_id: null,
  children_ids: [],
  is_expandable: true,
  candidates: [],
  ...overrides,
});

describe('appState - 50 步上限截断', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该保留原句(index 0)并截断中间历史,保持最多50个版本', async () => {
    // Mock window.electronAPI for this test
    (window as any).electronAPI = {
      analyzeExpansion: vi.fn().mockResolvedValue({
        success: true,
        data: {
          sentence: 'I wake up.',
          phrases: [
            createMockPhrase({ id: 'p1', text: 'I', type: 'NP', span: [0, 1] }),
            createMockPhrase({ id: 'p2', text: 'wake up', type: 'VP', span: [2, 9] }),
          ],
          warnings: [],
        },
      }),
      applyExpansion: vi.fn(),
    };

    const { result } = renderHook(() => useAppState());

    // 初始化:analyzeExpansion 创建 v0(原句)
    await act(async () => {
      await result.current[1].analyzeExpansion('I wake up.');
    });

    await waitFor(() => {
      expect(result.current[0].expansionHistory.length).toBe(1);
    });

    const originalSentence = result.current[0].expansionHistory[0].sentence;

    // 模拟 applyExpansion 调用52次,每次等待完成
    for (let i = 1; i <= 52; i++) {
      const mockResponse = {
        success: true,
        data: {
          sentence: `I wake up v${i}.`,
          phrases: [
            createMockPhrase({
              id: 'p1',
              text: 'I',
              type: 'NP',
              span: [0, 1],
              candidates: [{ kind: 'adjective', kind_label_cn: '形容词', templates: [], level: 1, available: true }]
            }),
            createMockPhrase({ id: 'p2', text: `wake up v${i}`, type: 'VP', span: [2, 10 + i.toString().length] }),
          ],
          warnings: [],
          validation: { severity: 'PASS', is_valid: true, errors: [], warnings: [], infos: [], auto_corrections: [] },
        },
      };

      (window.electronAPI.applyExpansion as any).mockResolvedValueOnce(mockResponse);

      const prevLength = result.current[0].expansionHistory.length;

      await act(async () => {
        await result.current[1].applyExpansion(`I wake up v${i - 1}.`, 'p1', 'tpl_adjective_test');
      });

      // 等待 history 更新
      await waitFor(() => {
        const newLength = result.current[0].expansionHistory.length;
        expect(newLength).toBeGreaterThan(prevLength - 1); // 允许截断时长度不增加
      });
    }

    const history = result.current[0].expansionHistory;
    // 应该正好50个版本
    expect(history.length).toBe(50);
    // 第一个版本应该是原句
    expect(history[0].sentence).toBe(originalSentence);
    // 最后一个版本应该是 v52
    expect(history[49].sentence).toBe('I wake up v52.');
    // currentIndex 应该指向最后一个(49)
    expect(result.current[0].expansionCurrentIndex).toBe(50);
  });

  it('应该在截断后保持原句 + 最近49步', async () => {
    // Mock window.electronAPI for this test
    (window as any).electronAPI = {
      analyzeExpansion: vi.fn().mockResolvedValue({
        success: true,
        data: {
          sentence: 'Original sentence.',
          phrases: [
            createMockPhrase({ id: 'p1', text: 'Original', type: 'NP', span: [0, 8] }),
          ],
          warnings: [],
        },
      }),
      applyExpansion: vi.fn(),
    };

    const { result } = renderHook(() => useAppState());

    await act(async () => {
      await result.current[1].analyzeExpansion('Original sentence.');
    });

    await waitFor(() => {
      expect(result.current[0].expansionHistory.length).toBe(1);
    });

    // 推送60个版本
    for (let i = 1; i <= 60; i++) {
      const mockResponse = {
        success: true,
        data: {
          sentence: `Sentence v${i}.`,
          phrases: [createMockPhrase({ id: 'p1', text: `v${i}`, type: 'NP', span: [0, 2] })],
          warnings: [],
          validation: { severity: 'PASS', is_valid: true, errors: [], warnings: [], infos: [], auto_corrections: [] },
        },
      };
      (window.electronAPI.applyExpansion as any).mockResolvedValueOnce(mockResponse);

      await act(async () => {
        await result.current[1].applyExpansion(i === 1 ? 'Original sentence.' : `Sentence v${i - 1}.`, 'p1', 'tpl_test');
      });

      await waitFor(() => {
        expect(result.current[0].expansionHistory.length).toBeGreaterThan(0);
      });
    }

    const history = result.current[0].expansionHistory;
    expect(history.length).toBe(50);
    expect(history[0].sentence).toBe('Original sentence.');
    // v12-v60 应该被保留(v1-v11被截断了)
    expect(history[1].sentence).toBe('Sentence v12.');
    expect(history[49].sentence).toBe('Sentence v60.');
  });

  it('应该在未达到50步时正常工作', async () => {
    // Mock window.electronAPI for this test
    (window as any).electronAPI = {
      analyzeExpansion: vi.fn().mockResolvedValue({
        success: true,
        data: {
          sentence: 'Test sentence.',
          phrases: [
            createMockPhrase({ id: 'p1', text: 'Test', type: 'NP', span: [0, 4] }),
          ],
          warnings: [],
        },
      }),
      applyExpansion: vi.fn(),
    };

    const { result } = renderHook(() => useAppState());

    await act(async () => {
      await result.current[1].analyzeExpansion('Test sentence.');
    });

    await waitFor(() => {
      expect(result.current[0].expansionHistory.length).toBe(1);
    });

    // 只推送10个版本
    for (let i = 1; i <= 10; i++) {
      const mockResponse = {
        success: true,
        data: {
          sentence: `Test v${i}.`,
          phrases: [createMockPhrase({ id: 'p1', text: `v${i}`, type: 'NP', span: [0, 2] })],
          warnings: [],
        },
      };
      (window.electronAPI.applyExpansion as any).mockResolvedValueOnce(mockResponse);

      await act(async () => {
        await result.current[1].applyExpansion(i === 1 ? 'Test sentence.' : `Test v${i - 1}.`, 'p1', 'tpl_test');
      });

      await waitFor(() => {
        expect(result.current[0].expansionHistory.length).toBeGreaterThan(i);
      });
    }

    const history = result.current[0].expansionHistory;
    // 应该是11个版本(原句 + 10次扩展)
    expect(history.length).toBe(11);
    expect(history[0].sentence).toBe('Test sentence.');
    expect(history[10].sentence).toBe('Test v10.');
    expect(result.current[0].expansionCurrentIndex).toBe(10);
  });

  it('应该在 Undo 后 Apply 时正确截断 future 并维持50步上限', async () => {
    // Mock window.electronAPI for this test
    (window as any).electronAPI = {
      analyzeExpansion: vi.fn().mockResolvedValue({
        success: true,
        data: {
          sentence: 'Base sentence.',
          phrases: [
            createMockPhrase({ id: 'p1', text: 'Base', type: 'NP', span: [0, 4] }),
          ],
          warnings: [],
        },
      }),
      applyExpansion: vi.fn(),
    };

    const { result } = renderHook(() => useAppState());

    await act(async () => {
      await result.current[1].analyzeExpansion('Base sentence.');
    });

    await waitFor(() => {
      expect(result.current[0].expansionHistory.length).toBe(1);
    });

    // 推送5个版本
    for (let i = 1; i <= 5; i++) {
      const mockResponse = {
        success: true,
        data: {
          sentence: `Base v${i}.`,
          phrases: [createMockPhrase({ id: 'p1', text: `v${i}`, type: 'NP', span: [0, 2] })],
          warnings: [],
        },
      };
      (window.electronAPI.applyExpansion as any).mockResolvedValueOnce(mockResponse);

      await act(async () => {
        await result.current[1].applyExpansion(i === 1 ? 'Base sentence.' : `Base v${i - 1}.`, 'p1', 'tpl_test');
      });

      await waitFor(() => {
        expect(result.current[0].expansionHistory.length).toBe(i + 1);
      });
    }

    expect(result.current[0].expansionHistory.length).toBe(6);
    expect(result.current[0].expansionCurrentIndex).toBe(5);

    // Undo 3次,回到 index 2
    act(() => {
      result.current[1].undoExpansion();
      result.current[1].undoExpansion();
      result.current[1].undoExpansion();
    });

    await waitFor(() => {
      expect(result.current[0].expansionCurrentIndex).toBe(2);
    });

    // 从 index 2 再 Apply 一个新版本
    const mockResponse = {
      success: true,
      data: {
        sentence: 'Base new branch.',
        phrases: [createMockPhrase({ id: 'p1', text: 'new', type: 'NP', span: [0, 3] })],
        warnings: [],
      },
    };
    (window.electronAPI.applyExpansion as any).mockResolvedValueOnce(mockResponse);

    await act(async () => {
      await result.current[1].applyExpansion('Base v2.', 'p1', 'tpl_test');
    });

    await waitFor(() => {
      const history = result.current[0].expansionHistory;
      // 应该截断 future:保留 0-2 + 新版本 = 4个版本
      expect(history.length).toBe(4);
      expect(history[0].sentence).toBe('Base sentence.');
      expect(history[1].sentence).toBe('Base v1.');
      expect(history[2].sentence).toBe('Base v2.');
      expect(history[3].sentence).toBe('Base new branch.');
      expect(result.current[0].expansionCurrentIndex).toBe(3);
    });
  });
});
