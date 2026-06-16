# Grammar Lab 开发日志

> 按阶段倒序记录开发过程、关键决策与踩过的坑。

---

## M2 - 句剖析分析场景(2026-06-14)

### 目标

给「句剖析分析」场景填充真实内容:把英文句子按**语义块**切开(主��/谓语/宾语/状语/从句),用色块展示句子的"解剖架构",并支持教师手动修正 spaCy 的误判。

### 关键决策

1. **后端用 spaCy 真实分析,而非规则启发式**
   - `en_core_web_sm` 已在跑,能直接提供 POS、依存关系、分句。
   - 验证后确认它对复合句的依存分析有缺陷(见下文「坑」),但这恰恰证明了手动编辑功能的必要性。

2. **语义块切割,而非逐词词性色块**
   - 用户明确要求"以语义块的形式切割,而非纠结于每个单词的词性"。
   - 实现上:遍历整句 token,按 `dep_` 归类角色(主语/谓语/宾语/状语/从句),连续同角色 token 合并成一个块。

3. **精简为两大模块**(原计划三个,砍掉句子骨架四槽位)
   - 用户反馈"句子骨架(四槽位)有些冗余,把 ① ③ 做好做精细即可"。
   - 最终:① 语义块流式色带(主视图)② 主从分句分解。

4. **手动编辑模式:以词为单位的拖拽搬移**
   - 用户原话:"语义块用不同颜色的框框住不同成分,教师可以拖动框将不属于某成分的词排除,或框选进本应属于其中的内容"。
   - 实现成 HTML5 Drag and Drop,词为最小单位,不引入新依赖。
   - 仅本会话生效(项目无 git 持久化之外的存储层),含撤销栈和重置。

5. **anatomy 数据流与 tense 解耦**
   - 各场景各发各的请求(`/api/tense/analyze` vs `/api/anatomy/analyze`),与阶段 1 模式对称。
   - `SentenceAnalysis` 上加 `anatomy` 字段,与 `tenses` 并存。

### 踩过的坑

1. **spaCy `en_core_web_sm` 对复合句的依存分析缺陷**
   - 例:`When I arrived, she was reading.` —— spaCy 把从句树错误挂在 `was`(aux)下,导致 `token.subtree` 把主语 `she` 并入谓语块。
   - 例:`The students who finished the homework left early.` —— spaCy 把名词 `students` 当 ROOT,动词 `left` 错挂到 `homework` 下。
   - **解决**:放弃用 `token.subtree` 切块,改为**逐词归类**——遍历整句,按每个 token 的 `dep_` 决定角色,用从句根 token 的 `subtree` 集合标记 in-clause 词。这样即便 spaCy ���树结构有误,词级归类仍能产出合理结果。
   - **残余**:个别句型仍会误判(由手动编辑兜底)。

2. **从句未从父块剥离 → 语义块文本重复**
   - 第一版定语从句的 subtree 挂在先行词下,导致主语块 `The boy` 实际包含 `The boy who I met yesterday`。
   - **解决**:从句子树单独识别 + 从父块排除。

3. **React Hooks 规则错误 → 编辑态白屏**
   - 把 `useMemo` 写在三元运算符分支 `isEditing ? workingChunks : useMemo(...)` 里。
   - `isEditing` 切换时 Hook 调用数量变化,React 抛 "Rendered more hooks than during the previous render",整个组件树崩溃 → 白屏。
   - **解决**:`useMemo` 提到条件外无条件执行。低级错误,记此为戒。

4. **拖拽默认插到末尾**
   - 初版 drop handler 固定用 `chunk.words.length` 作插入位置,完全没追踪鼠标位置。
   - **解决**:新增 `computeInsertIndex()`,遍历目标块内词元素,用每个词中点 X 坐标判断鼠标落在哪个间隙。

5. **完成编辑后结果丢失**
   - 展示态用 `backendChunks`(从后端原始数据派生),编辑态用 `workingChunks`。点「完成」切回展示态 → 编辑全没。
   - **解决**:`workingChunks` 作为唯一展示源,编辑只改它,完成后保留。只有「重置」才回 backend。

