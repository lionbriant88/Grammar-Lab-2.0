import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExplainHistoryDrawer } from '../ExplainHistoryDrawer';
import { useExplainStore } from '../../../stores/explainStore';
import type { ExplainHistoryItem } from '../../../stores/explainStore';

const buildItem = (overrides: Partial<ExplainHistoryItem>): ExplainHistoryItem => ({
  context: {
    scene: 'timeline',
    input_sentence: 'I have lived here.',
    selected_node_id: 'n1',
    node_type: 'tense',
    selected_node: { text: 'have lived' },
    engine_result_summary: {},
    language: 'zh',
    student_level: 'intermediate',
  },
  result: {
    title: '现在完成时',
    summary: '',
    why: '',
    example: '',
    commonMistakes: [],
    tips: [],
    source: 'ai',
    provider: 'ollama',
    model: 'llama3.1:8b',
    promptVersion: 'M4a_v1',
    cached: false,
    generatedAt: new Date().toISOString(),
    degraded: false,
  },
  viewedAt: new Date().toISOString(),
  ...overrides,
});

beforeEach(() => {
  useExplainStore.getState().clearHistory();
});

describe('ExplainHistoryDrawer', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <ExplainHistoryDrawer open={false} onClose={vi.fn()} onSelect={vi.fn()} darkMode={false} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('shows empty state when open with no history', () => {
    render(
      <ExplainHistoryDrawer open={true} onClose={vi.fn()} onSelect={vi.fn()} darkMode={false} />,
    );
    expect(screen.getByText(/暂无历史/i)).toBeInTheDocument();
  });

  it('groups history by Today/Yesterday/Earlier', () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 86400000);
    const threeDaysAgo = new Date(now.getTime() - 3 * 86400000);

    useExplainStore.getState().pushHistory(buildItem({ viewedAt: now.toISOString() }));
    useExplainStore.getState().pushHistory(
      buildItem({ context: { ...buildItem({}).context, selected_node_id: 'n2' }, viewedAt: yesterday.toISOString() }),
    );
    useExplainStore.getState().pushHistory(
      buildItem({ context: { ...buildItem({}).context, selected_node_id: 'n3' }, viewedAt: threeDaysAgo.toISOString() }),
    );

    render(
      <ExplainHistoryDrawer open={true} onClose={vi.fn()} onSelect={vi.fn()} darkMode={false} />,
    );

    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
    expect(screen.getByText('Earlier')).toBeInTheDocument();
  });

  it('fires onSelect when history item clicked', () => {
    const onSelect = vi.fn();
    useExplainStore.getState().pushHistory(buildItem({}));

    render(
      <ExplainHistoryDrawer open={true} onClose={vi.fn()} onSelect={onSelect} darkMode={false} />,
    );

    const itemButton = screen.getByText('现在完成时');
    fireEvent.click(itemButton);

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].result.title).toBe('现在完成时');
  });

  it('fires onClose when overlay backdrop clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <ExplainHistoryDrawer open={true} onClose={onClose} onSelect={vi.fn()} darkMode={false} />,
    );

    // Backdrop is the first fixed inset-0 div
    const backdrop = container.querySelector('.bg-black\\/20');
    expect(backdrop).toBeInTheDocument();
    fireEvent.click(backdrop!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('fires onClose when X button clicked', () => {
    const onClose = vi.fn();
    render(
      <ExplainHistoryDrawer open={true} onClose={onClose} onSelect={vi.fn()} darkMode={false} />,
    );

    const closeBtn = screen.getByText('✕');
    fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
