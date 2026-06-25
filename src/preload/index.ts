import { contextBridge, ipcRenderer } from 'electron';

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  analyzeSentence: (sentence: string) => ipcRenderer.invoke('analyze-sentence', sentence),
  analyzeAnatomy: (sentence: string) => ipcRenderer.invoke('analyze-sentence-anatomy', sentence),
  analyzeExpansion: (sentence: string) => ipcRenderer.invoke('analyze-sentence-expansion', sentence),
  applyExpansion: (sentence: string, phraseId: string, templateId: string) =>
    ipcRenderer.invoke('apply-expansion', sentence, phraseId, templateId),
  speakText: (text: string) => ipcRenderer.invoke('speak-text', text),
  copyToClipboard: (text: string) => ipcRenderer.invoke('copy-to-clipboard', text),
  onDarkModeChange: (callback: (isDark: boolean) => void) => {
    ipcRenderer.on('dark-mode-changed', (_event, isDark: boolean) => {
      callback(isDark);
    });
  },
  explainNode: (ctx: any) => ipcRenderer.invoke('explain-node', ctx),
  getExplainHealth: () => ipcRenderer.invoke('explain-health'),
});

// 类型声明
export interface ElectronAPI {
  analyzeSentence: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  analyzeAnatomy: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  analyzeExpansion: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  applyExpansion: (sentence: string, phraseId: string, templateId: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  speakText: (text: string) => Promise<{ success: boolean }>;
  copyToClipboard: (text: string) => Promise<{ success: boolean }>;
  onDarkModeChange: (callback: (isDark: boolean) => void) => void;
  explainNode: (ctx: any) => Promise<{ success: boolean; data?: any; error?: string }>;
  getExplainHealth: () => Promise<{ success: boolean; data?: any; error?: string }>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
