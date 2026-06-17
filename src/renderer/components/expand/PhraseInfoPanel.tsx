import type { PhraseNodeInfo } from '../../types';
import { featuresToBadges } from '../../utils/phraseColor';

export interface PhraseInfoPanelProps {
  phrase: PhraseNodeInfo | null;
  darkMode: boolean;
}

const ROLE_LABELS_CN: Record<string, string> = {
  subject: '主语',
  predicate: '谓语',
  object: '宾语',
  adverbial: '状语',
  other: '其它',
};

export default function PhraseInfoPanel({ phrase, darkMode }: PhraseInfoPanelProps) {
  if (!phrase) {
    return (
      <div
        className={`p-5 rounded-2xl border ${
          darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
        }`}
      >
        <h3 className={`text-sm font-bold uppercase tracking-wider mb-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
          短语信息
        </h3>
        <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          选中短语后查看详情
        </p>
      </div>
    );
  }

  const role = ROLE_LABELS_CN[phrase.syntactic_role] ?? phrase.syntactic_role;
  const features = phrase.features as Record<string, unknown>;

  return (
    <div
      className={`p-5 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <h3 className={`text-sm font-bold uppercase tracking-wider mb-3 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        短语信息
      </h3>

      <dl className="space-y-2 text-xs">
        <Row label="当前短语" value={phrase.text} darkMode={darkMode} />
        <Row label="短语类型" value={phrase.type} darkMode={darkMode} />
        <Row label="中心词" value={phrase.head_token_text} darkMode={darkMode} />
        <Row label="POS" value={phrase.head_pos} darkMode={darkMode} />
        <Row label="语法角色" value={role} darkMode={darkMode} />
        {phrase.type === 'VP' && features.tense ? (
          <Row label="时态" value={String(features.tense)} darkMode={darkMode} />
        ) : null}
      </dl>

      {Object.keys(features).length > 0 && (
        <div className="mt-3">
          <p className={`text-[10px] uppercase tracking-wider mb-1.5 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
            特征
          </p>
          <div className="flex flex-wrap gap-1">
            {featuresToBadges(phrase.type as any, features).map((tag) => (
              <span
                key={tag}
                className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                  darkMode ? 'bg-emerald-500/20 text-emerald-300' : 'bg-emerald-100 text-emerald-700'
                }`}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, darkMode }: { label: string; value: string; darkMode: boolean }) {
  return (
    <div className="flex items-baseline gap-2">
      <dt className={`flex-shrink-0 w-16 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>{label}</dt>
      <dd className={`font-mono ${darkMode ? 'text-slate-200' : 'text-slate-800'}`}>{value}</dd>
    </div>
  );
}
