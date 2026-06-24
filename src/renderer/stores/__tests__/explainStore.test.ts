import { describe, it, expect, beforeEach } from 'vitest';
import { useExplainStore } from '../explainStore';

describe('explainStore', () => {
  beforeEach(() => {
    useExplainStore.getState().clearHistory();
  });

  const fakeItem = (id: string) => ({
    context: {
      scene: 'timeline' as const,
      input_sentence: 's',
      selected_node_id: id,
      node_type: 'tense' as const,
      selected_node: {},
      engine_result_summary: {},
      language: 'zh' as const,
      student_level: 'intermediate' as const,
    },
    result: {
      title: id,
      summary: '',
      why: '',
      example: '',
      commonMistakes: [],
      tips: [],
      source: 'ai' as const,
      provider: 'ollama',
      model: 'llama3.1:8b',
      promptVersion: 'M4a_v1',
      cached: false,
      generatedAt: new Date().toISOString(),
      degraded: false,
    },
    viewedAt: new Date().toISOString(),
  });

  it('pushHistory adds item at front', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().pushHistory(fakeItem('b'));
    expect(useExplainStore.getState().history.map((h) => h.result.title)).toEqual(['b', 'a']);
  });

  it('pushHistory dedupes by selected_node_id', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().pushHistory(fakeItem('a'));
    expect(useExplainStore.getState().history.length).toBe(1);
  });

  it('pushHistory caps at 30 items (LRU)', () => {
    for (let i = 0; i < 35; i++) {
      useExplainStore.getState().pushHistory(fakeItem(`n${i}`));
    }
    const hist = useExplainStore.getState().history;
    expect(hist.length).toBe(30);
    expect(hist[0].result.title).toBe('n34'); // 最新
    expect(hist[29].result.title).toBe('n5');
  });

  it('clearHistory empties store', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().clearHistory();
    expect(useExplainStore.getState().history).toEqual([]);
  });
});
