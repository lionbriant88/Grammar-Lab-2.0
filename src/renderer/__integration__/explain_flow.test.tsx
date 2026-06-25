import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { ExplainPanel } from '../components/explain/ExplainPanel';
import { ExplainHistoryDrawer } from '../components/explain/ExplainHistoryDrawer';
import { useExplainStore } from '../stores/explainStore';
import type { SelectionEvent } from '../types/selection';
import type { ExplainResult } from '../types/explain';

const mockExplainNode = vi.fn();
const mockGetHealth = vi.fn();

const sampleResult = (overrides: Partial<ExplainResult> = {}): ExplainResult => ({
  title: '现在完成时',
  summary: 'summary',
  why: 'why',
  example: 'example',
  commonMistakes: [],
  tips: [],
  source: 'ai',
  provider: 'ollama',
  model: 'llama3.1:8b',
  promptVersion: 'M4a_v1',
  cached: false,
  generatedAt: new Date().toISOString(),
  degraded: false,
  ...overrides,
});

const explainResponseFor = (r: ExplainResult) => ({
  success: true,
  data: {
    ok: true,
    degraded: r.degraded,
    result: {
      title: r.title,
      summary: r.summary,
      why: r.why,
      example: r.example,
      common_mistakes: r.commonMistakes,
      tips: r.tips,
      source: r.source,
      provider: r.provider,
      model: r.model,
      prompt_version: r.promptVersion,
      cached: r.cached,
      generated_at: r.generatedAt,
    },
  },
});

beforeEach(() => {
  mockExplainNode.mockReset();
  mockGetHealth.mockReset();
  Object.assign(window, {
    electronAPI: {
      explainNode: mockExplainNode,
      getExplainHealth: mockGetHealth,
    },
  });
  // Reset persisted store between tests.
  useExplainStore.setState({ history: [] });
  // Clear localStorage from zustand/persist.
  localStorage.clear();
});

const selection = (id = 'n1'): SelectionEvent => ({
  scene: 'timeline',
  node: { id, type: 'tense', data: { verb: 'have lived' } },
});

describe('explain flow (ExplainPanel → explainStore → ExplainHistoryDrawer)', () => {
  it('writes to history when ExplainPanel receives a successful response', async () => {
    const r = sampleResult({ title: 'A' });
    mockExplainNode.mockResolvedValueOnce(explainResponseFor(r));

    render(
      <ExplainPanel selection={selection('hist-1')} sentence="I have lived here." darkMode={false} />,
    );

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
    });
    const history = useExplainStore.getState().history;
    expect(history).toHaveLength(1);
    expect(history[0].result.title).toBe('A');
    expect(history[0].context.selected_node_id).toBe('hist-1');
  });

  it('ExplainHistoryDrawer renders all pinned and unpinned entries from the store', () => {
    const r1 = sampleResult({ title: 'Pinned entry' });
    const r2 = sampleResult({ title: 'Recent entry' });
    act(() => {
      useExplainStore.getState().pushHistory({
        context: { scene: 'timeline', selected_node_id: 'p1' } as any,
        result: r1,
        viewedAt: new Date().toISOString(),
      });
      useExplainStore.getState().pushHistory({
        context: { scene: 'timeline', selected_node_id: 'p2' } as any,
        result: r2,
        viewedAt: new Date().toISOString(),
      });
    });

    const onSelect = vi.fn();
    const onClose = vi.fn();
    render(
      <ExplainHistoryDrawer open onClose={onClose} onSelect={onSelect} darkMode={false} />,
    );

    // Drawer's data-testid is on the root panel.
    expect(screen.getByTestId('history-drawer')).toBeInTheDocument();
    // Both entries must appear (no pin filter at the drawer level).
    expect(screen.getByText('Pinned entry')).toBeInTheDocument();
    expect(screen.getByText('Recent entry')).toBeInTheDocument();
  });

  it('rapid selection changes only keep the last in history (abort + request_id double-safety)', async () => {
    // First selection: slow IPC that never resolves.
    let resolveSlow: ((v: any) => void) | null = null;
    const slowPromise = new Promise<any>((resolve) => {
      resolveSlow = resolve;
    });
    mockExplainNode.mockImplementationOnce(() => slowPromise);
    // Second selection: fast success.
    mockExplainNode.mockResolvedValueOnce(
      explainResponseFor(sampleResult({ title: 'Second wins' })),
    );

    const { rerender } = render(
      <ExplainPanel selection={selection('a')} sentence="I have lived here." darkMode={false} />,
    );
    // Loading skeleton for the first (slow) call.
    await waitFor(() => {
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
    expect(mockExplainNode).toHaveBeenCalledTimes(1);

    // User clicks the second node.
    rerender(
      <ExplainPanel selection={selection('b')} sentence="I have lived here." darkMode={false} />,
    );

    // Second IPC was triggered.
    await waitFor(() => {
      expect(mockExplainNode).toHaveBeenCalledTimes(2);
    });
    // Second result renders.
    await waitFor(() => {
      expect(screen.getByText('Second wins')).toBeInTheDocument();
    });

    // If the slow call resolves *after* the fast one, the panel must not regress.
    if (resolveSlow) {
      await act(async () => {
        (resolveSlow as any)(explainResponseFor(sampleResult({ title: 'Stale should lose' })));
      });
    }
    // Give the microtask queue a turn.
    await new Promise((r) => setTimeout(r, 0));

    // Panel still shows the second selection.
    expect(screen.queryByText('Stale should lose')).not.toBeInTheDocument();
    expect(screen.getByText('Second wins')).toBeInTheDocument();

    // History dedup by (scene, selected_node_id): the latest push for each
    // selection wins. The stale push (selection 'a') must NOT be in history
    // because its call was aborted before the response was processed; the
    // second push (selection 'b') is the only one persisted.
    const history = useExplainStore.getState().history;
    const ids = history.map((h) => h.context.selected_node_id);
    expect(ids).toEqual(['b']);
  });
});