6. **换例句后句剖析显示旧句子**
   - `analyzeSentence` 换句时仍保留旧 anatomy 引用;句剖析场景下「开始分析」只触发 tense 不触发 anatomy。
   - **解决**:`analyzeSentence` 检测 `sentenceChanged` 时清空 anatomy;`handleAnalyze` 在 anatomy 场景同步触发 `analyzeAnatomy`。

7. **编辑态点选块不响应 → 改角色按钮永远灰着**
   - `ChunkBlocks.tsx` 的块 `onClick` 条件是 `!isEditing && !isPunct`——编辑态下点块完全没反应。
   - 但 `EditToolbar` 的「改角色」按钮是按 `selectedRole` 是否非空启用的。编辑态下点不动块 → 永远没选中 → 改角色按钮永远 disabled。
   - 致命矛盾:编辑态核心功能(改角色)在编辑态下走不通。
   - **解决**:把条件改成 `if (!isAllPunct)`——编辑态和展示态都允许点选块(词 `<span>` 单独元素不冒泡,点词仍是拖拽起点,两者不冲突)。

8. **后端把实词判成 punct → 教师拖不出**
   - 例句 `The cat ... is black.` 的表语 `black` 被分到 `role:"punct"` 块。
   - `ChunkBlocks` 用 `isPunct = chunk.role === 'punct'` 一刀切,punct 块所有词 `draggable=false`。
   - 结果:后端误判的实词被「标点保护」反向锁死,教师永远救不出来——这恰好违背了「手动编辑兜底 spaCy 误判」的设计初衷。
   - **解决**:把块级 punct 判定改成「块内所有词全是标点符号才锁」,引入 `isPurePunctuation(word)` 工具函数。纯标点(, . ! ?)仍不可拖;混着实词的块(无论 role)全可拖。后端分析器暂不改,前端兜底更稳。

### 文件清单

**新增(后端)**:
- `backend/grammar_engine/anatomy_analyzer.py` — spaCy 语义块/分句分析核心

**新增(前端)**:
- `src/renderer/components/anatomy/ChunkBlocks.tsx` — 语义块色带 + 编辑拖拽
- `src/renderer/components/anatomy/EditToolbar.tsx` — 编辑工具条
- `src/renderer/components/anatomy/ClauseBreakdown.tsx` — 分句分解卡片
- `src/renderer/utils/roleColor.ts` — 角色→配色映射

**修改**:
- `backend/grammar_engine/models.py` — Chunk/Clause/ClauseElement/AnatomyResponse
- `backend/app.py` — `/api/anatomy/analyze` 端点
- `src/main/ipc/index.ts` — `analyze-sentence-anatomy` handler
- `src/preload/index.ts` — `analyzeAnatomy` 暴露
- `src/renderer/state/appState.ts` — `analyzeAnatomy` action + 换句清空 anatomy
- `src/renderer/types/index.ts` — AnatomyBackend 等类型
- `src/renderer/components/anatomy/AnatomyScene.tsx` — 场景编排 + 编辑状态机
- `src/renderer/App.tsx` — anatomy 数据流 + 场景切换自动拉取

### 验证

- ✅ 后端端点 curl 多句通过(简单句、含定语/状语/宾语从句)
- ✅ TypeScript 编译零错误
- ✅ electron-vite 构建 main/preload/renderer 全部成功
- ✅ 端到端:时间轴 + 句剖析两场景正常,拖拽编辑、完成保留、换例句重分析均经人工验证通过

### 已知局限

- spaCy `en_core_web_sm` 对个别复杂句(名词+定语从句+动词)会误判 ROOT,由手动编辑功能兜底。
- 编辑结果仅本会话生效,未持久化。

---

## M1 - 时间轴分析场景(2026-06-13)

详见 `docs/PROGRESS.md` 阶段 1 章节。9 种时态识别 + 时间轴可视化,mock 后端。

---

## M0 - 基础框架(2026-06-12)

Electron + React + TypeScript + Vite + Tailwind,三个场景容器,布局组件。
