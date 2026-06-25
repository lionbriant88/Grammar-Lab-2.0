import { useState, useEffect, useCallback } from 'react';
import type { SentenceAnalysis, AnatomyChunk, ChunkRole } from '../../types';
import type { SelectionEvent } from '../../types/selection';
import { getRoleLabel } from '../../utils/roleColor';
import ChunkBlocks, { type EditableChunk } from './ChunkBlocks';
import EditToolbar from './EditToolbar';
import ClauseBreakdown from './ClauseBreakdown';

export interface AnatomySceneProps {
  analysis: SentenceAnalysis | null;
  darkMode: boolean;
  onAnalyzeAnatomy: (sentence: string) => void;
  isAnalyzing: boolean;
  error: string | null;
  // M4c Task 23: passed in by App.tsx; wired by Task 24
  onSelectNode?: (sel: SelectionEvent) => void;
}

/** 后端 AnatomyChunk → 可编辑 EditableChunk(把 text 拆成词) */
function toEditable(c: AnatomyChunk): EditableChunk {
  return {
    id: c.id,
    role: c.role,
    words: c.text.split(/\s+/).filter(Boolean),
    label: c.label,
    subordinate: c.subordinate,
  };
}

export default function AnatomyScene({
  analysis,
  darkMode,
  onAnalyzeAnatomy,
  isAnalyzing,
  error,
}: AnatomySceneProps) {
  const backend = analysis?.anatomy?.backend;

  const [isEditing, setIsEditing] = useState(false);
  const [workingChunks, setWorkingChunks] = useState<EditableChunk[]>([]);
  const [history, setHistory] = useState<EditableChunk[][]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 后端数据变化(新分析)时,重置本地编辑状态
  useEffect(() => {
    if (backend) {
      setWorkingChunks(backend.chunks.map(toEditable));
      setHistory([]);
      setIsEditing(false);
      setSelectedId(null);
    }
  }, [backend]);

  // 若 analysis 存在但 anatomy 缺失,触发拉取(由 App 层也兜底)
  useEffect(() => {
    if (analysis && analysis.sentence && !analysis.anatomy && !isAnalyzing) {
      onAnalyzeAnatomy(analysis.sentence);
    }
  }, [analysis, isAnalyzing, onAnalyzeAnatomy]);

  // workingChunks 始终是当前展示版本:新分析到来时由上方 useEffect 从 backend 初始化,
  // 编辑只修改它,完成编辑后保留(不回退到 backend)。这样「完成」不会丢失编辑结果。
  // 「重置为自动」才会把 workingChunks 重新设为 backend 原始版本。

  /** 进入编辑前快照入栈 */
  const pushHistory = useCallback((next: EditableChunk[]) => {
    setHistory((h) => [...h, workingChunks]);
    setWorkingChunks(next);
  }, [workingChunks]);

  const handleMoveWord = useCallback(
    (sourceId: string, wordIdx: number, targetId: string, insertIdx: number) => {
      const source = workingChunks.find((c) => c.id === sourceId);
      const target = workingChunks.find((c) => c.id === targetId);
      if (!source || !target || source.id === target.id) return;
      const word = source.words[wordIdx];
      if (!word) return;

      const next = workingChunks.map((c) => ({ ...c, words: [...c.words] }));
      // 从 source 移除
      const srcNext = next.find((c) => c.id === sourceId)!;
      srcNext.words.splice(wordIdx, 1);
      // 插入 target
      const tgtNext = next.find((c) => c.id === targetId)!;
      const idx = Math.min(insertIdx, tgtNext.words.length);
      tgtNext.words.splice(idx, 0, word);
      // source 清空则移除(标点块除外——标点不会被拖)
      const filtered = next.filter((c) => c.words.length > 0 || c.role === 'punct');

      pushHistory(filtered);
    },
    [workingChunks, pushHistory]
  );

  const handleSetRole = useCallback(
    (role: ChunkRole) => {
      if (!selectedId) return;
      const next = workingChunks.map((c) =>
        c.id === selectedId ? { ...c, role, label: getRoleLabel(role) } : c
      );
      pushHistory(next);
    },
    [selectedId, workingChunks, pushHistory]
  );

  const handleUndo = useCallback(() => {
    setHistory((h) => {
      if (h.length === 0) return h;
      const prev = h[h.length - 1];
      setWorkingChunks(prev);
      return h.slice(0, -1);
    });
  }, []);

  const handleReset = useCallback(() => {
    if (backend) {
      setHistory((h) => (h.length === 0 ? h : [...h, workingChunks]));
      setWorkingChunks(backend.chunks.map(toEditable));
      setSelectedId(null);
    }
  }, [backend, workingChunks]);

  const handleFinish = useCallback(() => {
    setIsEditing(false);
    setSelectedId(null);
  }, []);

  // ---- 渲染分支 ----

  // 空态:还没分析过
  if (!analysis) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center py-20 text-slate-400">
          <p className="text-lg">句剖析分析 - 等待分析</p>
          <p className="text-sm mt-2">输入句子后点击"开始分析"查看语义块结构</p>
        </div>
      </div>
    );
  }

  // loading
  if (isAnalyzing && !backend) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center py-20 text-slate-400">
          <p className="text-lg">正在分析句子结构...</p>
        </div>
      </div>
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

  // 有数据但 chunks 空(后端警告)
  if (backend && backend.chunks.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="p-6 rounded-2xl border border-orange-200 bg-orange-50 text-orange-800">
          <h3 className="font-bold mb-2">分析警告</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {backend.summary.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  if (!backend) return null;

  const selectedChunk = workingChunks.find((c) => c.id === selectedId) || null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 语义块主视图(顶部右侧带编辑开关) */}
      <div className="flex items-center justify-between -mb-2">
        <h2 className={`text-base font-bold ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
          🔍 语义块解剖
        </h2>
        <button
          onClick={() => {
            if (isEditing) {
              handleFinish();
            } else {
              setIsEditing(true);
            }
          }}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            isEditing
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : darkMode
              ? 'border border-slate-600 text-slate-200 hover:bg-slate-700'
              : 'border border-slate-300 text-slate-700 hover:bg-slate-100'
          }`}
        >
          {isEditing ? '✓ 完成编辑' : '✏️ 编辑'}
        </button>
      </div>

      {isEditing && (
        <EditToolbar
          darkMode={darkMode}
          selectedRole={selectedChunk?.role ?? null}
          onSetRole={handleSetRole}
          canUndo={history.length > 0}
          onUndo={handleUndo}
          onReset={handleReset}
          onFinish={handleFinish}
        />
      )}

      <ChunkBlocks
        chunks={workingChunks}
        darkMode={darkMode}
        isEditing={isEditing}
        selectedId={selectedId}
        onSelectChunk={setSelectedId}
        onMoveWord={handleMoveWord}
      />

      {/* 分句分解(只读,展示系统分析的主从结构) */}
      <ClauseBreakdown clauses={backend.clauses} darkMode={darkMode} />

      {isEditing && (
        <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          提示:拖动词语到其它色块可调整成分归属;选中一个块后可在顶部改角色。分句结构卡为系统分析参考,不随编辑更新。
        </p>
      )}
    </div>
  );
}
