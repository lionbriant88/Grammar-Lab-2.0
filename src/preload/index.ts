import { contextBridge, ipcRenderer } from 'electron';

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  analyzeSentence: (sentence: string) => ipcRenderer.invoke('analyze-sentence', sentence),
  speakText: (text: string) => ipcRenderer.invoke('speak-text', text),
  copyToClipboard: (text: string) => ipcRenderer.invoke('copy-to-clipboard', text),
  onDarkModeChange: (_callback: (isDark: boolean) => void) => {
    // TODO: 实现主题监听
  }
});

// 类型声明
export interface ElectronAPI {
  analyzeSentence: (sentence: string) => Promise<{ success: boolean; data?: any }>;
  speakText: (text: string) => Promise<{ success: boolean }>;
  copyToClipboard: (text: string) => Promise<{ success: boolean }>;
  onDarkModeChange: (callback: (isDark: boolean) => void) => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
