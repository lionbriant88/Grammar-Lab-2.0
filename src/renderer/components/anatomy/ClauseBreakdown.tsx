import type { AnatomyClause } from '../../types';
import { getRoleColorClass } from '../../utils/roleColor';

export interface ClauseBreakdownProps {
  clauses: AnatomyClause[];
  darkMode: boolean;
}

/** kind → (色条颜色, 徽章 class 浅/深) */
const KIND_META: Record<
  AnatomyClause['kind'],
  { bar: string; badgeLight: string; badgeDark: string }
> = {
  main: {
    bar: 'border-blue-400',
    badgeLight: 'bg-blue-100 text-blue-700',
    badgeDark: 'bg-blue-500/20 text-blue-300',
  },
  relative: {
    bar: 'border-pink-400',
    badgeLight: 'bg-pink-100 text-pink-700',
    badgeDark: 'bg-pink-500/20 text-pink-300',
  },
  adverbial: {
    bar: 'border-amber-400',
    badgeLight: 'bg-amber-100 text-amber-700',
    badgeDark: 'bg-amber-500/20 text-amber-300',
  },
  object_clause: {
    bar: 'border-violet-400',
    badgeLight: 'bg-violet-100 text-violet-700',
    badgeDark: 'bg-violet-500/20 text-violet-300',
  },
};

export default function ClauseBreakdown({ clauses, darkMode }: ClauseBreakdownProps) {
  const mainClause = clauses.find((c) => c.kind === 'main');
  const subClauses = clauses.filter((c) => c.kind !== 'main');
  const hasSub = subClauses.length > 0;

  return (
    <div
      className={`p-6 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <h3
        className={`text-sm font-bold uppercase tracking-wider mb-4 ${
          darkMode ? 'text-slate-400' : 'text-slate-500'
        }`}
      >
        {hasSub ? '主从分句分解' : '句子成分'}
      </h3>

      <div className="space-y-3">
        {mainClause && (
          <ClauseCard clause={mainClause} darkMode={darkMode} indent={false} />
        )}
        {subClauses.map((c) => (
          <ClauseCard key={c.id} clause={c} darkMode={darkMode} indent />
        ))}
      </div>
    </div>
  );
}

function ClauseCard({
  clause,
  darkMode,
  indent,
}: {
  clause: AnatomyClause;
  darkMode: boolean;
  indent: boolean;
}) {
  const meta = KIND_META[clause.kind];
  const cardBase = darkMode
    ? 'bg-slate-800/60 border-slate-700'
    : 'bg-slate-50 border-slate-200';
  const badge = darkMode ? meta.badgeDark : meta.badgeLight;

  return (
    <div
      className={[
        'rounded-xl border border-l-4 p-4',
        cardBase,
        meta.bar,
        indent ? 'ml-6' : '',
      ].join(' ')}
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className={`px-2 py-0.5 rounded-md text-xs font-bold ${badge}`}>
          {clause.label}
        </span>
        {clause.antecedent && (
          <span className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
            修饰 <span className="font-semibold">{clause.antecedent}</span>
          </span>
        )}
      </div>

      <p className={`text-sm mb-3 ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
        {clause.text}
      </p>

      {clause.elements.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {clause.elements.map((e, i) => (
            <span
              key={i}
              className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${getRoleColorClass(
                e.class,
                darkMode
              )}`}
            >
              <span className="opacity-60 mr-1">{e.label}</span>
              {e.word}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
