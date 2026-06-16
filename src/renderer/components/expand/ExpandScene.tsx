import { useState, useEffect, useCallback } from 'react';
import type { SentenceAnalysis, PhraseNodeInfo } from '../../types';
import ExtensionLibrary from './ExtensionLibrary';
import SentenceCanvas from './SentenceCanvas';
import ExtensionMenu from './ExtensionMenu';
import ExpansionTree from './ExpansionTree';

export interface ExpandSceneProps {
  analysis: SentenceAnalysis | null;
  darkMode: boolean;
  onAnalyzeExpansion: (sentence: string) => void;
  isAnalyzing: boolean;
  error: string | null;
}

export default function ExpandScene({
  analysis,
  darkMode,
  onAnalyzeExpansion,
  isAnalyzing,
  error,
}: ExpandSceneProps) {
  const backend = analysis?.expansion?.backend;

  const [menuOpenFor, setMenuOpenFor] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  // 新分析到来时重置本地交互态
  useEffect(() => {
    setMenuOpenFor(null);
    setHighlightedId(null);
  }, [backend]);

  // 若 analysis 存在但 expansion 缺失,触发拉取(由 App 层也兜底)
  useEffect(() => {
    if (analysis && analysis.sentence && !analysis.expansion && !isAnalyzing) {
      onAnalyzeExpansion(analysis.sentence);
    }
  }, [analysis, isAnalyzing, onAnalyzeExpansion]);

  const handleToggleMenu = useCallback((phraseId: string) => {
    setMenuOpenFor((cur) => (cur === phraseId ? null : phraseId));
    setHighlightedId(phraseId);
  }, []);

  // 右栏点 kind 叶子 → 高亮中栏对应短语 [+](仅视觉联动,spec §4.2)
  const handleSelectPhraseFromTree = useCallback((phraseId: string) => {
    setHighlightedId(phraseId);
    // 若该短语可扩展,自动展开菜单,让用户立即看到候选
    setMenuOpenFor(phraseId);
  }, []);

  const handleCloseMenu = useCallback(() => {
    setMenuOpenFor(null);
  }, []);

  // ---- 渲染分支 ----

  // 空态
  if (!analysis) {
    return (
      <Centered darkMode={darkMode}>
        <p className="text-lg">句扩展分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析",查看句子如何一步步扩展</p>
      </Centered>
    );
  }

  // loading
  if (isAnalyzing && !backend) {
    return (
      <Centered darkMode={darkMode}>
        <p className="text-lg">正在分析短语结构...</p>
      </Centered>
    );
  }

  // error
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

  // 后端警告(空 phrases)
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
  const openPhrase = menuOpenFor ? phrases.find((p) => p.id === menuOpenFor) ?? null : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between -mb-2">
        <h2 className={`text-base font-bold ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
          🧱 句扩展
        </h2>
        <span className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          只读预览 · 提交扩展将在 M3a+1 开放
        </span>
      </div>

      <div className="grid grid-cols-12 gap-4 items-start">
        {/* 左栏:扩展类型库(占位) */}
        <div className="col-span-12 lg:col-span-3">
          <ExtensionLibrary darkMode={darkMode} />
        </div>

        {/* 中栏:句子画布 + [+] 浮层 */}
        <div className="col-span-12 lg:col-span-5">
          <div className="relative">
            <SentenceCanvas
              phrases={phrases}
              darkMode={darkMode}
              menuOpenFor={menuOpenFor}
              highlightedId={highlightedId}
              onToggleMenu={handleToggleMenu}
            />
            {openPhrase && (
              <ExtensionMenu phrase={openPhrase} darkMode={darkMode} onClose={handleCloseMenu} />
            )}
          </div>
        </div>

        {/* 右栏:短语结构图(标题=短语结构图,非成分句法树) */}
        <div className="col-span-12 lg:col-span-4">
          <ExpansionTree
            sentence={backend.sentence}
            phrases={phrases}
            darkMode={darkMode}
            onSelectPhrase={handleSelectPhraseFromTree}
            highlightedId={highlightedId}
          />
        </div>
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
