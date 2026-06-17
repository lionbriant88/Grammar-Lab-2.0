# Grammar Lab 开发日志

> 按阶段倒序记录开发过程、关键决策与踩过的坑。

---

## 2026-06-17 M3a+1 — 句扩展写路径与视觉重塑

[按倒序记]

### 阶段切分(方案 B:垂直切分,后端优先)

- M3a+1.1 后端写路径:`/api/expansion/apply` 端点 + apply_template 拼装器 + Validator 4 级
- M3a+1.2 前端最小闭环:history[] + SentenceVersion 快照 + Undo/Redo
- M3a+1.3 视觉重塑:Inspector 化 + 嵌套右栏 + Quota DFS + 底栏 timeline
- M3a+1.4 收尾:50 步上限 + 键盘快捷键 + 全链路验证

### 架构铁律(用户 2026-06-17 确认)

- 后端 100% stateless(无 session_id,响应只含 sentence/phrases/warnings/validation)
- 后端是唯一句法权威(前端永不自造 PhraseNode)
- 1 apply = 1 SentenceVersion 快照(不存 patch,不合并)
- Quota 是前端 DFS 派生(后端响应永不含 quota 字段)
- Validator 顾问非权威(/apply 永远 200,severity 4 级包装)
- 画布 phrase-level 平铺(永远不出现 token 卡片)
- M3b 接 Benepar 时只换 phrase_segmenter 函数体,不动 apply / history / UI

### 踩坑/决策

- 拼装规则按 base 句重算位置(不依赖 history[]),V1+V2+V3 累加语义自然成立
- timeline 支持跳任意版本 + 从中分支(M5 Version Tree 演化留接口)
- 50 步上限触发截断后顶栏弹 toast,原句永远保留
- Quota DFS 简化版:只看 children_ids 递归,child.type 映射到 parent 上的 kind

### 验证

- pytest 26/26 通过(M3a 11 + M3a+1.1 15,1 skipped)
- curl 4 端点全 200
- tsc --noEmit 零错
- npm run build 全链路
- Electron 端到端 4 阶段联测
- Vitest 1/1 通过(50 步截断)

---

## M3a - 句扩展 Grammar Engine(phrase-level)+ 只读三栏 UI(2026-06-16)

### 目标

交付句扩展模块的**最小可验证骨架**:后端 Grammar Engine(phrase-level 数据模型)+ 前端只读三栏 UI(扩展类型库 / 句子画布 / 短语结构图)。M3a 严格只读,不做提交闭环。

### 核心设计精神

**数据模型稳定优先于分析精度**:M3a 目标是验证 Grammar Engine 的数据模型稳定性,不是实现最终句法分析器。优先保证 `PhraseNode` 可扩展(M3b/M3c 不改数据结构)、Parent-Child 可挂载、VP 特征完整——保证 M3b 接 Benepar / M3c 接 LanguageTool 时无需重构。

### 关键决策

