import { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import TimelineScene from './components/timeline/TimelineScene';
import AnatomyScene from './components/anatomy/AnatomyScene';
import ExpandScene from './components/expand/ExpandScene';
import { ExplainPanel } from './components/explain/ExplainPanel';
import { ExplainHistoryDrawer } from './components/explain/ExplainHistoryDrawer';
import { useHealthStore } from './stores/healthStore';
import type { SceneType } from './types';
import type { SelectionEvent } from './types/selection';
import { useAppState } from './state/appState';

function App() {
  const [activeScene, setActiveScene] = useState<SceneType>('timeline');
  const [darkMode, setDarkMode] = useState(false);
  const [inputText, setInputText] = useState('I usually get up at seven every morning.');
  const [state, actions] = useAppState();
  // M4c Task 23: shared selection state across scenes → ExplainPanel
  const [selection, setSelection] = useState<SelectionEvent | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const { health, refresh: refreshHealth } = useHealthStore();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // M3a+1.4: 键盘快捷键 - Undo/Redo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 只在 expand 场景且有 history 时响应
      if (activeScene !== 'expand' || state.expansionHistory.length === 0) return;

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

      // Undo: Cmd/Ctrl+Z (without Shift)
      if (ctrlOrCmd && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        actions.undoExpansion();
        return;
      }

      // Redo: Cmd/Ctrl+Shift+Z or Ctrl+Y
      if ((ctrlOrCmd && e.key === 'z' && e.shiftKey) || (e.ctrlKey && e.key === 'y')) {
        e.preventDefault();
        actions.redoExpansion();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeScene, state.expansionHistory.length, actions]);

  useEffect(() => {
    if (activeScene === 'anatomy' && state.currentAnalysis && !state.currentAnalysis.anatomy) {
      actions.analyzeAnatomy(state.currentAnalysis.sentence);
    }
  }, [activeScene, state.currentAnalysis, actions]);

  useEffect(() => {
    if (activeScene === 'expand' && state.currentAnalysis && !state.currentAnalysis.expansion) {
      actions.analyzeExpansion(state.currentAnalysis.sentence);
    }
  }, [activeScene, state.currentAnalysis, actions]);

  // M4c Task 23: kick off health check on mount + every 5 min
  useEffect(() => {
    refreshHealth();
    const t = setInterval(refreshHealth, 5 * 60 * 1000);
    return () => clearInterval(t);
  }, [refreshHealth]);

  // M4c Task 23: sentence for ExplainPanel (used as context input_sentence)
  const currentSentence = state.currentAnalysis?.sentence ?? '';

  const handleAnalyze = () => {
    actions.analyzeSentence(inputText);
    if (activeScene === 'anatomy') {
      actions.analyzeAnatomy(inputText);
    }
    if (activeScene === 'expand') {
      actions.analyzeExpansion(inputText);
    }
  };

  const renderScene = () => {
    switch (activeScene) {
      case 'timeline':
        return <TimelineScene analysis={state.currentAnalysis} darkMode={darkMode} onSelectNode={setSelection} />;
      case 'anatomy':
        return (
          <AnatomyScene
            analysis={state.currentAnalysis}
            darkMode={darkMode}
            onAnalyzeAnatomy={(s) => actions.analyzeAnatomy(s)}
            isAnalyzing={state.isLoading}
            error={state.error}
            onSelectNode={setSelection}
          />
        );
      case 'expand':
        return (
          <ExpandScene
            analysis={state.currentAnalysis}
            darkMode={darkMode}
            onAnalyzeExpansion={(s) => actions.analyzeExpansion(s)}
            onApplyExpansion={(s, p, t) => actions.applyExpansion(s, p, t)}
            onUndoExpansion={() => actions.undoExpansion()}
            onRedoExpansion={() => actions.redoExpansion()}
            onSelectVersion={(versionId) => {
              // 跳到任意版本:找到对应 index,模拟 Undo/Redo 到那里
              const idx = state.expansionHistory.findIndex((v) => v.version_id === versionId);
              if (idx < 0) return;
              if (idx < state.expansionCurrentIndex) {
                for (let i = state.expansionCurrentIndex; i > idx; i--) {
                  actions.undoExpansion();
                }
              } else if (idx > state.expansionCurrentIndex) {
                for (let i = state.expansionCurrentIndex; i < idx; i++) {
                  actions.redoExpansion();
                }
              }
            }}
            expansionCurrentIndex={state.expansionCurrentIndex}
            expansionHistoryLength={state.expansionHistory.length}
            expansionHistory={state.expansionHistory}
            isAnalyzing={state.isLoading}
            error={state.error}
            onSelectNode={setSelection}
          />
        );
      default:
        return <TimelineScene analysis={state.currentAnalysis} darkMode={darkMode} onSelectNode={setSelection} />;
    }
  };

  return (
    <MainLayout
      activeScene={activeScene}
      darkMode={darkMode}
      inputText={inputText}
      onSceneChange={setActiveScene}
      onDarkModeToggle={() => setDarkMode(!darkMode)}
      onInputChange={setInputText}
      onAnalyze={handleAnalyze}
      onClear={() => {
        setInputText('');
        actions.clearAnalysis();
      }}
    >
      {/* M4c Task 23: scene + ExplainPanel side-by-side, collapse on small screens */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-4 h-full">
        <div className="min-w-0">{renderScene()}</div>
        <aside className="lg:sticky lg:top-0 lg:max-h-[calc(100vh-1rem)] lg:overflow-y-auto">
          <ExplainPanel selection={selection} sentence={currentSentence} darkMode={darkMode} />
        </aside>
      </div>

      {/* M4c Task 23: floating health LED + history button (Header not modified) */}
      <button
        type="button"
        title={`${health.provider || ''} / ${health.model || ''} (${health.status})`}
        className="fixed top-3 right-16 z-50 p-1 rounded bg-white/80 dark:bg-slate-800/80 shadow"
        aria-label="AI health status"
      >
        <span
          className={
            health.status === 'ready' ? 'bg-green-500' :
            health.status === 'degraded' ? 'bg-yellow-500' :
            health.status === 'offline' ? 'bg-red-500' :
            'bg-slate-400'
          }
          style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%' }}
        />
      </button>
      <button
        type="button"
        onClick={() => setHistoryOpen(true)}
        className="fixed top-3 right-3 z-50 p-1 px-2 rounded bg-white/80 dark:bg-slate-800/80 shadow text-sm"
        aria-label="Open history"
      >
        🕘 History
      </button>

      <ExplainHistoryDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelect={(item) =>
          setSelection({
            scene: item.context.scene,
            node: {
              id: item.context.selected_node_id,
              type: item.context.node_type,
              data: item.context.selected_node,
            },
          })
        }
        darkMode={darkMode}
      />
    </MainLayout>
  );
}

export default App;
