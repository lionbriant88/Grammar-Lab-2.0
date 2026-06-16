import type { PhraseNodeInfo, PhraseType } from '../../types';
import {
  getPhraseColor,
  getPhraseBadge,
  featuresToBadges,
  getPhraseLabel,
} from '../../utils/phraseColor';

export interface SentenceCanvasProps {
  phrases: PhraseNodeInfo[];
  darkMode: boolean;
  /** 当前展开 [+] 菜单的短语 id(null=无) */
  menuOpenFor: string | null;
  /** 树上某 kind 叶子被点 → 高亮对应短语 [+] */
  highlightedId: string | null;
  onToggleMenu: (phraseId: string) => void;
}

export default function SentenceCanvas({
  phrases,
  darkMode,
  menuOpenFor,
  highlightedId,
  onToggleMenu,
}: SentenceCanvasProps) {
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
        句子画布
      </h3>

      <div className="flex flex-wrap items-stretch gap-2.5">
        {phrases.map((p) => (
          <PhraseCard
            key={p.id}
            phrase={p}
            darkMode={darkMode}
            isOpen={menuOpenFor === p.id}
            isHighlighted={highlightedId === p.id}
            onToggle={() => onToggleMenu(p.id)}
          />
        ))}
      </div>

      {phrases.length === 0 && (
        <p className={`text-sm ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          未识别到短语。
        </p>
      )}

      {/* 图例 */}
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5">
        <LegendDot darkMode={darkMode} label="可扩展" dot="bg-blue-400" />
        <LegendDot darkMode={darkMode} label="不可扩展" dot={darkMode ? 'bg-slate-600' : 'bg-slate-300'} />
      </div>
    </div>
  );
}

function LegendDot({
  darkMode,
  label,
  dot,
}: {
  darkMode: boolean;
  label: string;
  dot: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-block w-3 h-3 rounded-full ${dot}`} />
      <span className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{label}</span>
    </div>
  );
}

function PhraseCard({
  phrase,
  darkMode,
  isOpen,
  isHighlighted,
  onToggle,
}: {
  phrase: PhraseNodeInfo;
  darkMode: boolean;
  isOpen: boolean;
  isHighlighted: boolean;
  onToggle: () => void;
}) {
  const type = phrase.type as PhraseType;
  const featureBadges = featuresToBadges(type, phrase.features);

  // 不可扩展 → 灰显(opacity-50),不可点
  if (!phrase.is_expandable) {
    return (
      <div
        className={`group relative rounded-xl border px-3 py-2 opacity-50 select-none ${
          darkMode ? 'bg-slate-800/40 border-slate-700' : 'bg-slate-50 border-slate-200'
        }`}
      >
        <PhraseBody phrase={phrase} type={type} darkMode={darkMode} featureBadges={featureBadges} />
      </div>
    );
  }

  // 可扩展 → 高亮描边(蓝)+ 绿点 + [+]
  return (
    <button
      type="button"
      onClick={onToggle}
      className={[
        'group relative rounded-xl border px-3 py-2 transition-all text-left',
        'border-2',
        darkMode ? 'border-blue-400/70 hover:border-blue-400' : 'border-blue-400 hover:border-blue-500',
        isHighlighted ? 'ring-2 ring-blue-400 -translate-y-0.5 shadow-md' : 'hover:-translate-y-0.5 hover:shadow-md',
        isOpen ? 'ring-2 ring-blue-400 -translate-y-0.5 shadow-md' : '',
        getPhraseColor(type, darkMode),
      ].join(' ')}
      title="点击查看可扩展项"
    >
      {/* 右上角绿点(可扩展标识) */}
      <span className="absolute -top-1.5 -right-1.5 w-3 h-3 rounded-full bg-emerald-400 ring-2 ring-white dark:ring-slate-900" />
      <PhraseBody phrase={phrase} type={type} darkMode={darkMode} featureBadges={featureBadges} expandable />
      {/* [+] 按钮 */}
      <span
        className={`mt-1.5 inline-flex items-center gap-0.5 text-xs font-bold ${
          darkMode ? 'text-blue-300' : 'text-blue-600'
        }`}
      >
        {isOpen ? '− 收起' : '+ 扩展'}
      </span>
    </button>
  );
}

function PhraseBody({
  phrase,
  type,
  darkMode,
  featureBadges,
  expandable = false,
}: {
  phrase: PhraseNodeInfo;
  type: PhraseType;
  darkMode: boolean;
  featureBadges: string[];
  expandable?: boolean;
}) {
  return (
    <>
      <div className="flex items-center gap-1.5 mb-1">
        <span
          className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold tracking-wide ${getPhraseBadge(
            type,
            darkMode
          )}`}
        >
          {type}
        </span>
        {featureBadges.map((tag) => (
          <span
            key={tag}
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
              darkMode ? 'bg-slate-700/60 text-slate-300' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {tag}
          </span>
        ))}
      </div>
      <div
        className={`text-sm font-medium leading-snug ${
          expandable ? (darkMode ? 'text-slate-100' : 'text-slate-800') : darkMode ? 'text-slate-400' : 'text-slate-600'
        }`}
      >
        {phrase.text}
      </div>
      <div
        className={`mt-0.5 text-[10px] uppercase tracking-wider ${
          darkMode ? 'text-slate-500' : 'text-slate-400'
        }`}
      >
        {getPhraseLabel(type)}
      </div>
    </>
  );
}
