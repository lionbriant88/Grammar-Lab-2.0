import { create } from 'zustand';
import type { HealthState } from '../types/explain';

interface HealthStore {
  health: HealthState;
  setHealth: (h: HealthState) => void;
  refresh: () => Promise<void>;
}

export const useHealthStore = create<HealthStore>((set) => ({
  health: { status: 'unknown' },
  setHealth: (h) => set({ health: h }),
  refresh: async () => {
    try {
      const r = await window.electronAPI.getExplainHealth();
      if (r?.success && r.data?.available) {
        set({
          health: {
            status: 'ready',
            provider: r.data.provider,
            model: r.data.model,
            latencyMs: r.data.latency_ms,
          },
        });
      } else {
        set({
          health: { status: 'offline', reason: r?.data?.error || 'unavailable' },
        });
      }
    } catch (e) {
      set({ health: { status: 'offline', reason: String(e) } });
    }
  },
}));
