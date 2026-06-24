import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ExplainContext, ExplainResult } from '../types/explain';

const MAX_HISTORY = 30;

export interface ExplainHistoryItem {
  context: ExplainContext;
  result: ExplainResult;
  viewedAt: string;
}

interface ExplainStore {
  history: ExplainHistoryItem[];
  pushHistory: (item: ExplainHistoryItem) => void;
  clearHistory: () => void;
}

const sameSelection = (a: ExplainContext, b: ExplainContext) =>
  a.scene === b.scene && a.selected_node_id === b.selected_node_id;

export const useExplainStore = create<ExplainStore>()(
  persist(
    (set, get) => ({
      history: [],
      pushHistory: (item) => {
        const deduped = get().history.filter((h) => !sameSelection(h.context, item.context));
        set({ history: [item, ...deduped].slice(0, MAX_HISTORY) });
      },
      clearHistory: () => set({ history: [] }),
    }),
    { name: 'grammar-lab.explain-history' },
  ),
);
