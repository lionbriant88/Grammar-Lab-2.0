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

  const handleAnalyze = () => {
    actions.analyzeSentence(inputText);
  };

  const renderScene = () => {
    switch (activeScene) {
      case 'timeline':
        return <TimelineScene analysis={state.currentAnalysis} darkMode={darkMode} />;
      case 'anatomy':
        return <AnatomyScene analysis={state.currentAnalysis} />;
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
