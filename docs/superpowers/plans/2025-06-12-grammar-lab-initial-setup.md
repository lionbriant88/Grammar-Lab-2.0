# Grammar Lab 初始项目搭建实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 搭建 Grammar Lab 语法实验室项目的基础架构，包括前端界面框架和核心功能模块的基础结构。

**架构：** 使用 Electron + React + TypeScript 构建桌面应用，Tailwind CSS 处理样式，支持离线运行和后续 AI 模型集成。

**技术栈：** Electron, React 18, TypeScript, Vite, Tailwind CSS

---

## 项目结构

```
Grammar Lab/
├── src/
│   ├── main/                    # Electron 主进程
│   │   ├── index.ts            # 主进程入口
│   │   ├── ipc/                # IPC 通信处理
│   │   └── windows/            # 窗口管理
│   ├── renderer/                # 渲染进程（React）
│   │   ├── assets/             # 静态资源
│   │   ├── components/         # React 组件
│   │   │   ├── layout/         # 布局组件
│   │   │   ├── timeline/       # 时间轴功能
│   │   │   ├── anatomy/        # 句剖析功能
│   │   │   ├── expand/         # 句扩充功能
│   │   │   └── common/         # 通用组件
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── lib/                # 工具函数
│   │   ├── store/              # 状态管理
│   │   ├── types/              # TypeScript 类型
│   │   ├── App.tsx             # 根组件
│   │   └── main.tsx            # 渲染进程入口
│   └── shared/                 # 共享代码
├── public/                      # 静态资源
├── docs/                        # 文档
├── tests/                       # 测试文件
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── electron.vite.config.ts
└── README.md
```

---

## 任务 1: 初始化项目配置

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vite.config.ts`
- Create: `electron.vite.config.ts`
- Create: `tailwind.config.js`
- Create: `.gitignore`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "grammar-lab",
  "version": "0.1.0",
  "description": "英语语法实验室 - 离线英语教学辅助软件",
  "main": "dist-electron/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "preview": "electron-vite preview",
    "build:win": "npm run build && electron-builder --win",
    "build:mac": "npm run build && electron-builder --mac",
    "build:linux": "npm run build && electron-builder --linux"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/node": "^20.12.7",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "electron": "^30.0.0",
    "electron-builder": "^24.13.3",
    "electron-vite": "^2.3.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5",
    "vite": "^5.2.11"
  },
  "build": {
    "appId": "com.grammarlab.app",
    "productName": "Grammar Lab",
    "directories": {
      "output": "release"
    },
    "files": [
      "dist/**/*",
      "dist-electron/**/*"
    ]
  }
}
```

- [ ] **Step 2: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@renderer/*": ["src/renderer/*"],
      "@main/*": ["src/main/*"],
      "@shared/*": ["src/shared/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["electron.vite.config.ts", "vite.config.ts"]
}
```

- [ ] **Step 4: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@renderer': path.resolve(__dirname, './src/renderer'),
      '@shared': path.resolve(__dirname, './src/shared')
    }
  },
  server: {
    port: 5173
  }
});
```

- [ ] **Step 5: 创建 electron.vite.config.ts**

```typescript
import { defineConfig } from 'electron-vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  main: {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@main': path.resolve(__dirname, './src/main'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  },
  preload: {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  },
  renderer: {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@renderer': path.resolve(__dirname, './src/renderer'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  }
});
```

- [ ] **Step 6: 创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/renderer/**/*.{js,jsx,ts,tsx}',
    './src/index.html'
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#1e293b',
          950: '#020617'
        },
        blue: {
          150: '#1d4ed8'
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      },
      keyframes: {
        fadeIn: {
          'from': { opacity: '0', transform: 'translateY(12px)' },
          'to': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    }
  }
};
```

- [ ] **Step 7: 创建 postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
};
```

- [ ] **Step 8: 创建 .gitignore**

```
# Dependencies
node_modules/
.pnp/
.pnp.js

# Build outputs
dist/
dist-electron/
release/
out/

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Local env files
.env
.env.local
.env.*.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Claude
.claude/
```

- [ ] **Step 9: 创建 README.md**

