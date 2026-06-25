import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ExplainPanel } from '../ExplainPanel';

// mock electronAPI
const mockExplainNode = vi.fn();
const mockGetHealth = vi.fn();

beforeEach(() => {
  mockExplainNode.mockReset();
  mockGetHealth.mockReset();
  (window as any).electronAPI = {
    explainNode: mockExplainNode,
    getExplainHealth: mockGetHealth,
  };
});

describe('ExplainPanel', () => {
  it('renders empty state when no selection', () => {
    render(<ExplainPanel selection={null} sentence="Hello." darkMode={false} />);
    expect(screen.getByText(/点击节点/i)).toBeInTheDocument();
  });

  it('renders loading skeleton while fetching', async () => {
    mockExplainNode.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <ExplainPanel
        selection={{
          scene: 'timeline',
          node: { id: 'n1', type: 'tense', data: {} },
        }}
        sentence="I have lived here."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  it('renders ready state on success', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: false,
        result: {
          title: '现在完成时',
          summary: '...',
          why: '...',
          example: '...',
          common_mistakes: [],
          tips: [],
          source: 'ai',
          provider: 'ollama',
          model: 'llama3.1:8b',
          prompt_version: 'M4a_v1',
          cached: false,
          generated_at: new Date().toISOString(),
        },
      },
    });
    render(
      <ExplainPanel
        selection={{
          scene: 'timeline',
          node: { id: 'n1', type: 'tense', data: { verb: 'have lived' } },
        }}
        sentence="I have lived here."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText('现在完成时')).toBeInTheDocument();
    });
  });

  it('shows degraded banner when degraded=true', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: true,
        result: {
          title: 'Fallback Title',
          summary: '',
          why: '',
          example: '',
          common_mistakes: [],
          tips: [],
          source: 'fallback',
          provider: 'fallback',
          model: 'builtin',
          prompt_version: 'M4a_v1',
          cached: false,
          generated_at: new Date().toISOString(),
        },
      },
    });
    render(
      <ExplainPanel
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/AI unavailable/i)).toBeInTheDocument();
    });
  });
});
