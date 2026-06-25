import { useState } from 'react';
import type { PhraseNodeInfo, ExpansionCandidate, ExpansionTemplateInfo } from '../../types';
import { computeQuotas } from '../../utils/expansionQuota';

export interface ExpansionInspectorProps {
  phrase: PhraseNodeInfo | null;
  darkMode: boolean;
  onApply: (templateId: string) => void;
  /** M4c Task 24: emit SelectionEvent when a template chip is clicked */
  onSelectTemplate?: (template: ExpansionTemplateInfo, kind: string) => void;
  isApplying: boolean;
}

/**
 * 画布下方固定面板(替代 M3a 浮层 ExtensionMenu)。
 * Accordion 分组,chip 即应用,不弹二次确认。
 */
export default function ExpansionInspector({ phrase, darkMode, onApply, onSelectTemplate, isApplying }: ExpansionInspectorProps) {
  if (!phrase) {
    return (
      <div
        className={`p-6 rounded-2xl border ${
          darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
        }`}
      >
        <h3 className={`text-sm font-bold uppercase tracking-wider mb-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
          扩展选项
        </h3>
        <p className={`text-sm ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          选中画布中任一短语查看可扩展项
        </p>
      </div>
    );
  }

  const quotaMap = computeQuotas([phrase]);
  const phraseQuota = quotaMap[phrase.id] ?? {};

  return (
    <div
      className={`p-6 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <h3 className={`text-sm font-bold uppercase tracking-wider mb-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        扩展选项
      </h3>
      <p className={`text-xs mb-4 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
        选中短语: <span className="font-mono">{phrase.text}</span> ({phrase.type})
      </p>

      <div className="space-y-3">
        {phrase.candidates.map((c) => {
          // 配额检查
          const quota = phraseQuota[c.kind as keyof typeof phraseQuota];
          const reached = quota?.reached ?? false;
          return (
            <KindAccordion
              key={c.kind}
              candidate={c}
              darkMode={darkMode}
              isApplying={isApplying}
              quotaReached={reached}
              onApply={onApply}
              onSelectTemplate={onSelectTemplate}
            />
          );
        })}
        {phrase.candidates.length === 0 && (
          <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
            该短语暂无可扩展项。
          </p>
        )}
      </div>
    </div>
  );
}

function KindAccordion({
  candidate,
  darkMode,
  isApplying,
  quotaReached,
  onApply,
  onSelectTemplate,
}: {
  candidate: ExpansionCandidate;
  darkMode: boolean;
  isApplying: boolean;
  quotaReached: boolean;
  onApply: (templateId: string) => void;
  onSelectTemplate?: (template: ExpansionTemplateInfo, kind: string) => void;
}) {
  const [open, setOpen] = useState(candidate.available && !quotaReached);
  const available = candidate.available;

  return (
    <div className={`rounded-lg border ${darkMode ? 'border-slate-700' : 'border-slate-200'}`}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`w-full flex items-center justify-between px-3 py-2 ${
          darkMode ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'
        }`}
      >
        <div className="flex items-center gap-1.5">
          <span className="text-xs">{open ? '▼' : '▸'}</span>
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
        <div className="flex items-center gap-1.5">
          {!available && (
            <span className={`px-1.5 py-0 rounded text-[9px] ${darkMode ? 'bg-slate-700/50 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>
              未开放
            </span>
          )}
          {quotaReached && available && (
            <span className={`px-1.5 py-0 rounded text-[9px] ${darkMode ? 'bg-amber-500/20 text-amber-300' : 'bg-amber-100 text-amber-700'}`}>
              Maximum expansion reached
            </span>
          )}
        </div>
      </button>
      {open && (
        <div className="px-3 pb-3">
          {available && candidate.templates.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {candidate.templates.map((t) => (
                <TemplateChip
                  key={t.template_id}
                  template={t}
                  darkMode={darkMode}
                  disabled={isApplying || quotaReached}
                  onClick={() => {
                    onSelectTemplate?.(t, candidate.kind);
                    onApply(t.template_id);
                  }}
                />
              ))}
            </div>
          ) : (
            <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
              暂无可用模板。
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function TemplateChip({
  template,
  darkMode,
  disabled,
  onClick,
}: {
  template: ExpansionTemplateInfo;
  darkMode: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      title={`${template.surface} → ${template.preview}`}
      className={`rounded-lg border px-2.5 py-1 text-sm font-medium transition-all ${
        disabled
          ? darkMode
            ? 'bg-slate-800/40 border-slate-700 text-slate-500 cursor-not-allowed'
            : 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'
          : darkMode
          ? 'bg-slate-700/40 border-slate-600 text-slate-100 hover:bg-slate-600/60 hover:border-blue-400'
          : 'bg-slate-50 border-slate-200 text-slate-800 hover:bg-blue-50 hover:border-blue-400'
      }`}
    >
      {template.surface}
    </button>
  );
}
