# Grammar Lab 开发进度

> **最后更新:** 2026-06-25
> **当前阶段:** 阶段 4 - AI Explain Layer ✅（M4a-M4d 全量交付 + 收尾 I2+M3+M5）

---

## 📊 整体进度

| 阶段 | 名称 | 状态 | 完成时间 |
|------|------|------|----------|
| 0 | 基础框架搭建 | ✅ 完成 | 2026-06-12 |
| 1 | 时间轴分析功能 | ✅ 完成 | 2026-06-13 |
| 2 | 句剖析分析功能 | ✅ 完成 | 2026-06-14 |
| 3 | 句扩展分析功能 | ✅ 完成 (M3a → M3c5 全部完成) | 2026-06-24 |
| 4 | AI Explain Layer | ✅ 完成 (M4a-M4d 全量交付) + 收尾 (I2+M3+M5) | 2026-06-25 |

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

## ✅ 阶段 3: 句扩展分析功能 - M3a 完成(2026-06-16)

### 任务清单

- [x] 后端 Grammar Engine(phrase-level 数据模型)
  - `phrase_segmenter.py` [新] - NP/VP/PP 识别 + Parent-Child 挂载(调整1)+ VP 完整时态链(调整2)
  - `expansion_rules.py` [新] - 规则库(键=PhraseType)
  - `expansion_templates.py` [新] - L1 模板 20 个(adj7/adv6/num4/degree3)
  - `expansion_validator.py` [新] - 主谓一致有实现,其他 4 项签名齐返回 PASS
  - `expansion_engine.py` [新] - 主入口 analyze
  - `models.py` 追加 `Expansion*` Pydantic 6 类
- [x] 后端端点 `app.py` 追加 `/api/expansion/analyze`
- [x] 单元测试 `test_expansion_engine.py`(15 测试全过)+ `conftest.py`
- [x] 前端 IPC 链路(ipc/preload/types/appState/App,复制 M2 anatomy 模式)
- [x] 前端三栏 UI:SentenceCanvas(短语画布+特征槽徽章+可扩展高亮)+ ExtensionMenu([+]只读浮层)+ ExpansionTree(右栏「短语结构图」)+ ExtensionLibrary(左栏占位)+ ExpandScene 三栏编排
- [x] UI 风格对齐 anatomy(新 utils/phraseColor.ts,NP=蓝/VP=绿/PP=琥珀)
- [x] Electron 端到端人工验证通过

### 设计要点

