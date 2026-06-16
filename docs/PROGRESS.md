# Grammar Lab 开发进度

> **最后更��:** 2026-06-14
> **当前阶段:** 阶段 2 - 句剖析分析 ✅（后端 + 编译链路验证通过,UI 交互待人工确认）

---

## 📊 整体进度

| 阶段 | 名称 | 状态 | 完成时间 |
|------|------|------|----------|
| 0 | 基础框架搭建 | ✅ 完成 | 2026-06-12 |
| 1 | 时间轴分析功能 | ✅ 完成 | 2026-06-13 |
| 2 | 句剖析分析功能 | ✅ 完成 | 2026-06-14 |
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

## ✅ 阶段 1: 时间轴分析功能（已完成）

### 任务清单

- [x] 后端 mock 分析器 (`backend/grammar_engine/tense_analyzer.py`) - 9 种时态识别
- [x] 预设例句库 (`backend/grammar_engine/preset_sentences.py`) - 9 条覆盖 9 种时态
- [x] 后端 API 接入 (`backend/app.py`) - `/api/tense/analyze` 调用分析器
- [x] Electron IPC 真实化 (`src/main/ipc/index.ts`) - HTTP 调用后端
- [x] 前端类型扩展 (`src/renderer/types/index.ts`) - backend 响应字段
- [x] 工具函数 (`src/renderer/utils/tenseLabel.ts`, `zoneColor.ts`)
- [x] 状态管理 (`src/renderer/state/appState.ts`)
- [x] 时间轴可视化组件 (`TimelineChart.tsx`, `VerbDetailCard.tsx`, `TimeAdverbialList.tsx`)
- [x] TimelineScene 重写 - 集成所有组件
- [x] Header 预设扩展 - 9 条时态例句
- [x] 进度文档更新

### 新增文件

- `backend/grammar_engine/tense_analyzer.py` - 9 种时态识别（规则 + 词表）
- `backend/grammar_engine/preset_sentences.py` - 9 条预设例句
- `src/renderer/components/timeline/TimelineChart.tsx` - 时间轴核心组件
- `src/renderer/components/timeline/VerbDetailCard.tsx` - 节点详情卡
- `src/renderer/components/timeline/TimeAdverbialList.tsx` - 时间状语条
- `src/renderer/state/appState.ts` - 应用状态管理
- `src/renderer/utils/tenseLabel.ts` - 时态标签映射
- `src/renderer/utils/zoneColor.ts` - 时区配色

### 修改文件

- `backend/app.py` - analyze 端点接入真实分析器
- `src/main/ipc/index.ts` - IPC 转 HTTP 调用
- `src/renderer/types/index.ts` - 追加 backend 响应字段
- `src/renderer/App.tsx` - 接入 IPC + 状态透传
- `src/renderer/components/timeline/TimelineScene.tsx` - 替换空占位
- `src/renderer/components/layout/Header.tsx` - 9 条预设
- `src/renderer/index.css` - 入场动画
- `docs/PROGRESS.md` - 阶段 1 标记完成

---

## ✅ 阶段 2: 句剖析分析功能（已完成）

### 任务清单

- [x] 后端 spaCy 分析器 (`backend/grammar_engine/anatomy_analyzer.py`) - 语义块 + 主从分句
- [x] Pydantic 模型 (`backend/grammar_engine/models.py`) - Chunk/Clause/ClauseElement/AnatomyResponse
- [x] 后端端点 (`backend/app.py`) - `/api/anatomy/analyze`
- [x] 前端类型 (`src/renderer/types/index.ts`) - AnatomyBackend/AnatomyChunk/AnatomyClause
- [x] IPC handler (`src/main/ipc/index.ts`) - `analyze-sentence-anatomy`
- [x] preload 暴露 (`src/preload/index.ts`) - `analyzeAnatomy`
- [x] 状态管理 (`src/renderer/state/appState.ts`) - `analyzeAnatomy`(与 tense 数据合并存储)
- [x] 工具函数 (`src/renderer/utils/roleColor.ts`) - 角色→配色/中文标签
- [x] 语义块主视图 (`ChunkBlocks.tsx`) - 流式色带 + 编辑态拖拽搬词
- [x] 编辑工具条 (`EditToolbar.tsx`) - 改角色/撤销/重置/完成
- [x] 主从分句分解 (`ClauseBreakdown.tsx`) - 主句+从句卡片
- [x] 场景编排 (`AnatomyScene.tsx`) - 编辑状态机 + 历史栈
- [x] App.tsx 数据流 - 切到 anatomy 场景自动拉取

### 设计要点

- **语义块切割（非逐词词性）**：把句子切成主语块/谓语块/宾语块/状语块/从句块，每块一种颜色（主语=蓝、谓语=绿、宾语=紫、状语=琥珀、从句=粉），横向流式色带展示。
- **基于 spaCy 依存分析**：用 `en_core_web_sm` 的 dep_/subtree 逐词归类，从句（relcl/advcl/ccomp）独立剥离成块。
- **手动编辑模式（教师修正）**：spaCy 对复杂句必然出错（如把名词误判为 ROOT），教师可通过拖拽把词搬到正确的色块、或选中整块改角色。仅本会话生效，含撤销栈和重置。
- **两大模块**：① 语义块色带（主视图，可编辑）② 主从分句分解（只读参考）。

### 新增文件

- `backend/grammar_engine/anatomy_analyzer.py` - spaCy 语义块/分句分析
- `src/renderer/components/anatomy/ChunkBlocks.tsx` - 语义块色带 + 编辑拖拽
- `src/renderer/components/anatomy/EditToolbar.tsx` - 编辑工具条
- `src/renderer/components/anatomy/ClauseBreakdown.tsx` - 分句分解卡片
- `src/renderer/utils/roleColor.ts` - 角色→配色映射

### 修改文件

- `backend/grammar_engine/models.py` - 追加 anatomy Pydantic 模型
- `backend/app.py` - `/api/anatomy/analyze` 端点
- `src/main/ipc/index.ts` - `analyze-sentence-anatomy` handler
- `src/preload/index.ts` - `analyzeAnatomy` 暴露
- `src/renderer/state/appState.ts` - `analyzeAnatomy` action + anatomy 字段合并
- `src/renderer/types/index.ts` - AnatomyBackend 等类型 + SentenceAnalysis.anatomy
- `src/renderer/components/anatomy/AnatomyScene.tsx` - 重写空占位
- `src/renderer/App.tsx` - anatomy 数据流 + 场景切换自动拉取

### 验证状态

- ✅ 后端端点 curl 多句通过（简单句、含定语/状语/宾语从句均正确）
- ✅ TypeScript 编译零错误
- ✅ electron-vite 构建 main/preload/renderer 全部成功
- ✅ Vite dev server 解析所有新模块（200）
- ✅ Electron 窗口内人工验证：拖拽编辑 + 选块改角色 + 标点块内误判词可拖 均通过（2026-06-16）
- ✅ 已知局限：spaCy en_core_web_sm 对个别复杂句（如名词+定语从句+动词）会误判 ROOT，由手动编辑模式兜底

---

---

## ⏭️ 下一步：阶段 3 - 句扩展分析功能

### 计划任务

1. **扩展示例** - 核心词 → 修饰语 → 从句的渐进式扩展示例
2. **分类展示** - 按扩展类型分类（形容词、副词、介词短语、从句）
3. **集成到场景** - 替换 ExpandScene 空白占位符

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
