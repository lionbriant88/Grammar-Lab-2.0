import React, { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import TimelineScene from './components/timeline/TimelineScene';
import AnatomyScene from './components/anatomy/AnatomyScene';
import ExpandScene from './components/expand/ExpandScene';
import type { SceneType } from './types';

function App() {
  const [activeScene, setActiveScene] = useState<SceneType>('timeline');
  const [darkMode, setDarkMode] = useState(false);
  const [inputText, setInputText] = useState('The book that I bought yesterday is very interesting.');

  // 暗黑模式切换
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const renderScene = () => {
    switch (activeScene) {
      case 'timeline':
        return <TimelineScene />;
      case 'anatomy':
        return <AnatomyScene />;
      case 'expand':
        return <ExpandScene />;
      default:
        return <TimelineScene />;
    }
  };

  const handleAnalyze = () => {
    console.log('Analyzing sentence:', inputText);
    // TODO: 实现分析逻辑
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
      onClear={() => setInputText('')}
    >
      {renderScene()}
    </MainLayout>
  );
}

export default App;
