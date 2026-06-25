import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MarkdownView } from '../MarkdownView';

describe('MarkdownView', () => {
  it('returns null for empty content', () => {
    const { container } = render(<MarkdownView content="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders markdown content as prose', () => {
    const { container } = render(<MarkdownView content="**bold** and *italic*" />);
    const prose = container.querySelector('.prose');
    expect(prose).toBeInTheDocument();
    expect(prose?.textContent).toContain('bold');
    expect(prose?.textContent).toContain('italic');
  });
});
