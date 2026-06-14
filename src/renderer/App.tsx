import { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import TimelineScene from './components/timeline/TimelineScene';
import AnatomyScene from './components/anatomy/AnatomyScene';
import ExpandScene from './components/expand/ExpandScene';
import type { SceneType } from './types';
import { useAppState } from './state/appState';

function App() {
  const [activeScene, setActiveScene] = useState<SceneType>('timeline');
  const [darkMode, setDarkMode] = useState(false);
  const [inputText, setInputText] = useState('I usually get up at seven every morning.');
  const [state, actions] = useAppState();

  // 暗黑模式切换
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // 切到句剖析场景且该句尚未分析过句剖析时,自动拉取 anatomy 数据
  useEffect(() => {
    if (activeScene === 'anatomy' && state.currentAnalysis && !state.currentAnalysis.anatomy) {
      actions.analyzeAnatomy(state.currentAnalysis.sentence);
    }
  }, [activeScene, state.currentAnalysis, actions]);

  const handleAnalyze = () => {
    actions.analyzeSentence(inputText);
    // 句剖析场景下,同步拉取 anatomy(基于当前输入框句子)
    if (activeScene === 'anatomy') {
      actions.analyzeAnatomy(inputText);
    }
  };

  const renderScene = () => {
    switch (activeScene) {
      case 'timeline':
        return <TimelineScene analysis={state.currentAnalysis} darkMode={darkMode} />;
      case 'anatomy':
        return (
          <AnatomyScene
            analysis={state.currentAnalysis}
            darkMode={darkMode}
            onAnalyzeAnatomy={(s) => actions.analyzeAnatomy(s)}
            isAnalyzing={state.isLoading}
            error={state.error}
          />
        );
      case 'expand':
        return <ExpandScene analysis={state.currentAnalysis} />;
      default:
        return <TimelineScene analysis={state.currentAnalysis} darkMode={darkMode} />;
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
      {renderScene()}
    </MainLayout>
  );
}

export default App;
