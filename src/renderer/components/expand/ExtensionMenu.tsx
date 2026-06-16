import type { PhraseNodeInfo, ExpansionCandidate } from '../../types';

export interface ExtensionMenuProps {
  phrase: PhraseNodeInfo;
  darkMode: boolean;
  /** 关闭浮层 */
  onClose: () => void;
}

/**
 * [+] 浮层:列出该短语的可扩展候选(kind 分组 + 模板网格)。
 * M3a 只读:「应用」按钮 disabled + tooltip(提交功能 M3a+1 开放)。
 */
export default function ExtensionMenu({ phrase, darkMode, onClose }: ExtensionMenuProps) {
  const available = phrase.candidates.filter((c) => c.available);
  const locked = phrase.candidates.filter((c) => !c.available);

  return (
    <div
      className={`absolute z-30 top-full mt-2 left-0 w-72 rounded-xl border shadow-xl p-3 ${
        darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'
      }`}
      onClick={(e) => e.stopPropagation()}
    >
      {/* 头部 */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-bold ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>
          扩展「{phrase.text}」
        </span>
        <button
          type="button"
          onClick={onClose}
          className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
            darkMode ? 'text-slate-400 hover:bg-slate-700' : 'text-slate-500 hover:bg-slate-100'
          }`}
          aria-label="关闭"
        >
          ✕
        </button>
      </div>

      <div className="max-h-72 overflow-y-auto space-y-3 pr-0.5">
        {available.map((c) => (
          <KindSection key={c.kind} candidate={c} darkMode={darkMode} />
        ))}
        {available.length === 0 && (
          <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
            该短语暂无可应用的词级扩展。
          </p>
        )}

        {locked.length > 0 && (
          <div className={`pt-2 border-t ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
            <p className={`text-[10px] uppercase tracking-wider mb-1 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
              即将开放
            </p>
            <div className="flex flex-wrap gap-1">
              {locked.map((c) => (
                <span
                  key={c.kind}
                  className={`px-1.5 py-0.5 rounded text-[10px] ${
                    darkMode ? 'bg-slate-700/50 text-slate-500' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {c.kind_label_cn}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 底部提示:M3a 不做提交 */}
      <div className={`mt-3 pt-2 border-t ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
        <button
          type="button"
          disabled
          title="提交扩展功能将在 M3a+1 开放"
          className={`w-full px-3 py-1.5 rounded-lg text-xs font-medium cursor-not-allowed ${
            darkMode ? 'bg-slate-700/60 text-slate-500' : 'bg-slate-100 text-slate-400'
          }`}
        >
          应用扩展(M3a+1 开放)
        </button>
      </div>
    </div>
  );
}

function KindSection({ candidate, darkMode }: { candidate: ExpansionCandidate; darkMode: boolean }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className={`text-xs font-bold ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
          {candidate.kind_label_cn}
        </span>
        <span
          className={`px-1 py-0 rounded text-[9px] font-mono ${
            darkMode ? 'bg-slate-700/60 text-slate-400' : 'bg-slate-100 text-slate-500'
          }`}
        >
          L{candidate.level}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        {candidate.templates.map((t) => (
          <div
            key={t.template_id}
            className={`rounded-lg border px-2 py-1.5 ${
              darkMode ? 'bg-slate-700/40 border-slate-600' : 'bg-slate-50 border-slate-200'
            }`}
          >
            <div className={`text-sm font-semibold ${darkMode ? 'text-slate-100' : 'text-slate-800'}`}>
              {t.surface}
            </div>
            <div className={`text-[10px] ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              → {t.preview}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
