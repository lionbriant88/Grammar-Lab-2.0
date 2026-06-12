import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import type { SceneType } from '../../types';

interface MainLayoutProps {
  activeScene: SceneType;
  darkMode: boolean;
  inputText: string;
  onSceneChange: (scene: SceneType) => void;
  onDarkModeToggle: () => void;
  onInputChange: (text: string) => void;
  onAnalyze: () => void;
  onClear: () => void;
  children: React.ReactNode;
}

export default function MainLayout({
  activeScene,
  darkMode,
  inputText,
  onSceneChange,
  onDarkModeToggle,
  onInputChange,
  onAnalyze,
  onClear,
  children
}: MainLayoutProps) {
  return (
    <div className={`min-h-screen flex flex-col md:flex-row transition-colors duration-300 ${
      darkMode ? 'bg-slate-950 text-slate-100' : 'bg-[#f4f7fc] text-slate-800'
    }`}>
      {/* 移动端顶部状态栏 */}
      <div className={`md:hidden flex items-center justify-between p-4 border-b ${
        darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
      }`}>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-lg shadow">
            <svg className="w-6 h-6 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <span className="font-bold text-base tracking-wide">Grammar Lab</span>
        </div>
        <button
          onClick={onDarkModeToggle}
          className={`p-2 rounded-lg border transition-all ${
            darkMode ? 'bg-slate-800 border-slate-700 text-yellow-400' : 'bg-slate-50 border-slate-200 text-slate-500'
          }`}
        >
          {darkMode ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m12.728 12.728l.707.707M12 7a5 5 0 100 10 5 5 0 000-10z" />
            </svg>
          )}
        </button>
      </div>

      {/* 侧边栏 - 桌面端 */}
      <div className="hidden md:flex">
        <Sidebar
          activeScene={activeScene}
          onSceneChange={onSceneChange}
          darkMode={darkMode}
          onDarkModeToggle={onDarkModeToggle}
        />
      </div>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col overflow-y-auto min-w-0">
        <Header
          activeScene={activeScene}
          inputText={inputText}
          onInputChange={onInputChange}
          onAnalyze={onAnalyze}
          onClear={onClear}
          darkMode={darkMode}
        />

        {/* 内容渲染区 */}
        <div className="p-6 flex-1 min-h-0">
          {children}
        </div>
      </main>
    </div>
  );
}
