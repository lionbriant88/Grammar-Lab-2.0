import { ipcMain } from 'electron';

export function registerIpcHandlers() {
  // 分析句子
  ipcMain.handle('analyze-sentence', async (_event, _sentence: string) => {
    // TODO: 实现句子分析逻辑
    return { success: true, data: null };
  });

  // 朗读句子
  ipcMain.handle('speak-text', async (_event, _text: string) => {
    // TODO: 实现朗读逻辑
    return { success: true };
  });

  // 复制到剪贴板
  ipcMain.handle('copy-to-clipboard', async (_event, _text: string) => {
    // TODO: 实现剪贴板逻辑
    return { success: true };
  });
}
