import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SourceBadge } from '../SourceBadge';

describe('SourceBadge', () => {
  it('renders AI badge with brain icon', () => {
    render(<SourceBadge source="ai" />);
    expect(screen.getByText((content) => content.includes('🧠'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('AI'))).toBeInTheDocument();
  });

  it('renders Cache badge with bolt icon', () => {
    render(<SourceBadge source="cache" />);
    expect(screen.getByText((content) => content.includes('⚡'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('Cache'))).toBeInTheDocument();
  });

  it('renders Fallback badge with book icon', () => {
    render(<SourceBadge source="fallback" />);
    expect(screen.getByText((content) => content.includes('📘'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('Rule'))).toBeInTheDocument();
  });
});
