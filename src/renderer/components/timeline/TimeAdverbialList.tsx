import { getZoneColorClass } from '../../utils/zoneColor';
import type { BackendTimeAdverbial } from '../../types';

interface TimeAdverbialListProps {
  adverbials: BackendTimeAdverbial[];
  darkMode: boolean;
  onAdverbialClick?: (id: string) => void;
}

// 语义类型中文映射
const SEMANTIC_TYPE_LABELS: Record<BackendTimeAdverbial['semantic_type'], string> = {
  past_point: '过去时间点',
  present_point: '现在时间点',
  future_point: '将来时间点',
  duration: '持续时长',
  since_start: '起始时间',
  frequency: '频率',
  reference_clause: '从句标记',
};

export default function TimeAdverbialList({ adverbials, darkMode, onAdverbialClick }: TimeAdverbialListProps) {
  if (adverbials.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h4 className={`text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        时间状语
      </h4>
      <div className="flex flex-wrap gap-2">
        {adverbials.map((adv) => (
          <button
            key={adv.id}
            onClick={() => onAdverbialClick?.(adv.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${getZoneColorClass(adv.time_zone, darkMode)} hover:opacity-80`}
            title={SEMANTIC_TYPE_LABELS[adv.semantic_type]}
          >
            <span className="font-semibold">{adv.surface}</span>
            <span className="ml-1 opacity-70">({SEMANTIC_TYPE_LABELS[adv.semantic_type]})</span>
          </button>
        ))}
      </div>
    </div>
  );
}
