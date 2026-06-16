import type { PhraseNodeInfo, PhraseType } from '../../types';
import {
  getPhraseBadge,
  featuresToBadges,
  getPhraseLabel,
} from '../../utils/phraseColor';

export interface ExpansionTreeProps {
  sentence: string;
  phrases: PhraseNodeInfo[];
  darkMode: boolean;
  /** 点击 kind 叶子 → 联动中栏高亮对应短语 [+] */
  onSelectPhrase: (phraseId: string) => void;
  /** 当前高亮的短语 id(来自中栏/树点击) */
  highlightedId: string | null;
}

/**
 * 右栏「短语结构图」(M3a)。
 *
 * 调整 3(命名):M3a 标题文案 = 「短语结构图」(Phrase Structure Preview),
 * **不叫**「成分句法树」——M3a 尚未引入 Benepar,当前只是 spaCy 的 phrase grouping。
 * M3b 引入 Benepar 后再升级命名。组件文件名不变。
 *
 * 结构(扁平短语序列,非嵌套树——M3a 不显示 Parent-Child 嵌套):
 *   根:整句文本
 *   二层:各短语节点(NP/VP/PP),按句中顺序;可扩展高亮、不可扩展灰显
 *   三层:可扩展短语下的 kind 分支 + 前 2-3 个模板 surface 叶子
 *   L2/L3 kind 标「未开放」灰态
 */
export default function ExpansionTree({
  sentence,
  phrases,
  darkMode,
  onSelectPhrase,
  highlightedId,
}: ExpansionTreeProps) {
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
        短语结构图
      </h3>
      <p className={`text-[10px] mb-4 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
        Phrase Structure Preview · 静态展示每个短语可往哪些方向扩展
      </p>

      {/* 根:整句 */}
      <div
        className={`rounded-lg px-3 py-2 mb-3 text-center text-sm font-medium ${
          darkMode ? 'bg-slate-800/70 text-slate-200' : 'bg-slate-100 text-slate-700'
        }`}
      >
        {sentence}
      </div>

      {/* 二层 + 三层 */}
      <div className="space-y-2 pl-1 border-l-2 border-dashed border-slate-300 dark:border-slate-700">
        {phrases.map((p) => (
          <PhraseBranch
            key={p.id}
            phrase={p}
            darkMode={darkMode}
            isHighlighted={highlightedId === p.id}
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
  onSelect,
}: {
  phrase: PhraseNodeInfo;
  darkMode: boolean;
  isHighlighted: boolean;
  onSelect: () => void;
}) {
  const type = phrase.type as PhraseType;
  const featureBadges = featuresToBadges(type, phrase.features);
  const dim = !phrase.is_expandable;

  return (
    <div className="ml-2">
      {/* 二层:短语节点 */}
      <button
        type="button"
        onClick={onSelect}
        disabled={dim}
        className={[
          'inline-flex items-center gap-1.5 rounded-lg px-2 py-1 transition-all',
          dim ? 'opacity-50 cursor-default' : 'hover:-translate-y-0.5',
          isHighlighted ? 'ring-2 ring-blue-400' : '',
        ].join(' ')}
        title={dim ? '该短语当前不可扩展' : '点击高亮中栏 [+]'}
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
        {phrase.is_expandable && (
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
        )}
      </button>

      {/* 三层:kind 分支 + 模板叶子(仅可扩展) */}
      {phrase.is_expandable && phrase.candidates.length > 0 && (
        <div className="mt-1 ml-4 space-y-1 border-l border-slate-200 dark:border-slate-700 pl-3">
          {phrase.candidates.map((c) => (
            <div key={c.kind} className="flex items-start gap-1.5 flex-wrap">
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  c.available
                    ? darkMode
                      ? 'bg-blue-500/20 text-blue-300'
                      : 'bg-blue-100 text-blue-700'
                    : darkMode
                    ? 'bg-slate-700/50 text-slate-500'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {c.kind_label_cn}
                {!c.available && ' · 未开放'}
              </span>
              {c.available &&
                c.templates.slice(0, 3).map((t) => (
                  <span
                    key={t.template_id}
                    className={`px-1.5 py-0.5 rounded text-[10px] ${
                      darkMode ? 'bg-slate-800 text-slate-300' : 'bg-slate-50 text-slate-500'
                    }`}
                  >
                    {t.surface}
                  </span>
                ))}
            </div>
          ))}
        </div>
      )}

      <div className={`mt-0.5 ml-1 text-[9px] uppercase tracking-wider ${darkMode ? 'text-slate-600' : 'text-slate-400'}`}>
        {getPhraseLabel(type)}
      </div>
    </div>
  );
}
