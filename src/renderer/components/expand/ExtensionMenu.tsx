import type { PhraseNodeInfo, ExpansionCandidate } from '../../types';

export interface ExtensionMenuProps {
  phrase: PhraseNodeInfo;
  darkMode: boolean;
  /** 关闭浮层 */
  onClose: () => void;
  /** 选中模板 → 触发 applyExpansion(传入 templateId)。M3a+1:由父组件 (ExpandScene) 传 onApply。 */
  onApply: (templateId: string) => void;
  /** 是否正在 apply 中(显示 loading) */
  isApplying: boolean;
}

/**
 * [+] 浮层:M3a+1.2 起可点 chip 直接 apply(应用扩展按钮 = 单个 chip 即应用)。
 * M3a+1.3 起,该浮层被重写为 ExpansionInspector.tsx;此文件保留以兼容回退。
 */
export default function ExtensionMenu({ phrase, darkMode, onClose, onApply, isApplying }: ExtensionMenuProps) {
  const available = phrase.candidates.filter((c) => c.available);

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
          <KindSection
            key={c.kind}
            candidate={c}
            darkMode={darkMode}
            isApplying={isApplying}
            onSelect={(templateId) => onApply(templateId)}
          />
        ))}
        {available.length === 0 && (
          <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
            该短语暂无可应用的词级扩展。
          </p>
        )}
      </div>
    </div>
  );
}

function KindSection({
  candidate,
  darkMode,
  isApplying,
  onSelect,
}: {
  candidate: ExpansionCandidate;
  darkMode: boolean;
  isApplying: boolean;
  onSelect: (templateId: string) => void;
}) {
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
          <button
            key={t.template_id}
            type="button"
            disabled={isApplying}
            onClick={() => onSelect(t.template_id)}
            className={`rounded-lg border px-2 py-1.5 text-left transition-all ${
              isApplying
                ? darkMode
                  ? 'bg-slate-700/30 border-slate-700 cursor-not-allowed opacity-50'
                  : 'bg-slate-50 border-slate-200 cursor-not-allowed opacity-50'
                : darkMode
                ? 'bg-slate-700/40 border-slate-600 hover:bg-slate-600/60 hover:border-blue-400'
                : 'bg-slate-50 border-slate-200 hover:bg-blue-50 hover:border-blue-400'
            }`}
          >
            <div className={`text-sm font-semibold ${darkMode ? 'text-slate-100' : 'text-slate-800'}`}>
              {t.surface}
            </div>
            <div className={`text-[10px] ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              → {t.preview}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
