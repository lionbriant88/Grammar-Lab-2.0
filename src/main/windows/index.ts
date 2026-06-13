import { BrowserWindow } from 'electron';
import * as path from 'path';
import { existsSync } from 'fs';

export function createMainWindow(): BrowserWindow {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 600,
    frame: true,
    titleBarStyle: 'default',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    },
    backgroundColor: '#f4f7fc',
    show: false
  });

  // 开发模式下加载开发服务器
  const devUrl = process.env.VITE_DEV_SERVER_URL;
  const rendererFile = path.join(__dirname, '../renderer/index.html');

  if (devUrl) {
    // 标准 electron-vite 注入路径
    mainWindow.loadURL(devUrl);
    mainWindow.webContents.openDevTools();
  } else if (existsSync(rendererFile)) {
    // 回退：本地构建产物（生产模式或 dev server 未就绪）
    mainWindow.loadFile(rendererFile);
  } else {
    // 最后回退：直接探测常见 dev 端口（当 electron-vite 未注入 env 时）
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.webContents.on('did-fail-load', (_e, errorCode, errorDescription, validatedURL) => {
    console.error(`[Grammar Lab] 加载失败: ${errorCode} ${errorDescription} url=${validatedURL}`);
  });

  return mainWindow;
}
