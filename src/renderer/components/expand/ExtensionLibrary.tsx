export interface ExtensionLibraryProps {
  darkMode: boolean;
}

/**
 * 左栏「扩展类型库」(M3a 占位,只展示)。
 * 列出 L1 已开放(adj/adv/number/degree)与 L2/L3 未开放项。点击无反应
 * (M3a+1 才接左侧面板的拖入式扩展)。
 */
const L1_KINDS = [
  { cn: '形容词', en: 'adjective' },
  { cn: '副词', en: 'adverb' },
  { cn: '数词', en: 'number' },
  { cn: '程度副词', en: 'degree_adverb' },
];
const L2_KINDS = [
  { cn: '介词短语', en: 'prepositional_phrase' },
  { cn: '分词短语', en: 'participle_phrase' },
  { cn: '不定式', en: 'infinitive_phrase' },
];
const L3_KINDS = [
  { cn: '定语从句', en: 'relative_clause' },
  { cn: '状语从句', en: 'adverbial_clause' },
  { cn: '名词性从句', en: 'noun_clause' },
];

export default function ExtensionLibrary({ darkMode }: ExtensionLibraryProps) {
  return (
    <div
      className={`p-5 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <h3
        className={`text-sm font-bold uppercase tracking-wider mb-3 ${
          darkMode ? 'text-slate-400' : 'text-slate-500'
        }`}
      >
        扩展类型库
      </h3>

      <KindGroup title="L1 · 词级" subtitle="已开放" kinds={L1_KINDS} darkMode={darkMode} available />
      <KindGroup title="L2 · 短语级" subtitle="未开放" kinds={L2_KINDS} darkMode={darkMode} available={false} />
      <KindGroup title="L3 · 从句级" subtitle="未开放" kinds={L3_KINDS} darkMode={darkMode} available={false} />
    </div>
  );
}

function KindGroup({
  title,
  subtitle,
  kinds,
  darkMode,
  available,
}: {
  title: string;
  subtitle: string;
  kinds: { cn: string; en: string }[];
  darkMode: boolean;
  available: boolean;
}) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`text-xs font-bold ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>{title}</span>
        <span
          className={`px-1.5 py-0 rounded text-[9px] ${
            available
              ? darkMode
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-emerald-100 text-emerald-700'
              : darkMode
              ? 'bg-slate-700/60 text-slate-500'
              : 'bg-slate-100 text-slate-400'
          }`}
        >
          {subtitle}
        </span>
      </div>
      <div className="space-y-1">
        {kinds.map((k) => (
          <div
            key={k.en}
            className={`flex items-center justify-between rounded-lg px-2 py-1 text-xs ${
              available
                ? darkMode
                  ? 'bg-slate-800/60 text-slate-300'
                  : 'bg-slate-50 text-slate-600'
                : darkMode
                ? 'bg-slate-800/30 text-slate-600'
                : 'bg-slate-50 text-slate-400'
            }`}
          >
            <span>{k.cn}</span>
            <span className="text-[9px] font-mono opacity-70">{k.en}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
