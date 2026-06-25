import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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

  it('renders all result sections (summary, why, example, commonMistakes, tips)', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: false,
        result: {
          title: '现在完成时',
          summary: 'A summary',
          why: 'A why',
          example: 'An example',
          common_mistakes: ['mistake 1', 'mistake 2'],
          tips: ['tip 1'],
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
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText('A summary')).toBeInTheDocument();
    });
    expect(screen.getByText('A why')).toBeInTheDocument();
    expect(screen.getByText('An example')).toBeInTheDocument();
    expect(screen.getByText('mistake 1')).toBeInTheDocument();
    expect(screen.getByText('mistake 2')).toBeInTheDocument();
    expect(screen.getByText('tip 1')).toBeInTheDocument();
  });

  it('uses builtin fallback when API returns failure', async () => {
    mockExplainNode.mockResolvedValue({ success: false, error: 'oops' });
    render(
      <ExplainPanel
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      // BUILTIN_FALLBACK title is "解释"
      expect(screen.getByText('解释')).toBeInTheDocument();
    });
    // Should also show degraded banner
    expect(screen.getByText(/AI unavailable/i)).toBeInTheDocument();
  });

  it('shows error state when API throws', async () => {
    mockExplainNode.mockRejectedValue(new Error('boom'));
    render(
      <ExplainPanel
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/出错了/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/boom/i)).toBeInTheDocument();
  });

  it('toggles pinned state when pin button clicked', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: false,
        result: {
          title: 'Title',
          summary: 'S',
          why: 'W',
          example: '',
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
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText('Title')).toBeInTheDocument();
    });
    const pinBtn = screen.getByTitle('Pin 当前解释');
    expect(pinBtn).toBeInTheDocument();
    // Click toggles to pinned
    fireEvent.click(pinBtn);
    expect(screen.getByTitle('取消 Pin')).toBeInTheDocument();
  });
});