```markdown
# Grammar Lab - 语法实验室

英语语法实验室是一款离线英语教学辅助软件，专注于帮助学生和教师理解英语语法结构。

## 功能

- **时间轴分析** - 可视化动词时态的时空关系
- **句剖析分析** - 句子结构和语法成分的详细分析
- **句扩展分析** - 从简单句到复杂句的渐进式扩展示例

## 开发

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 打包
npm run build:win  # Windows
npm run build:mac  # macOS
npm run build:linux  # Linux
```

## 技术栈

- Electron
- React 18
- TypeScript
- Vite
- Tailwind CSS
```

- [ ] **Step 10: 提交配置文件**

```bash
cd "D:/Grammar Lab"
git init
git add .
git commit -m "feat: initialize project configuration"
```

---

## 任务 2: 创建 Electron 主进程结构

**Files:**
- Create: `src/main/index.ts`
- Create: `src/main/windows/index.ts`
- Create: `src/main/ipc/index.ts`
- Create: `src/preload/index.ts`

- [ ] **Step 1: 创建主进程入口文件**

```typescript
// src/main/index.ts
import { app, BrowserWindow } from 'electron';
import * as path from 'path';
import { createMainWindow } from './windows';

let mainWindow: BrowserWindow | null = null;

// 单实例锁
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

app.on('ready', () => {
  mainWindow = createMainWindow();
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    mainWindow = createMainWindow();
  }
});
```

- [ ] **Step 2: 创建窗口管理模块**

```typescript
// src/main/windows/index.ts
import { BrowserWindow } from 'electron';
import * as path from 'path';

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
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  return mainWindow;
}
```

- [ ] **Step 3: 创建 IPC 通信模块（基础结构）**

```typescript
// src/main/ipc/index.ts
import { ipcMain } from 'electron';

export function registerIpcHandlers() {
  // 分析句子
  ipcMain.handle('analyze-sentence', async (event, sentence: string) => {
    // TODO: 实现句子分析逻辑
    return { success: true, data: null };
  });

  // 朗读句子
  ipcMain.handle('speak-text', async (event, text: string) => {
    // TODO: 实现朗读逻辑
    return { success: true };
  });

  // 复制到剪贴板
  ipcMain.handle('copy-to-clipboard', async (event, text: string) => {
    // TODO: 实现剪贴板逻辑
    return { success: true };
  });
}
```

- [ ] **Step 4: 创建预加载脚本**

```typescript
// src/preload/index.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  analyzeSentence: (sentence: string) => ipcRenderer.invoke('analyze-sentence', sentence),
  speakText: (text: string) => ipcRenderer.invoke('speak-text', text),
  copyToClipboard: (text: string) => ipcRenderer.invoke('copy-to-clipboard', text),
  onDarkModeChange: (callback: (isDark: boolean) => void) => {
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
```

- [ ] **Step 5: 提交主进程代码**

```bash
cd "D:/Grammar Lab"
git add src/
git commit -m "feat: add Electron main process structure"
```

---

## 任务 3: 创建 React 渲染进程基础结构

**Files:**
- Create: `src/renderer/main.tsx`
- Create: `src/renderer/App.tsx`
- Create: `src/renderer/index.html`
- Create: `src/renderer/types/index.ts`

- [ ] **Step 1: 创建渲染进程入口文件**

```typescript
// src/renderer/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 2: 创建全局样式文件**

```css
/* src/renderer/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-[#f4f7fc] text-slate-800;
  }
  
  .dark body {
    @apply bg-slate-950 text-slate-100;
  }
}

@layer components {
  .animate-fade-in {
    animation: fadeIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
}
```

- [ ] **Step 3: 创建 HTML 模板**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Grammar Lab - 语法实验室</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/renderer/main.tsx"></script>
</body>
</html>
```

- [ ] **Step 4: 创建 TypeScript 类型定义**

```typescript
// src/renderer/types/index.ts

// 功能场景类型
export type SceneType = 'timeline' | 'anatomy' | 'expand';

// 句子分析数据类型
export interface SentenceAnalysis {
  sentence: string;
  translation: string;
  translationExplanation: string;
  skeleton: {
    subject: string;
    verb: string;
    object_or_predicative: string;
    modifier: string;
  };
  decomposition: {
    mainClause: Clause;
    subClause?: Clause;
  };
  syntaxTree: SyntaxNode[];
  posTags: PosTag[];
  tenses: TenseAnalysis;
  expansions: ExpansionData;
  aiTeacherInsight: string;
}

export interface Clause {
  text: string;
  elements: ClauseElement[];
}

export interface ClauseElement {
  word: string;
  label: string;
  class: string;
}

export interface SyntaxNode {
  id: string;
  label: string;
  text: string;
  sublabel?: string;
  parent?: string;
  type?: string;
  isDashed?: boolean;
}

export interface PosTag {
  word: string;
  pos: string;
  type: string;
  detail: string;
}

export interface TenseAnalysis {
  past: string;
  present: string;
  summary: string;
  detailList: TenseDetail[];
}

export interface TenseDetail {
  verb: string;
  tense: string;
  role: string;
  voice: string;
  info: string;
}

export interface ExpansionData {
  word: string;
  progressiveSteps: ExpansionStep[];
  categories: Record<string, ExpansionCategory[]>;
}

export interface ExpansionStep {
  step: string;
  text: string;
  desc: string;
}

export interface ExpansionCategory {
  type: string;
  example: string;
}

// 应用状态类型
export interface AppState {
  activeScene: SceneType;
  darkMode: boolean;
  inputText: string;
  currentAnalysis: SentenceAnalysis | null;
  isLoading: boolean;
}

// Toast 通知类型
export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}
```

- [ ] **Step 5: 创建根组件基础结构**

```typescript
// src/renderer/App.tsx
import React, { useState, useEffect } from 'react';
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

  return (
    <div className="min-h-screen flex">
      {/* TODO: 添加侧边栏和主内容区 */}
      <div className="flex-1">
        <h1 className="text-2xl font-bold p-6">Grammar Lab - 语法实验室</h1>
        <p className="p-6 text-slate-600">项目初始化成功，开始开发...</p>
      </div>
    </div>
  );
}

