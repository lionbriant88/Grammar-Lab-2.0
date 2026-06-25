import { useState } from 'react';
import TimelineChart from './TimelineChart';
import VerbDetailCard from './VerbDetailCard';
import TimeAdverbialList from './TimeAdverbialList';
import type { SentenceAnalysis } from '../../types';
import type { SelectionEvent } from '../../types/selection';

interface TimelineSceneProps {
  analysis: SentenceAnalysis | null;
  darkMode: boolean;
  // M4c Task 23: passed in by App.tsx; wired by Task 24
  onSelectNode?: (sel: SelectionEvent) => void;
}

export default function TimelineScene({ analysis, darkMode, onSelectNode }: TimelineSceneProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // 获取后端数据
  const backend = analysis?.tenses?.backend;
  const verbs = backend?.verbs || [];
  const adverbials = backend?.timeAdverbials || [];
  const timelineNodes = backend?.timeline?.nodes || [];
  const warnings = backend?.summary?.warnings || [];

  // 获取选中的动词
  const selectedVerb = verbs.find((v) => v.id === selectedNodeId) || null;

  // 错误/空态处理
  if (!analysis) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center py-20 text-slate-400">
          <p className="text-lg">时间轴分析 - 等待分析</p>
          <p className="text-sm mt-2">输入句子后点击"开始分析"查看时态时间轴</p>
        </div>
      </div>
    );
  }

  // 有警告但没有动词
  if (verbs.length === 0 && warnings.length > 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className={`p-6 rounded-2xl border border-orange-200 bg-orange-50 text-orange-800`}>
          <h3 className="font-bold mb-2">分析警告</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
          <p className="text-sm mt-3 opacity-70">
            提示：当前使用基于规则的启发式分析器，识别能力有限。后续将接入 spaCy 进行更精确的分析。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 时间状语条 */}
      {adverbials.length > 0 && (
        <TimeAdverbialList
          adverbials={adverbials}
          darkMode={darkMode}
          onAdverbialClick={(id) => {
            // 找到该时间状语关联的动词并高亮（基于时区匹配）
            const clickedAdverbial = adverbials.find((a) => a.id === id);
            if (clickedAdverbial) {
              const relatedVerb = verbs.find((v) => v.time_zone === clickedAdverbial.time_zone);
              if (relatedVerb) {
                setSelectedNodeId(relatedVerb.id);
              }
            }
          }}
        />
      )}

      {/* 时间轴 */}
      <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
        <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
          时态时间轴
        </h3>
        <TimelineChart
          nodes={timelineNodes}
          darkMode={darkMode}
          onNodeClick={(verbId) => {
            setSelectedNodeId(verbId);
            const verb = verbs.find((v) => v.id === verbId);
            if (verb) {
              onSelectNode?.({
                scene: 'timeline',
                node: {
                  id: `verb-${verbId}`,
                  type: 'tense',
                  data: { verb: verb.surface, tense: verb.tense, position: verb.span[0] },
                },
              });
            }
          }}
          selectedNodeId={selectedNodeId || undefined}
        />
      </div>

      {/* 动词详情卡 */}
      <VerbDetailCard
        verb={selectedVerb}
        darkMode={darkMode}
        sentence={backend?.sentence || analysis.sentence || ''}
      />

      {/* 摘要 */}
      {backend?.summary && (
        <div className={`p-4 rounded-xl border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-slate-50 border-slate-200'}`}>
          <div className="flex items-center justify-between text-sm">
            <span className={darkMode ? 'text-slate-400' : 'text-slate-500'}>识别动词数</span>
            <span className={`font-bold ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
              {backend.summary.supportedVerbCount} / {backend.summary.verbCount}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className={darkMode ? 'text-slate-400' : 'text-slate-500'}>主要时态</span>
            <span className={`font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
              {backend.summary.primaryTense}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
