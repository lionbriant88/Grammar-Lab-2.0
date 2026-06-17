import { useState, useEffect, useCallback } from 'react';
import type { SentenceAnalysis, PhraseNodeInfo } from '../../types';
import ExtensionLibrary from './ExtensionLibrary';
import SentenceCanvas from './SentenceCanvas';
import ExpansionInspector from './ExpansionInspector';
import ExpansionTree from './ExpansionTree';

export interface ExpandSceneProps {
  analysis: SentenceAnalysis | null;
  darkMode: boolean;
  onAnalyzeExpansion: (sentence: string) => void;
  onApplyExpansion: (sentence: string, phraseId: string, templateId: string) => void;  // M3a+1
  onUndoExpansion: () => void;  // M3a+1
  onRedoExpansion: () => void;  // M3a+1
  expansionCurrentIndex: number;  // M3a+1
  expansionHistoryLength: number;  // M3a+1
  isAnalyzing: boolean;
  error: string | null;
}

export default function ExpandScene({
  analysis,
  darkMode,
  onAnalyzeExpansion,
  onApplyExpansion,
  onUndoExpansion,
  onRedoExpansion,
  expansionCurrentIndex,
  expansionHistoryLength,
  isAnalyzing,
  error,
}: ExpandSceneProps) {
  const backend = analysis?.expansion?.backend;

  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    setHighlightedId(null);
  }, [backend]);

  useEffect(() => {
    if (analysis && analysis.sentence && !analysis.expansion && !isAnalyzing) {
      onAnalyzeExpansion(analysis.sentence);
    }
  }, [analysis, isAnalyzing, onAnalyzeExpansion]);

  const handleSelectPhrase = useCallback((phraseId: string) => {
    setHighlightedId(phraseId);
  }, []);

  const handleApply = useCallback(async (phraseId: string, templateId: string) => {
    if (!backend) return;
    setIsApplying(true);
    try {
      await onApplyExpansion(backend.sentence, phraseId, templateId);
      setHighlightedId(phraseId);
    } finally {
      setIsApplying(false);
    }
  }, [backend, onApplyExpansion]);

  // 空态 / loading / error / warnings 分支保持 M3a
  if (!analysis) {
    return (
      <Centered darkMode={darkMode}>
        <p className="text-lg">句扩展分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析",查看句子如何一步步扩展</p>
      </Centered>
    );
  }

  if (isAnalyzing && !backend) {
    return (
      <Centered darkMode={darkMode}>
        <p className="text-lg">正在分析短语结构...</p>
      </Centered>
    );
  }

  if (error && !backend) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="p-6 rounded-2xl border border-red-200 bg-red-50 text-red-800">
          <h3 className="font-bold mb-2">分析失败</h3>
          <p className="text-sm">{error}</p>
          <p className="text-sm mt-3 opacity-70">请确保后端服务正在运行 (python backend/app.py)</p>
        </div>
      </div>
    );
  }

  if (backend && backend.phrases.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="p-6 rounded-2xl border border-orange-200 bg-orange-50 text-orange-800">
          <h3 className="font-bold mb-2">分析警告</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {backend.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  if (!backend) return null;

  const phrases: PhraseNodeInfo[] = backend.phrases;
  const selectedPhrase = highlightedId ? phrases.find((p) => p.id === highlightedId) ?? null : null;
  const canUndo = expansionCurrentIndex > 0;
  const canRedo = expansionCurrentIndex < expansionHistoryLength - 1;

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between -mb-2">
        <h2 className={`text-base font-bold ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
          🧱 句扩展
        </h2>
        <span className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          写路径 · M3a+1.3
        </span>
      </div>

      <div className="grid grid-cols-12 gap-4 items-start">
        <div className="col-span-12 lg:col-span-3">
          <ExtensionLibrary darkMode={darkMode} />
        </div>

        <div className="col-span-12 lg:col-span-5 space-y-4">
          <SentenceCanvas
            phrases={phrases}
            darkMode={darkMode}
            menuOpenFor={null}
            highlightedId={highlightedId}
            onToggleMenu={handleSelectPhrase}
          />
          <ExpansionInspector
            phrase={selectedPhrase}
            darkMode={darkMode}
            onApply={(templateId) => highlightedId && handleApply(highlightedId, templateId)}
            isApplying={isApplying}
          />
        </div>

        <div className="col-span-12 lg:col-span-4">
          <ExpansionTree
            sentence={backend.sentence}
            phrases={phrases}
            darkMode={darkMode}
            onSelectPhrase={handleSelectPhrase}
            highlightedId={highlightedId}
          />
        </div>
      </div>

      {/* 占位 Undo/Redo(M3a+1.4 替换为 timeline 之外,简单按钮先保留) */}
      <div className={`flex items-center gap-2 mt-4 text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        <button
          type="button"
          disabled={!canUndo}
          onClick={onUndoExpansion}
          className={`px-2 py-1 rounded ${
            canUndo ? darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100' : 'opacity-50 cursor-not-allowed'
          }`}
        >
          ↶ 撤销
        </button>
        <button
          type="button"
          disabled={!canRedo}
          onClick={onRedoExpansion}
          className={`px-2 py-1 rounded ${
            canRedo ? darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100' : 'opacity-50 cursor-not-allowed'
          }`}
        >
          ↷ 重做
        </button>
        <span>已应用 {expansionCurrentIndex} 个扩展</span>
      </div>

      {backend.warnings.length > 0 && (
        <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          提示:{backend.warnings.join('; ')}
        </p>
      )}
    </div>
  );
}

function Centered({ darkMode, children }: { darkMode: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className={`text-center py-20 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`}>{children}</div>
    </div>
  );
}