export default App;
```

- [ ] **Step 6: 提交渲染进程基础结构**

```bash
cd "D:/Grammar Lab"
git add src/renderer/
git commit -m "feat: add React renderer基础结构"
```

---

## 任务 4: 创建布局组件

**Files:**
- Create: `src/renderer/components/layout/Sidebar.tsx`
- Create: `src/renderer/components/layout/Header.tsx`
- Create: `src/renderer/components/layout/MainLayout.tsx`

- [ ] **Step 1: 创建侧边栏组件**

```typescript
// src/renderer/components/layout/Sidebar.tsx
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

const menuItems = [
  { id: 'timeline' as SceneType, label: '时间轴分析', icon: Icons.Clock },
  { id: 'anatomy' as SceneType, label: '句剖析分析', icon: Icons.Anatomy },
  { id: 'expand' as SceneType, label: '句扩展分析', icon: Icons.Expand }
];

export default function Sidebar({ activeScene, onSceneChange, darkMode, onDarkModeToggle }: SidebarProps) {
  return (
    <aside className={`w-64 flex-shrink-0 flex flex-col justify-between border-r no-print transition-all duration-300 ${
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
          
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onSceneChange(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3.5 rounded-xl text-sm font-semibold transition-all ${
                activeScene === item.id
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : `text-slate-500 hover:bg-slate-50 ${darkMode ? 'hover:bg-slate-800/50' : ''}`
              }`}
            >
              <item.icon />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* 底部配置 */}
      <div className="p-4 border-t space-y-3" style={{ borderColor: darkMode ? 'rgb(30, 41, 59)' : 'rgb(226, 232, 240)' }}>
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
```

- [ ] **Step 2: 创建头部组件**

```typescript
// src/renderer/components/layout/Header.tsx
import React from 'react';
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
  const [showPresetDropdown, setShowPresetDropdown] = React.useState(false);

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
            <button onClick={handleSpeak} className="absolute right-3 p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md" title="朗读">
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
            <div className={`p-3 text-[10px] font-bold uppercase tracking-wider ${
              darkMode ? 'bg-slate-800/40 border-slate-800' : 'bg-slate-50 border-slate-100 text-slate-400'
            }`}>
              切换学术级例句
            </div>
            <div className="p-1.5 space-y-1">
              {presets.map((preset, index) => (
                <button
                  key={index}
                  onClick={() => selectPreset(preset.sentence)}
                  className="w-full text-left p-3 text-xs rounded-xl hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-all"
                >
                  <p className={`font-semibold text-sm ${index === 0 ? 'text-blue-600 dark:text-blue-400' : 'text-indigo-600 dark:text-indigo-400'}`}>
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
```

- [ ] **Step 3: 创建主布局组件**

```typescript
// src/renderer/components/layout/MainLayout.tsx
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
        <button onClick={onDarkModeToggle} className={`p-2 rounded-lg border transition-all ${
          darkMode ? 'bg-slate-800 border-slate-700 text-yellow-400' : 'bg-slate-50 border-slate-200 text-slate-500'
        }`}>
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

      {/* 侧边栏 */}
      <Sidebar
        activeScene={activeScene}
        onSceneChange={onSceneChange}
        darkMode={darkMode}
        onDarkModeToggle={onDarkModeToggle}
      />

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
```

- [ ] **Step 4: 更新 App.tsx 使用新布局**

```typescript
// src/renderer/App.tsx
import React, { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import type { SceneType } from './types';

function App() {
  const [activeScene, setActiveScene] = useState<SceneType>('timeline');
  const [darkMode, setDarkMode] = useState(false);
  const [inputText, setInputText] = useState('The book that I bought yesterday is very interesting.');

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

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
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">画布区域 - 等待分析</p>
      </div>
    </MainLayout>
  );
}

export default App;
```

- [ ] **Step 5: 提交布局组件**

```bash
cd "D:/Grammar Lab"
git add src/renderer/components/
git commit -m "feat: add layout components (Sidebar, Header, MainLayout)"
```

---

## 任务 5: 创建场景容器组件

**Files:**
- Create: `src/renderer/components/timeline/TimelineScene.tsx`
- Create: `src/renderer/components/anatomy/AnatomyScene.tsx`
- Create: `src/renderer/components/expand/ExpandScene.tsx`

- [ ] **Step 1: 创建时间轴场景组件**

```typescript
// src/renderer/components/timeline/TimelineScene.tsx
import React from 'react';

export default function TimelineScene() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">时间轴分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析"查看时态时间轴</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建句剖析场景组件**

```typescript
// src/renderer/components/anatomy/AnatomyScene.tsx
import React from 'react';

export default function AnatomyScene() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">句剖析分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析"查看语法结构</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建句扩展场景组件**

```typescript
// src/renderer/components/expand/ExpandScene.tsx
import React from 'react';

export default function ExpandScene() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">句扩展分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析"查看扩展示例</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 更新 App.tsx 集成场景组件**

```typescript
// src/renderer/App.tsx
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
```

- [ ] **Step 5: 提交场景组件**

```bash
cd "D:/Grammar Lab"
git add src/renderer/components/
git commit -m "feat: add scene components (Timeline, Anatomy, Expand)"
```

---

## 任务 6: 安装依赖并测试运行

**Files:**
- Modify: `package.json` (验证安装)

- [ ] **Step 1: 安装项目依赖**

```bash
cd "D:/Grammar Lab"
npm install
```

预期输出：成功安装所有依赖包，无错误。

- [ ] **Step 2: 启动开发服务器**

```bash
npm run dev
```

预期输出：Electron 窗口打开，显示 Grammar Lab 界面。

- [ ] **Step 3: 验证界面功能**

检查以下功能是否正常：
1. 界面正常显示，无样式错误
2. 侧边栏导航切换正常
3. 三个场景组件都能正确切换
4. 暗黑模式切换正常
5. 输入框可以正常输入
6. 预设例句下拉菜单正常

- [ ] **Step 4: 修复发现的问题（如有）**

如发现问题，修复后提交：

```bash
git add .
git commit -m "fix: 修复开发测试中发现的问题"
```

- [ ] **Step 5: 构建测试**

```bash
npm run build
```

预期输出：成功构建，dist 和 dist-electron 目录生成。

---

## 任务 7: 添加项目文档

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/api-reference.md`
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: 创建架构文档**

```markdown
# Grammar Lab 架构文档

## 概述

Grammar Lab 是一个基于 Electron 的桌面应用，采用 React + TypeScript + Vite 技术栈。

## 项目结构

```
Grammar Lab/
├── src/
│   ├── main/           # Electron 主进程
│   ├── renderer/       # React 渲染进程
│   ├── preload/        # 预加载脚本（IPC 桥接）
│   └── shared/         # 共享代码
├── public/             # 静态资源
├── docs/               # 文档
└── tests/              # 测试文件
```

## 技术栈

- **Electron**: 桌面应用框架
- **React**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **Tailwind CSS**: 样式框架

## 核心模块

### 主进程 (src/main)
- 窗口管理
- IPC 通信
- 系统集成

### 渲染进程 (src/renderer)
- React 组件
- 状态管理
- UI 交互

### 预加载脚本 (src/preload)
- IPC 桥接
- 安全隔离

## 设计原则

1. **离线优先**: 核心功能无需网络
2. **渐进增强**: 支持 AI 模型集成
3. **类型安全**: 全面使用 TypeScript
4. **组件化**: 高度模块化的组件设计
```

- [ ] **Step 2: 创建 API 参考文档**

```markdown
# API 参考文档

## Electron API

### analyzeSentence(sentence: string)

分析输入的英语句子。

**参数:**
- `sentence`: 要分析的英语句子

**返回:**
```typescript
Promise<{ success: boolean; data?: SentenceAnalysis }>
```

### speakText(text: string)

朗读英语文本。

**参数:**
- `text`: 要朗读的文本

**返回:**
```typescript
Promise<{ success: boolean }>
```

### copyToClipboard(text: string)

复制文本到剪贴板。

**参数:**
- `text`: 要复制的文本

**返回:**
```typescript
Promise<{ success: boolean }>
```

## 类型定义

详见 `src/renderer/types/index.ts`。
```

- [ ] **Step 3: 创建贡献指南**

```markdown
# 贡献指南

## 开发流程

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'feat: add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

## 代码规范

- 使用 TypeScript 编写
- 遵循 ESLint 规则
- 组件采用函数式写法
- 使用 Hooks 管理状态

## 提交信息规范

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链更新
```

- [ ] **Step 4: 提交文档**

```bash
cd "D:/Grammar Lab"
git add docs/
git commit -m "docs: add project documentation"
```

---

## 任务 8: 最终验证和清理

**Files:**
- Verify: 整个项目结构

- [ ] **Step 1: 验证项目结构**

```bash
cd "D:/Grammar Lab"
tree /F /A  # Windows
# 或
find . -type f -name "*.ts" -o -name "*.tsx" | head -20
```

确保以下文件存在：
- ✅ package.json
- ✅ tsconfig.json
- ✅ vite.config.ts
- ✅ electron.vite.config.ts
- ✅ tailwind.config.js
- ✅ src/main/index.ts
- ✅ src/renderer/App.tsx
- ✅ src/renderer/components/layout/

- [ ] **Step 2: 最终构建测试**

```bash
npm run build
```

确保构建成功，无错误。

- [ ] **Step 3: 清理临时文件**

```bash
git status
```

确保没有未提交的临时文件。

- [ ] **Step 4: 创建版本标签**

```bash
git tag v0.1.0
git push origin v0.1.0  # 如果有远程仓库
```

- [ ] **Step 5: 最终提交**

```bash
git add .
git commit -m "chore: project initialization complete"
```

---

## 完成检查清单

在计划完成后，验证以下内容：

1. **项目结构**: ✓ 所有必需文件已创建
2. **依赖安装**: ✓ npm install 成功
3. **开发运行**: ✓ npm run dev 成功启动
4. **界面显示**: ✓ 界面正常显示，符合设计
5. **功能切换**: ✓ 三个场景可以正常切换
6. **构建测试**: ✓ npm run build 成功
7. **文档完整**: ✓ 所有文档已创建

---

## 下一步计划

完成初始项目搭建后，下一步将实现：

1. **时间轴分析功能** - 实现时态可视化
2. **句剖析分析功能** - 实现语法结构分析
3. **句扩展分析功能** - 实现扩展示例展示
4. **离线分析引擎** - 实现本地句子分析算法
5. **AI 模型集成** - 支持在线/离线 AI 模型
