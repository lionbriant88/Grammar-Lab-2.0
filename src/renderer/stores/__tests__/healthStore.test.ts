import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useHealthStore } from '../healthStore';

const mockGetExplainHealth = vi.fn();

beforeEach(() => {
  mockGetExplainHealth.mockReset();
  // Per-test override of the ambient electronAPI.
  Object.assign(window, {
    electronAPI: {
      getExplainHealth: mockGetExplainHealth,
    },
  });
  // Reset store to initial state
  useHealthStore.setState({ health: { status: 'unknown' } });
});

describe('healthStore', () => {
  it('starts with unknown status', () => {
    expect(useHealthStore.getState().health.status).toBe('unknown');
  });

  it('setHealth replaces the state', () => {
    useHealthStore.getState().setHealth({
      status: 'ready',
      provider: 'ollama',
      model: 'llama3.1:8b',
      latencyMs: 120,
    });
    const h = useHealthStore.getState().health;
    expect(h.status).toBe('ready');
    expect(h.provider).toBe('ollama');
    expect(h.model).toBe('llama3.1:8b');
    expect(h.latencyMs).toBe(120);
  });

  it('refresh sets ready when AI available', async () => {
    mockGetExplainHealth.mockResolvedValue({
      success: true,
      data: { available: true, provider: 'ollama', model: 'llama3.1:8b', latency_ms: 80 },
    });

    await useHealthStore.getState().refresh();
    const h = useHealthStore.getState().health;
    expect(h.status).toBe('ready');
    expect(h.provider).toBe('ollama');
    expect(h.latencyMs).toBe(80);
  });

  it('refresh sets offline when AI unavailable', async () => {
    mockGetExplainHealth.mockResolvedValue({
      success: true,
      data: { available: false, error: 'no model' },
    });

    await useHealthStore.getState().refresh();
    const h = useHealthStore.getState().health;
    expect(h.status).toBe('offline');
    expect(h.reason).toBe('no model');
  });

  it('refresh sets offline when response not success', async () => {
    mockGetExplainHealth.mockResolvedValue({ success: false });

    await useHealthStore.getState().refresh();
    const h = useHealthStore.getState().health;
    expect(h.status).toBe('offline');
    expect(h.reason).toBe('unavailable');
  });

  it('refresh sets offline when getExplainHealth throws', async () => {
    mockGetExplainHealth.mockRejectedValue(new Error('network down'));

    await useHealthStore.getState().refresh();
    const h = useHealthStore.getState().health;
    expect(h.status).toBe('offline');
    expect(h.reason).toContain('network down');
  });
});