1. **phrase-level 数据模型(非 token 级)**
   - 扩展单位是 NP/VP/PP/Clause,不是单个 token(原则 #1/#2)。
   - `PhraseNode` 是数据契约:含 `features`(特征槽)+ `parent_id`/`children_ids`(挂载)。
   - 规则库查询键是 `PhraseType`(NP_RULES),不是 token POS。

2. **调整 1:Parent-Child 挂载消除漂浮**
   - `PhraseNode` 加 `parent_id`/`children_ids`;segment() 内部建立 PP→相邻 NP/VP 挂载。
   - 例 `likes the dog in the park` → PP(`in the park`).parent_id = NP(`the dog`),父节点 children_ids 回填。
   - M3a 右栏不显示嵌套(扁平短语序列),但数据具备树能力(M3b/M3a+1 可视化)。

3. **调整 2:VP 吞完整时态链**
   - 从主动词回溯吞 auxiliaries + modal + main verb + particles(prt dep)。
   - `has been working` → 一个 VP,tense=`present_perfect_progressive`,aux_chain=`[has,been]`。
   - `would like` → 一个 VP,modal=`would`;`to help`(xcomp)不纳入,留 M3b。

4. **调整 3:右栏命名「短语结构图」而非「成分句法树」**
   - M3a 尚未引入 Benepar,当前只是 spaCy 的 phrase grouping,叫「成分句法树」是过度承诺。
   - 组件文件名 `ExpansionTree.tsx` 不变,仅 UI 标题文案 M3b 升级。

5. **Validator 只实现主谓一致,其余 4 项签名齐返回 PASS**
   - 直接读短语特征槽(不重新做 token 级句法分析),这是 phrase-level 模型的红利。
   - `He like dogs.` → auto-correction `{from:"like", to:"likes"}`。
   - 其余 4 项(tense_consistency/clause_completeness/non_finite/relative_pronoun)函数签名齐、返回 PASS,供 M3b/c 接入。

6. **IPC 链路复制 M2 anatomy 模式**
   - `ipc/index.ts`/`preload`/`appState.ts`/`App.tsx` 全部复制 anatomy 版,改名字和 URL。三段重复是已知问题,M3 结束后抽 `forwardToBackend(path)` 工具重构。

7. **UI 风格对齐 anatomy 场景**
   - 复用 anatomy 的容器(`p-6 rounded-2xl border`)、卡片、徽章、`darkMode`、`animate-fade-in` 风格。
   - 短语配色与角色色对齐:NP=蓝、VP=绿、PP=琥珀(新 utils/phraseColor.ts)。

### 踩过的坑

1. **spaCy 把 `like` 误标 ADP(主谓一致兜底)**
   - `He like dogs.` —— spaCy en_core_web_sm 把 `like` 标成 `ADP/ROOT`,无 Tense morph,导致 VP tense=`unknown`,主谓一致检查不触发。
   - 修复:Validator 加兜底——tense=unknown 且无 modal/aux 时按 simple present 处理;segmenter 加 `VERB_LEMMA_FALLBACK`(高频动词 lemma 白名单)识别谓语头。
   - 这是 spaCy 精度问题的工程兜底,符合「数据模型稳定优先于精度」精神。M3b 接 Benepar 后这类误标应大幅减少。

2. **代词 NP 不应可扩展**
   - 初版规则给所有 NP adj/number 候选,导致 `NP(I)` 也高亮可扩展(能说 "cute I"?)。
   - 修复:engine 里 head_pos==PRON 的 NP 标记 is_expandable=False。

3. **`pytest` 不在项目环境**
   - requirements.txt 未列 pytest。本次 `pip install pytest` 到项目用的全局 Python 3.12。后续应补进 requirements.txt(本次未擅动)。

4. **appState.ts 编辑误删尾部**
   - 一次 Edit 的 old_string 含 `\r\n` 换行未精确匹配,导致文件尾部(clearError/return/闭合括号)被误删。重读确认后用唯一锚点重建尾部。教训:Windows CRLF 文件做大段 Edit 前先确认换行,或用更小的唯一锚点。

### 验证状态

- ✅ `pytest backend/tests/test_expansion_engine.py` 15 测试全过(覆盖 spec §5.1 的 11 项区域)
- ✅ `curl /api/expansion/analyze` 三例通过(I like dogs. / He has been working hard. / likes the dog in the park)
- ✅ `npx tsc --noEmit` 零错误
- ✅ `npm run build` main/preload/renderer 全链路通过
- ✅ Electron 窗口人工验证(2026-06-16):三栏布局 / 短语画布特征槽徽章 / 可扩展高亮+绿点 / 不可扩展灰显 / [+]菜单显示模板 / 右栏「短语结构图」扁平结构 / 点树叶子联动中栏

### 路线图(M3a 之后)

- **M3a+1**(Phase 1 写路径):提交闭环、新增高亮、连线、动态 Expansion Tree、Parent-Child 可视化、Depth 限制
- **M3b**(Phase 2):装 Benepar,`phrase_segmenter` 换实现;PP/participle/infinitive phrase 扩展(含 `to help`);Validator tense_consistency 实现;右栏升级命名为「成分句法树」
- **M3c**(Phase 3):接 LanguageTool;relative/adverbial/noun clause 扩展;Validator 其他 3 项实现 + 关系代词匹配

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
