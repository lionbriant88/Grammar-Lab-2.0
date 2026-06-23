import type { PhraseNodeInfo, PhraseType, SentenceVersion } from '../../types';
import {
  getPhraseBadge,
  featuresToBadges,
  getPhraseLabel,
} from '../../utils/phraseColor';
import { computeQuotas, type QuotaMap } from '../../utils/expansionQuota';

export interface ExpansionTreeProps {
  sentence: string;
  phrases: PhraseNodeInfo[];
  darkMode: boolean;
  onSelectPhrase: (phraseId: string) => void;
  highlightedId: string | null;
  /** M3a+1.3:历史 versions(从 history 拿,空时回退到当前 phrases) */
  versions?: SentenceVersion[];
  currentVersionId?: string;
  onSelectVersion?: (versionId: string) => void;
}

/**
 * 右栏「句法结构」(M3b 升级命名)。
 * M3a+1.3:子树改嵌套卡片 + 缩进,无箭头。选中短语的子项展开显示 kind 分组 + chips。
 */
export default function ExpansionTree({
  sentence,
  phrases,
  darkMode,
  onSelectPhrase,
  highlightedId,
}: ExpansionTreeProps) {
  const quotaMap = computeQuotas(phrases);
  return (
    <div
      className={`p-6 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <h3
        className={`text-sm font-bold uppercase tracking-wider mb-1 ${
          darkMode ? 'text-slate-400' : 'text-slate-500'
        }`}
      >
        句法结构
      </h3>
      <p className={`text-[10px] mb-4 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
        Sentence Structure · 句子短语结构与扩展可能
      </p>

      {/* 根:整句 */}
      <div
        className={`rounded-lg px-3 py-2 mb-3 text-center text-sm font-medium ${
          darkMode ? 'bg-slate-800/70 text-slate-200' : 'bg-slate-100 text-slate-700'
        }`}
      >
        {sentence}
      </div>

      {/* 二层:各短语节点(无箭头,纯缩进) */}
      <div className="space-y-2 pl-3 border-l-2 border-dashed border-slate-300 dark:border-slate-700">
        {phrases.map((p) => (
          <PhraseBranch
            key={p.id}
            phrase={p}
            darkMode={darkMode}
            isHighlighted={highlightedId === p.id}
            quotaMap={quotaMap}
            onSelect={() => onSelectPhrase(p.id)}
          />
        ))}
      </div>
    </div>
  );
}

function PhraseBranch({
  phrase,
  darkMode,
  isHighlighted,
  quotaMap,
  onSelect,
}: {
  phrase: PhraseNodeInfo;
  darkMode: boolean;
  isHighlighted: boolean;
  quotaMap: QuotaMap;
  onSelect: () => void;
}) {
  const type = phrase.type as PhraseType;
  const featureBadges = featuresToBadges(type, phrase.features);
  const dim = !phrase.is_expandable;
  const phraseQuota = quotaMap[phrase.id] ?? {};
  const isExpanded = Object.values(phraseQuota).some((q) => q.used > 0);

  // 边框:可扩展=蓝,选中=绿,不可扩展=灰
  const borderClass = isHighlighted
    ? 'border-emerald-400'
    : dim
    ? 'border-slate-300 dark:border-slate-700'
    : isExpanded
    ? 'border-blue-400'
    : 'border-blue-300 dark:border-blue-500/50';

  return (
    <div className="ml-2">
      {/* 二层:短语节点(嵌套卡片) */}
      <button
        type="button"
        onClick={onSelect}
        disabled={dim}
        className={[
          'inline-flex items-center gap-1.5 rounded-lg border-2 px-2 py-1 transition-all',
          borderClass,
          dim ? 'opacity-50 cursor-default' : 'hover:-translate-y-0.5',
          isHighlighted ? 'ring-2 ring-emerald-400' : '',
        ].join(' ')}
        title={dim ? '该短语当前不可扩展' : '点击高亮中栏'}
      >
        <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${getPhraseBadge(type, darkMode)}`}>
          {type}
        </span>
        <span className={`text-sm font-medium ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
          {phrase.text}
        </span>
        {featureBadges.map((tag) => (
          <span
            key={tag}
            className={`px-1 py-0 rounded text-[9px] font-mono ${
              darkMode ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {tag}
          </span>
        ))}
        {/* 金色已扩展标记(若 isExpanded) */}
        {isExpanded && (
          <span className="inline-block w-3 h-3 rounded-full bg-amber-400" title="已扩展" />
        )}
      </button>

      {/* 三层:子项(若该 phrase 有 children 或 is_expandable 时显示 kind 分组) */}
      {!dim && phrase.is_expandable && (
        <div className="mt-2 ml-4 space-y-1.5 border-l-2 border-slate-200 dark:border-slate-700 pl-3">
          {phrase.candidates.map((c) => {
            const quota = (phraseQuota as any)[c.kind];
            const reached = quota?.reached ?? false;
            const used = quota?.used ?? 0;
            const max = quota?.max ?? 0;
            return (
              <div key={c.kind} className="flex items-start gap-1.5 flex-wrap">
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    c.available
                      ? reached
                        ? darkMode ? 'bg-amber-500/20 text-amber-300' : 'bg-amber-100 text-amber-700'
                        : darkMode ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-700'
                      : darkMode ? 'bg-slate-700/50 text-slate-500' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {c.kind_label_cn}
                  {c.available && ` (${used}/${max})`}
                  {!c.available && ' · 未开放'}
                </span>
                {c.available && used > 0 && c.templates.slice(0, 3).map((t) => (
                  <span
                    key={t.template_id}
                    className={`px-1.5 py-0.5 rounded text-[10px] flex items-center gap-0.5 ${
                      darkMode ? 'bg-amber-500/20 text-amber-200' : 'bg-amber-50 text-amber-700'
                    }`}
                  >
                    <span>✓</span>
                    <span>{t.surface}</span>
                  </span>
                ))}
              </div>
            );
          })}
        </div>
      )}

      <div className={`mt-0.5 ml-1 text-[9px] uppercase tracking-wider ${darkMode ? 'text-slate-600' : 'text-slate-400'}`}>
        {getPhraseLabel(type)}
      </div>
    </div>
  );
}
