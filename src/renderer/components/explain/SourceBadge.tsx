import type { ExplainSource } from '../../types/explain';

const BADGE: Record<ExplainSource, { icon: string; label: string; cls: string }> = {
  ai:       { icon: '🧠', label: 'AI',    cls: 'bg-purple-100 text-purple-700' },
  cache:    { icon: '⚡', label: 'Cache', cls: 'bg-yellow-100 text-yellow-700' },
  fallback: { icon: '📘', label: 'Rule',  cls: 'bg-slate-100 text-slate-600' },
};

export function SourceBadge({ source }: { source: ExplainSource }) {
  const b = BADGE[source];
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${b.cls}`}>
      {b.icon} {b.label}
    </span>
  );
}
