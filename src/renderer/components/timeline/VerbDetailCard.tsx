import { getTenseLabelCn, getZoneLabelCn, getAspectLabelCn } from '../../utils/tenseLabel';
import { getZoneColorClass } from '../../utils/zoneColor';
import type { BackendVerb } from '../../types';

interface VerbDetailCardProps {
  verb: BackendVerb | null;
  darkMode: boolean;
  sentence: string;
}

export default function VerbDetailCard({ verb, darkMode, sentence }: VerbDetailCardProps) {
  if (!verb) {
    return (
      <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'}`}>
        <p className={`text-center text-sm ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          点击时间轴上的节点查看详情
        </p>
      </div>
    );
  }

  // 高亮句子中的动词短语
  const getHighlightedSentence = () => {
    if (!verb.span || verb.span.length !== 2) return sentence;
    const [start, end] = verb.span;
    return (
      <>
        {sentence.slice(0, start)}
        <mark className={`px-1 rounded ${darkMode ? 'bg-blue-500/30 text-blue-300' : 'bg-blue-100 text-blue-800'}`}>
          {sentence.slice(start, end)}
        </mark>
        {sentence.slice(end)}
      </>
    );
  };

  return (
    <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'} animate-fade-in`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-slate-800'}`}>
            {verb.surface}
          </h3>
          <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
            原形: {verb.lemma}
          </p>
        </div>
        <div className={`px-3 py-1.5 rounded-lg text-sm font-semibold border ${getZoneColorClass(verb.time_zone, darkMode)}`}>
          {getZoneLabelCn(verb.time_zone)}
        </div>
      </div>

      <div className="space-y-3">
        <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
          <div className="flex justify-between items-center">
            <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>时态</span>
            <span className={`text-sm font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
              {getTenseLabelCn(verb.tense)}
            </span>
          </div>
        </div>

        <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
          <div className="flex justify-between items-center">
            <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>体</span>
            <span className={`text-sm font-bold ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>
              {getAspectLabelCn(verb.aspect)}
            </span>
          </div>
        </div>

        <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
          <div className="flex justify-between items-center">
            <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>完整短语</span>
            <span className={`text-sm font-mono ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
              {verb.phrase}
            </span>
          </div>
        </div>

        <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
          <div className="flex justify-between items-center">
            <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>置信度</span>
            <span className={`text-sm font-bold ${darkMode ? 'text-orange-400' : 'text-orange-600'}`}>
              {(verb.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {verb.subject_text && (
          <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
            <div className="flex justify-between items-center">
              <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>主语</span>
              <span className={`text-sm ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>
                {verb.subject_text}
              </span>
            </div>
          </div>
        )}

        <div className={`p-3 rounded-lg ${darkMode ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
          <span className={`text-xs font-semibold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>句子位置</span>
          <p className={`text-sm mt-1 font-mono ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>
            {getHighlightedSentence()}
          </p>
        </div>
      </div>
    </div>
  );
}
