import { ipcMain } from 'electron';

const BACKEND_URL = 'http://127.0.0.1:18765';
const ANALYZE_TIMEOUT = 5000;

const BUILTIN_FALLBACK_RESULT = {
  title: '解释',
  summary: 'AI 暂不可用。',
  why: '请检查后端服务是否运行,或 AI provider 是否配置。',
  example: '',
  common_mistakes: [],
  tips: [],
  source: 'fallback',
  provider: 'builtin',
  model: 'builtin',
  prompt_version: 'M4a_v1',
  cached: false,
  generated_at: new Date().toISOString(),
};

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

  // 句剖析分析
  ipcMain.handle('analyze-sentence-anatomy', async (_event, sentence: string) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT);

      const response = await fetch(`${BACKEND_URL}/api/anatomy/analyze`, {
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

  // 句扩展分析(M3a,phrase-level 只读)
  ipcMain.handle('analyze-sentence-expansion', async (_event, sentence: string) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT);

      const response = await fetch(`${BACKEND_URL}/api/expansion/analyze`, {
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

  // 句扩展 apply 路径(M3a+1,/api/expansion/apply)
  ipcMain.handle('apply-expansion', async (_event, sentence: string, phraseId: string, templateId: string) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT);

      const response = await fetch(`${BACKEND_URL}/api/expansion/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sentence, phrase_id: phraseId, template_id: templateId, mode: 'offline' }),
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

  // M4: AI explain
  ipcMain.handle('explain-node', async (_event, ctx) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 35_000);

      const response = await fetch(`${BACKEND_URL}/api/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ctx),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // /api/explain 理论上不会 4xx/5xx,这里兜底
        return {
          success: true,
          data: { ok: true, degraded: true, result: BUILTIN_FALLBACK_RESULT },
        };
      }
      return { success: true, data: await response.json() };
    } catch (error) {
      return {
        success: true,
        data: { ok: true, degraded: true, result: BUILTIN_FALLBACK_RESULT },
      };
    }
  });

  ipcMain.handle('explain-health', async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/api/explain/health`);
      if (!r.ok) {
        return { success: false, error: `HTTP ${r.status}` };
      }
      return { success: true, data: await r.json() };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  });
}
