import { useState } from 'react';
import type { SentenceVersion } from '../../types';

export interface ExpansionTimelineProps {
  versions: SentenceVersion[];
  currentIndex: number;
  darkMode: boolean;
  onSelectVersion: (versionId: string) => void;
  onUndo: () => void;
  onRedo: () => void;
}

/**
 * 底栏纵向 timeline(spec §4.6):
 * - 横向两行布局
 * - 第一行 4 字段
 * - 第二行 timeline(展开/折叠,默认折叠)
 */
export default function ExpansionTimeline({
  versions,
  currentIndex,
  darkMode,
  onSelectVersion,
  onUndo,
  onRedo,
}: ExpansionTimelineProps) {
  const [expanded, setExpanded] = useState(false);
  const canUndo = currentIndex > 0;
  const canRedo = currentIndex < versions.length - 1;
  const current = versions[currentIndex];

  return (
    <div
      className={`border-t ${
        darkMode ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      {/* 第一行:状态信息 + 按钮 */}
      <div
        className={`flex items-center gap-4 px-4 py-2 text-xs ${
          darkMode ? 'text-slate-400' : 'text-slate-500'
        }`}
      >
        <span className="font-mono truncate max-w-[300px]" title={current?.sentence ?? ''}>
          Sentence: {current?.sentence ?? '(无)'}
        </span>
        <span>短语: {current?.phrases.length ?? 0}</span>
        <span>
          可扩展: {current?.phrases.filter((p) => p.is_expandable).length ?? 0}
        </span>
        <span>State: Analysis completed</span>

        <div className="ml-auto flex items-center gap-2">
          <span>已应用 {currentIndex} 个扩展</span>
          <button
            type="button"
            disabled={!canUndo}
            onClick={onUndo}
            className={`px-2 py-0.5 rounded ${
              canUndo ? darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100' : 'opacity-50 cursor-not-allowed'
            }`}
          >
            ↶ Undo
          </button>
          <button
            type="button"
            disabled={!canRedo}
            onClick={onRedo}
            className={`px-2 py-0.5 rounded ${
              canRedo ? darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100' : 'opacity-50 cursor-not-allowed'
            }`}
          >
            ↷ Redo
          </button>
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className={`px-2 py-0.5 rounded ${
              darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'
            }`}
          >
            {expanded ? '▴ 折叠' : '▾ 历史'}
          </button>
        </div>
      </div>

      {/* 第二行:timeline 展开 */}
      {expanded && (
        <div
          className={`px-4 py-2 max-h-48 overflow-y-auto ${
            darkMode ? 'border-slate-800' : 'border-slate-200'
          }`}
        >
          {[...versions].reverse().map((v, i) => {
            const realIndex = versions.length - 1 - i;
            const isCurrent = realIndex === currentIndex;
            const action = v.action_summary;
            return (
              <button
                key={v.version_id}
                type="button"
                onClick={() => onSelectVersion(v.version_id)}
                className={`w-full text-left flex items-start gap-2 py-1 px-2 rounded ${
                  isCurrent
                    ? darkMode ? 'bg-slate-700' : 'bg-blue-50'
                    : darkMode ? 'hover:bg-slate-800' : 'hover:bg-slate-50'
                }`}
              >
                <span
                  className={`flex-shrink-0 mt-0.5 w-2.5 h-2.5 rounded-full ${
                    isCurrent ? 'bg-emerald-400' : darkMode ? 'bg-slate-600' : 'bg-slate-300'
                  }`}
                />
                <span className={`flex-shrink-0 font-mono text-[10px] ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                  v{realIndex}
                </span>
                <span className={`flex-1 text-xs font-mono ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
                  {v.sentence}
                </span>
                <span className={`flex-shrink-0 text-[10px] ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                  {action
                    ? `${action.kind_label_cn} ${action.template_surface}`
                    : '(原句)'}
                </span>
                <span className={`flex-shrink-0 text-[10px] font-mono ${darkMode ? 'text-slate-600' : 'text-slate-400'}`}>
                  {new Date(v.timestamp).toLocaleTimeString()}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
