import React, { useState } from 'react';
import type { SceneType } from '../../types';

interface HeaderProps {
  activeScene: SceneType;
  inputText: string;
  onInputChange: (text: string) => void;
  onAnalyze: () => void;
  onClear: () => void;
  darkMode: boolean;
}

// 场景配置
const sceneConfig: Record<SceneType, { title: string; desc: string }> = {
  timeline: {
    title: '⏳ 动词时态 & 时间轴分析',
    desc: '拆解并定位句子中的每一个动词，并在时空维度进行精准定位'
  },
  anatomy: {
    title: '🔍 句子多阶解剖分析',
    desc: '通过色块、词性、层级结构还原图片最经典的解剖架构'
  },
  expand: {
    title: '🚀 递进式写作扩充工坊',
    desc: '将一个核心单词渐进扩充为主从复合的长难句型'
  }
};

// 图标组件
const SpeakerIcon = () => (
  <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
  </svg>
);

const ChevronDownIcon = () => (
  <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
);

export default function Header({ activeScene, inputText, onInputChange, onAnalyze, onClear, darkMode }: HeaderProps) {
  const [showPresetDropdown, setShowPresetDropdown] = useState(false);

  const presets = [
    { sentence: 'The book that I bought yesterday is very interesting.', desc: '包含定语从句' },
    { sentence: 'Although it was raining, they decided to go for a hike.', desc: '包含让步状语从句' }
  ];

  const handleSpeak = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(inputText);
      utterance.lang = 'en-US';
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  const selectPreset = (sentence: string) => {
    onInputChange(sentence);
    setShowPresetDropdown(false);
  };

  return (
    <header className={`p-6 border-b space-y-4 ${darkMode ? 'border-slate-800' : 'border-slate-200'}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{sceneConfig[activeScene].title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{sceneConfig[activeScene].desc}</p>
        </div>
      </div>

      {/* 输入控制区 */}
      <div className="relative">
        <div className={`p-3.5 rounded-2xl border shadow-sm flex flex-col md:flex-row items-center gap-3 transition-colors ${
          darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
        }`}>
          <div className="relative w-full flex-1 flex items-center">
            <input
              type="text"
              value={inputText}
              onChange={(e) => onInputChange(e.target.value)}
              placeholder="在此输入您的英语句子..."
              onKeyDown={(e) => e.key === 'Enter' && onAnalyze()}
              className={`w-full pl-4 pr-10 py-2.5 rounded-xl border text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
                darkMode ? 'bg-slate-800 border-slate-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            />
            <button
              onClick={handleSpeak}
              className={`absolute right-3 p-1 rounded-md ${darkMode ? 'hover:bg-slate-700' : 'hover:bg-slate-100'}`}
              title="朗读"
            >
              <SpeakerIcon />
            </button>
          </div>

          <div className="flex items-center space-x-2 w-full md:w-auto shrink-0 justify-end">
            <button
              onClick={onAnalyze}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-semibold rounded-xl flex items-center text-sm shadow-md shadow-blue-500/10 transition-all"
            >
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
              <span>开始分析</span>
            </button>

            <button
              onClick={onClear}
              className={`px-3 py-2.5 rounded-xl border font-medium text-xs transition-all ${
                darkMode ? 'border-slate-700 text-slate-300 hover:bg-slate-800' : 'border-slate-200 text-slate-500 hover:bg-slate-50'
              }`}
            >
              清空
            </button>

            <button
              onClick={() => setShowPresetDropdown(!showPresetDropdown)}
              className={`px-3.5 py-2.5 rounded-xl border font-medium text-xs flex items-center transition-all ${
                darkMode ? 'border-slate-700 text-slate-300 hover:bg-slate-800' : 'border-slate-200 text-slate-500 hover:bg-slate-50'
              }`}
            >
              <span>精选长句式</span>
              <ChevronDownIcon />
            </button>
          </div>
        </div>

        {/* 预设下拉菜单 */}
        {showPresetDropdown && (
          <div className={`absolute right-0 mt-2 w-96 rounded-2xl border shadow-xl z-20 overflow-hidden ${
            darkMode ? 'bg-slate-900 border-slate-800 text-slate-200' : 'bg-white border-slate-200 text-slate-700'
          }`}>
            <div className={`p-3 border-b text-[10px] font-bold uppercase tracking-wider ${
              darkMode ? 'bg-slate-800/40 border-slate-800' : 'bg-slate-50 border-slate-100 text-slate-400'
            }`}>
              切换学术级例句
            </div>
            <div className="p-1.5 space-y-1">
              {presets.map((preset, index) => (
                <button
                  key={index}
                  onClick={() => selectPreset(preset.sentence)}
                  className={`w-full text-left p-3 text-xs rounded-xl transition-all ${
                    darkMode ? 'hover:bg-blue-950/30' : 'hover:bg-blue-50'
                  }`}
                >
                  <p className={`font-semibold text-sm ${index === 0 ? 'text-blue-600' : 'text-indigo-600'}`}>
                    {preset.sentence}
                  </p>
                  <p className="text-slate-400 mt-1 text-[11px]">{preset.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
