import { ipcMain } from 'electron';

const BACKEND_URL = 'http://127.0.0.1:18765';
const ANALYZE_TIMEOUT = 5000;

export function registerIpcHandlers() {
  // 分析句子
  ipcMain.handle('analyze-sentence', async (_event, sentence: string) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT);

      const response = await fetch(`${BACKEND_URL}/api/tense/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sentence, mode: 'offline' }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 503) {
          return {
            success: false,
            error: '后端模型未加载，请等待后端启动完成',
          };
        }
        return {
          success: false,
          error: `后端返回错误: ${response.status} ${response.statusText}`,
        };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return {
          success: false,
          error: '请求超时，请确保后端服务正在运行 (python backend/app.py)',
        };
      }
      if ((error as Error).message.includes('ECONNREFUSED')) {
        return {
          success: false,
          error: '无法连接到后端服务，请先启动后端 (python backend/app.py)',
        };
      }
      return {
        success: false,
        error: `请求失败: ${(error as Error).message}`,
      };
    }
  });

  // 朗读句子（前端已实现 Web Speech API，这里保留占位）
  ipcMain.handle('speak-text', async (_event, _text: string) => {
    return { success: true };
  });

  // 复制到剪贴板（前端可直接使用 navigator.clipboard，这里保留占位）
  ipcMain.handle('copy-to-clipboard', async (_event, _text: string) => {
    const { clipboard } = require('electron');
    clipboard.writeText(_text);
    return { success: true };
  });
}