- **phrase-level 数据模型**:扩展单位是 NP/VP/PP/Clause,不是 token(原则 #1/#2)。
- **三条架构调整**:① PhraseNode 加 parent_id/children_ids(PP→NP/VP 挂载消除漂浮);② VP 吞完整时态链(has been working/would like 各一个 VP);③ 右栏叫「短语结构图」不叫「成分句法树」(M3b 升级)。
- **设计精神**:数据模型稳定优先于分析精度,为 M3b 接 Benepar / M3c 接 LanguageTool 预留接缝。
- **严格只读**:不做提交闭环、新增高亮、连线、动态 Expansion Tree、Level 2/3、完整 Validator、AI。

### 新增文件

- `backend/grammar_engine/phrase_segmenter.py` - 短语识别(spaCy noun_chunks+dep_,M3b 换 Benepar)
- `backend/grammar_engine/expansion_rules.py` - 规则库(短语类型→可扩展项)
- `backend/grammar_engine/expansion_templates.py` - L1 模板集(20 个)
- `backend/grammar_engine/expansion_validator.py` - Validator(主谓一致有实现,其他 4 项占位)
- `backend/grammar_engine/expansion_engine.py` - 主入口
- `backend/tests/test_expansion_engine.py` + `conftest.py` - 单元测试(15 项)
- `src/renderer/components/expand/SentenceCanvas.tsx` - 短语画布 + 节点卡片
- `src/renderer/components/expand/ExtensionMenu.tsx` - [+] 只读浮层
- `src/renderer/components/expand/ExpansionTree.tsx` - 右栏短语结构图
- `src/renderer/components/expand/ExtensionLibrary.tsx` - 左栏占位
- `src/renderer/utils/phraseColor.ts` - 短语类型配色(对齐 anatomy)

### 修改文件

- `backend/grammar_engine/models.py` - 追加 Expansion* Pydantic
- `backend/app.py` - 追加 /api/expansion/analyze 端点
- `src/main/ipc/index.ts` - analyze-sentence-expansion handler
- `src/preload/index.ts` - analyzeExpansion 暴露
- `src/renderer/state/appState.ts` - analyzeExpansion action
- `src/renderer/types/index.ts` - Expansion* 类型 + SentenceAnalysis.expansion
- `src/renderer/App.tsx` - expand 场景自动拉取 + props 升级
- `src/renderer/components/expand/ExpandScene.tsx` - 重写,三栏编排

### 验证状态

- ✅ pytest 15 测试全过
- ✅ curl 三例通过(含 VP 时态链 + PP 挂载)
- ✅ tsc --noEmit 零错误 + npm run build 全链路通过
- ✅ Electron 窗口人工验证(2026-06-16):三栏 / 画布特征槽 / 高亮灰显 / [+]菜单 / 右栏短语结构图 / 树点叶子联动

### 已知问题(留待后续)

1. ipc/index.ts / appState.ts 三段 handler/action 重复(tense/anatomy/expansion),M3 结束后抽工具重构。
2. spaCy 小模型对 `He like dogs.` 把 like 误标 ADP,靠 Validator simple_present 兜底 + VERB_LEMMA_FALLBACK 补救;M3b 接 Benepar 后应改善。
3. pytest 未列入 requirements.txt(本次装到全局 python),后续补。

---

## ✅ 阶段 3 续: M3b - Benepar + Aux Chain Validator (2026-06-23)

### 目标

Phase 2: 引入 Benepar 成分句法分析 + 助动词链完整性校验

### 任务清单

- [x] 后端 Benepar 集成（带 spaCy 降级机制）
- [x] PhraseNode 数据模型扩展（head_word/role/modifiers）
- [x] Validator aux_chain 完整性检查
- [x] 前端 UI 标题更新（句法结构）
- [x] TypeScript 类型定义更新

### 架构决策

1. **Benepar 降级策略**: transformers 5.x 兼容性问题，系统正确降级到 spaCy
2. **无 PP_RULES**: PP 扩展通过 children NP 自动处理
3. **无 PARTICIPLE_RULES**: 复用 VP + verb_form 特征
4. **Aux Chain 完整性**: 检查单 VP 内部，不做跨 VP 时态一致性

### 新增文件

- `backend/grammar_engine/phrase_segmenter_benepar.py`
- `docs/M3b-checkpoint-2026-06-23.md`
- `docs/superpowers/specs/2026-06-23-m3b-design-v2.md`

### 修改文件

- `backend/grammar_engine/nlp_loader.py`
- `backend/grammar_engine/phrase_segmenter.py`
- `backend/grammar_engine/expansion_validator.py`
- `backend/grammar_engine/models.py`
- `backend/requirements.txt`
- `src/renderer/components/expand/ExpansionTree.tsx`
- `src/renderer/types/index.ts`

### 验证状态

- ✅ pytest 30/31 通过
- ✅ TypeScript 零错误
- ✅ Benepar 降级机制验证
- ✅ M3a 回归测试通过

---

## ✅ 阶段 3 续续: M3c1 - Validation Layer (2026-06-23)

**目标:** 完善验证层，实现剩余 3 项 Rule Validators + LanguageTool 集成

### 核心任务

- ✅ **ExternalServiceManager 基类** - 为 LanguageTool/Ollama/AI/TTS 复用设计
- ✅ **LanguageToolManager** - 嵌入式服务器管理，非阻塞异步启动
- ✅ **safe_execute() 包装器** - 零崩溃保证，任何 validator 失败 → 降级 → 继续
- ✅ **3 项浅层 Rule Validators**:
  - clause_completeness - 从句完整性（缺主语/谓语）
  - non_finite_legality - 非谓语合法性（to + base form, 动词模式）
  - relative_pronoun_match - 关系代词匹配（人/物 + who/which）
- ✅ **LanguageTool Validator #6** - 次级顾问（非语法权威）
- ✅ **validate() 统一入口更新** - 6 项 validators 全部用 safe_execute 包装
- ✅ **Backend 启动集成** - LanguageTool 后台启动，Backend 立即可用
- ✅ **80/15/5 测试金字塔** - 28 个测试（重点：降级测试）

### 架构原则

- **验证优先，生成其次** - 永不同时开发模板和验证器
- **零崩溃保证** - 任何组件失败 → 降级 → 继续工作
- **Always HTTP 200** - 永不返回 500，Validator 是教师非编译器
- **LanguageTool 次级顾问** - Grammar Engine 是唯一语法权威

### 测试覆盖

- ✅ 21 个单元测试（80%）
- ✅ 7 个降级测试（15%，最高优先级）
- ✅ 全部通过，零崩溃验证

### 关键文件

- `backend/grammar_engine/external_service_manager.py` - 基类
- `backend/grammar_engine/languagetool_manager.py` - LT 管理器
- `backend/grammar_engine/expansion_validator.py` - 6 项 validators + safe_execute
- `backend/app.py` - 启动/关闭事件
- `backend/tests/test_m3c1_validators.py` - 单元测试
- `backend/tests/test_m3c1_degradation.py` - 降级测试

### 设计文档

- `docs/superpowers/specs/2026-06-23-m3c1-validation-layer-design.md`
- `docs/superpowers/plans/2026-06-23-m3c1-validation-layer.md`

---

## ✅ 阶段 3 续续续: M3c2 - Template Foundation (2026-06-23)

**目标:** 建立从句扩展的模板基础架构（内部准备，不对外开放）

### 核心任务

- ✅ **TemplateBase 抽象层** - Slot / ClauseTemplate / TemplateBase
- ✅ **ClauseRealizer 基础设施** - RealizationContext / 槽位替换 / 约束验证
- ✅ **3 类从句模板定义** - relative/adverbial/noun 各 2 个占位模板
- ✅ **expansion_engine 集成** - apply_template() 识别 ClauseTemplate
- ✅ **55 个单元测试** - 100% 通过

### 架构原则

- **无 UI，无 available=True** - 纯后端基础设施，前端不可见
- **槽位驱动设计** - Slot 是从句模板的核心抽象
- **Realizer 分离** - 实现与模板定义分离
- **为 M3c3-5 铺路** - 每个阶段只需加模板，不改架构

### 模板数量

- 定语从句: 2 个占位模板 (who/which + verb)
- 状语从句: 2 个占位模板 (because/when + clause)
- 名词性从句: 2 个占位模板 (that/whether + clause)
- **所有模板 available=False**

### 关键文件

- `backend/grammar_engine/template_base.py` - 模板基类
- `backend/grammar_engine/clause_realizer.py` - 实现器
- `backend/grammar_engine/clause_templates.py` - 模板定义
- `backend/grammar_engine/expansion_engine.py` - 集成（占位）
- `backend/tests/test_template_base.py` - 17 tests
- `backend/tests/test_clause_realizer.py` - 14 tests
- `backend/tests/test_clause_templates.py` - 22 tests
- `backend/tests/test_m3c2_integration.py` - 2 tests

### 设计文档

- `docs/superpowers/plans/2026-06-23-m3c2-template-foundation.md`

---

## ✅ 阶段 3 续续续续: M3c3 - Relative Clause Templates (2026-06-23)

**目标:** 开放定语从句模板，用户可在前端选择定语从句扩展

### 核心任务

- ✅ **扩展 RELATIVE_CLAUSE_TEMPLATES** - 从 2 个占位到 10 个真实模板
  - 主语关系从句: who/which/that + VP (3 个)
  - 宾语关系从句: who/whom/which/that + NP + VP (4 个)
  - 所有格关系从句: whose + NP + VP (1 个)
  - 关系副词从句: where/when + clause (2 个)
- ✅ **所有模板 available=True** - 前端可见可用
- ✅ **expansion_rules.py** - relative_clause 设置 available=True
- ✅ **RelativeClauseRealizer 完善** - 约束验证 + 先行词类型识别
- ✅ **集成到 expansion_engine** - expansion_templates 支持从句模板查询
- ✅ **单元测试** - 24 个测试全部通过
- ✅ **E2E 验证** - curl 测试通过，返回 10 个定语从句模板

### 关键实现

1. **先行词类型识别** (`RelativeClauseRealizer._get_antecedent_type`)
   - person: 人物名词（teacher/man/student）+ 人称代词（he/she）
   - thing: 默认类型（book/car/dog）
   - place: 地点名词（city/school/park）
   - time: 时间名词（day/year/moment）
   - reason: 原因名词（reason/cause）

2. **约束验证** (`_validate_antecedent_constraints`)
   - who/whom 要求 person
   - which 要求 thing
   - that 接受 any
   - where 要求 place
   - when 要求 time
   - whose 接受 any

3. **模板预览修复** (`expansion_engine._compose_preview`)
   - ClauseTemplate 直接返回 surface（保留槽位占位符 `<VERB>`）
   - WordTemplate 继续使用 example_anchor 逻辑

### 验证状态

- ✅ pytest 24/24 通过
- ✅ curl API 返回定语从句 candidates
- ✅ 10 个模板全部 available=True
- ✅ 先行词类型识别覆盖常见用例

### 设计文档

- `.claude/plans/m3c3-relative-clause-expansion.md`

---

## ⏭️ 下一步：阶段 3 续(M3c4-5) 或 阶段 4

- **M3c4**(Phase 3): 开放状语从句（10-12 个 because/when/if/although 模板）
- **M3c5**(Phase 3): 开放名词性从句（10-12 个 that/whether/what/how 模板）
- **阶段 4**: AI 模型集成

---

## ✅ 阶段 4 收尾: M4 Follow-ups (I2+M3+M5) — 2026-06-25

M4 整分支审查后列出的 4 个 deferred follow-ups 中,本批次关闭 3 个:

- ✅ **I2 (集成测)** — 新增 `backend/tests/integration/test_m4_full_flow.py`(4 条 in-process,TestClient 模式) + `src/renderer/__integration__/explain_flow.test.tsx`(3 条跨组件 Vitest)
- ✅ **M3 (@ts-ignore 清理)** — 新增 `src/types/electron-api.d.ts` ambient 声明,删除 `ExplainPanel.tsx:51` 与 `healthStore.ts:15` 两处 `@ts-ignore`,修正 3 处测试文件 mock 写法
- ✅ **M5 (worktree 清理)** — 移除 `feature-m3a-plus-1` worktree(已合并于 `30e02f3`)
- ⏭️ **M6 (i18n)** — 留待阶段 5 独立处理

**结果:** TypeScript 0 错误;前端 Vitest 43/43 通过(40 → 43);后端 pytest 全套回归不挂;`grep -r '@ts-ignore' src/` 为空;`git worktree list` 仅 main。

---

## 🐛 运行时排查记录: ExplainPanel 不显示 (2026-06-25)

本地启动 `npm run dev` 后,时间轴点击节点**不出现 ExplainPanel**。经 systematic-debugging 四阶段定位:

- **根因(环境,非代码):** `VITE_DEV_SERVER_URL` 在主进程未注入成功 → `src/main/windows/index.ts:31` 的回退 `existsSync(out/renderer/index.html)` 命中 → Electron 加载了 **2026-06-17 的过时静态构建产物**(早于 M4c 集成,没有 ExplainPanel)。M4 代码本身完全正常(后端 `/api/explain` 直测 200,DEBUG 日志显示完整调用链 `effect → explainNode=function → success=true`)。
- **修复:** `rm -rf out/renderer/`(保留 main/preload),重启 `npm run dev` → 回退落到第三条 `loadURL('localhost:5173')` → 加载实时 dev server → ExplainPanel 正常出现。
- **代码无改动**(诊断代码加完即删,工作树干净,测试全过)。

**详见记忆文件 `grammar-lab-env-trap.md`。**

---

## 📋 下次继续 —— 状态总览 (2026-06-25)

### ✅ 已完成并推送
- 阶段 0-3 全部完成
- 阶段 4 (M4 AI Explain Layer): M4a-M4d 全量交付 + 收尾 I2/M3/M5,98% 覆盖率,整分支审查通过
- 本次收尾批次 7 commit(`84808fc`..`570097c`)已推送 GitHub

### 🐛 已知 BUG / 待优化(未修,按优先级)

1. **【环境·复发风险】dev URL 注入 + 静态产物回退陷阱** — `windows/index.ts` 的三级回退在 dev URL 没注入时会**静默**加载过时 `out/renderer/`,不开 DevTools 不报错,极难发现。临时删产物已修当前,但下次 `npm run build` 后可能复发。**建议根治:** dev 模式优先探测 5173,或回退时 `console.warn`,或 dev 脚本前 `rimraf out/renderer`。
2. **【后端·预存】2 个 pytest 失败**(与 M4 无关,长期存在):
   - `tests/test_health.py::test_health_endpoint` — 需后端运行,CI 里会 timeout
   - `tests/test_m3c2_integration.py::test_apply_template_with_clause_template_placeholder` — fixture/断言问题,返回 `'The dog who is goodruns.'` 而非 `'The dog runs.'`
3. **【后端·质量】时态分析器误判** — `I have lived here for ten years.` 把 `here` 误识别为动词(v2, surface='here')。spaCy 小模型局限,或规则引擎 bug,需排查 `tense_analyzer.py`。
4. **【前端·latent】ExplainPanel `request_id` double-safety 形同虚设** — `ExplainPanel.tsx:94-96` 的 `.then()` 回调里 `if (myId !== requestIdRef.current) return;` guard 了一个空 body(真正的 setState/pushHistory 在 `fetchExplain` 内部、`.then()` 之前执行)。实际靠 `signal.aborted` 兜底,测试仍过。不影响功能,但与注释/测试名声称的"双重保险"不符。
5. **【功能·待办】M6 i18n** — 留待阶段 5。tense/zone 标签等硬编码中文,无 i18n 框架。

### ⏭️ 下次开工方向(待用户定)
- **阶段 5 候选:** TTS 发音集成 / 接真实 AI provider(Ollama 或云端)/ M6 i18n / 修上面 #3 时态误判
- 或先清技术债:修 #1 环境根治 + #2 预存测试

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
