import React from 'react';
import type { SceneType } from '../../types';

interface SidebarProps {
  activeScene: SceneType;
  onSceneChange: (scene: SceneType) => void;
  darkMode: boolean;
  onDarkModeToggle: () => void;
}

// 图标组件
const Icons = {
  Flask: () => (
    <svg className="w-6 h-6 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
    </svg>
  ),
  Clock: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Anatomy: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 11-4.243 0 3 3 0 014.243 0z" />
    </svg>
  ),
  Expand: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
    </svg>
  ),
  Moon: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
  ),
  Sun: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m12.728 12.728l.707.707M12 7a5 5 0 100 10 5 5 0 000-10z" />
    </svg>
  )
};

const menuItems: Array<{ id: SceneType; label: string; icon: React.FC }> = [
  { id: 'timeline', label: '时间轴分析', icon: Icons.Clock },
  { id: 'anatomy', label: '句剖析分析', icon: Icons.Anatomy },
  { id: 'expand', label: '句扩展分析', icon: Icons.Expand }
];

export default function Sidebar({ activeScene, onSceneChange, darkMode, onDarkModeToggle }: SidebarProps) {
  return (
    <aside className={`w-64 flex-shrink-0 flex flex-col justify-between border-r transition-all duration-300 ${
      darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
    }`}>
      <div>
        {/* Logo */}
        <div className={`p-6 flex items-center space-x-3 border-b ${darkMode ? 'border-slate-800' : ''}`}>
          <div className="p-2.5 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-xl shadow-md">
            <Icons.Flask />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-wide">Grammar Lab</h1>
            <p className="text-xs text-slate-400 font-medium">语法实验室</p>
          </div>
        </div>

        {/* 导航菜单 */}
        <nav className="px-4 py-6 space-y-1.5">
          <div className="pb-3 px-4 text-[10px] font-bold text-slate-400 tracking-wider uppercase">独立分析场景</div>

          {menuItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onSceneChange(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3.5 rounded-xl text-sm font-semibold transition-all ${
                  activeScene === item.id
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : `text-slate-500 ${darkMode ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`
                }`}
              >
                <IconComponent />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* 底部配置 */}
      <div className={`p-4 border-t space-y-3 ${darkMode ? 'border-slate-800' : 'border-slate-200'}`}>
        <div className="flex items-center justify-between px-2 text-xs text-slate-400">
          <span>自适应暗黑模式</span>
          <button
            onClick={onDarkModeToggle}
            className={`p-1.5 rounded-lg border transition-all ${
              darkMode ? 'bg-slate-800 border-slate-700 text-yellow-400' : 'bg-slate-50 border-slate-200 text-slate-500 hover:bg-slate-100'
            }`}
          >
            {darkMode ? <Icons.Moon /> : <Icons.Sun />}
          </button>
        </div>
        <div className={`p-4 rounded-2xl flex flex-col items-center justify-center text-center ${
          darkMode ? 'bg-slate-800/40' : 'bg-blue-50/50'
        }`}>
          <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider">Grammar Lab</span>
          <span className="text-[10px] text-slate-400 mt-1">100% 独立离线交互引擎</span>
        </div>
      </div>
    </aside>
  );
}
