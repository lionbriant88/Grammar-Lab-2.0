# Grammar Lab 开发进度

> **最后更新:** 2026-06-12
> **当前阶段:** 阶段 0 - 基础框架 ✅

---

## 📊 整体进度

| 阶段 | 名称 | 状态 | 完成时间 |
|------|------|------|----------|
| 0 | 基础框架搭建 | ✅ 完成 | 2026-06-12 |
| 1 | 时间轴分析功能 | ⏳ 待开始 | - |
| 2 | 句剖析分析功能 | ⏳ 待开始 | - |
| 3 | 句扩展分析功能 | ⏳ 待开始 | - |
| 4 | AI 模型集成 | ⏳ 待开始 | - |

---

## ✅ 阶段 0: 基础框架（已完成）

### 任务清单

- [x] 初始化项目配置（package.json、tsconfig、vite 配置等）
- [x] 创建 Electron 主进程结构（窗口、IPC、预加载）
- [x] 创建 React 渲染进程基础结构
- [x] 创建布局组件（Sidebar、Header、MainLayout）
- [x] 创建三个场景容器组件（时间轴、句剖析、句扩展）
- [x] 安装依赖并测试运行
- [x] 修复 Electron 二进制安装问题

### 项目结构

```
D:/Grammar Lab/
├── src/
│   ├── main/                       # Electron 主进程
│   │   ├── index.ts               # 主进程入口
│   │   ├── ipc/index.ts           # IPC 通信处理
│   │   └── windows/index.ts       # 窗口管理
│   ├── preload/
│   │   └── index.ts               # 预加载脚本
│   └── renderer/                   # React 渲染进程
│       ├── App.tsx                # 根组件
│       ├── main.tsx               # 入口
│       ├── index.css              # 全局样式
│       ├── index.html             # HTML 模板
│       ├── types/index.ts         # TypeScript 类型
│       └── components/
│           ├── layout/
│           │   ├── Sidebar.tsx          # 侧边栏
│           │   ├── Header.tsx           # 头部（输入控制）
│           │   └── MainLayout.tsx       # 主布局
│           ├── timeline/
│           │   └── TimelineScene.tsx    # 时间轴场景（空白）
│           ├── anatomy/
│           │   └── AnatomyScene.tsx     # 句剖析场景（空白）
│           └── expand/
│               └── ExpandScene.tsx      # 句扩展场景（空白）
├── docs/                          # 文档
│   ├── superpowers/plans/         # 实施计划
│   └── PROGRESS.md                # 进度文档
├── node_modules/                  # 依赖
├── out/                           # 构建输出（gitignore）
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── electron.vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .gitignore
└── README.md
```

### 技术栈

- **Electron 30** - 桌面应用框架
- **React 18.3.1** - UI 框架
- **TypeScript 5.4.5** - 类型安全
- **Vite 5.2.11** - 构建工具
- **electron-vite 2.3.0** - Electron 集成
- **Tailwind CSS 3.4.3** - 样式框架

### UI 特性

- ✅ 响应式布局（桌面 + 移动端）
- ✅ 暗黑模式切换
- ✅ 侧边栏导航切换
- ✅ 顶部输入控制区
- ✅ 预设例句下拉菜单
- ✅ 三个场景切换（当前为空画布）

### 开发命令

```bash
cd "D:/Grammar Lab"
npm install      # 安装依赖
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
```

---

## ⏭️ 下一步：阶段 1 - 时间轴分析功能

### 计划任务

1. **数据模型** - 定义时态分析的数据结构
2. **本地分析算法** - 实现启发式时态识别
3. **时间轴组件** - 可视化时态节点
4. **集成到场景** - 替换空白占位符
5. **测试和优化** - 验证准确性和性能

### 设计要点

- 三个时态节点：过去 (PAST)、现在 (PRESENT)、将来 (FUTURE)
- 支持多种时态识别：一般现在/过去/将来、现在进行、过去进行等
- 节点可点击查看详情
- 支持多动词时态分析

---

## 🗂️ 相关文件

- **设计参考:** `C:/Users/lionb/english-tutor-design/grammar-lab.html`
- **UI 设计源:** `D:/grammar_lab.tsx`
- **实施计划:** `docs/superpowers/plans/2025-06-12-grammar-lab-initial-setup.md`

---

## 📝 注意事项

1. **Electron 安装**: 由于环境问题，electron 的二进制需要手动下载。详见修复记录。
2. **构建输出**: `out/` 目录是 electron-vite 的默认输出，git 已忽略。
3. **依赖锁定**: package-lock.json 保留以确保团队协作一致性。
4. **设计稿**: 桌面 `C:/Users/lionb/english-tutor-design/` 下的 HTML 文件是设计参考，可作为 UI 实现对照。
