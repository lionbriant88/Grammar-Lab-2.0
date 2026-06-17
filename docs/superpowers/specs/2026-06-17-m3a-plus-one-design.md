# M3a+1 — Sentence Expansion 写路径 + 视觉重塑

> 设计稿日期:2026-06-17
> 状态:已确认(用户 2026-06-17 逐节确认 §1-§5),进入实施
> 前置:M3a(commit `5c9a433`,2026-06-16)只读骨架已交付
> 关联:M3a spec `2026-06-16-sentence-expansion-m3a-design.md`、M3a 路线图"M3a+1(Phase 1 写路径)"

---

## 1. 概览与 M3a+1 范围

### 1.1 一句话定位

M3a 让学生**看**句子的可扩展面(只读骨架)。M3a+1 让学生**做**——从原句开始,逐短语选择 adj/adv/num/degree,提交后画布 phrase 重画,底栏 timeline 记每步,Undo 任意回退。**后端是唯一句法权威,前端 history 是唯一时间机器。**

### 1.2 阶段切分(方案 B:垂直切分,后端优先)

| 阶段 | 范围 | 验证标准 |
|---|---|---|
| **M3a+1.1** 后端写路径 | `/api/expansion/apply` 端点 + PhraseNode → sentence 拼装器 + Validator 接 /apply(顾问模式,4 级 PASS/INFO/WARNING/ERROR) | pytest + curl,响应 200 + 完整 `ExpansionApplyResponse` |
| **M3a+1.2** 前端最小闭环 | IPC `apply-expansion` + preload `applyExpansion` + appState `applyExpansion` + history[]/currentIndex + 复用 M3a 浮层"应用"按钮 | Electron:点 [+]→点"应用"→画布 phrase 重画,Undo 回退 |
| **M3a+1.3** 视觉重塑(设计稿落地) | 拆 M3a 浮层 → Inspector 化中栏下方面板;ExpansionTree → 嵌套卡片(对齐设计稿"嵌套+缩进无箭头");底栏 timeline 替换简单 Undo 按钮;Quota DFS 派生 + 卡片左上角微型 chip;已扩展视觉态(蓝边+金色角标) | Electron 端到端,visual 验证 |
| **M3a+1.4** 收尾 | history 上限 50 截断 + 键盘快捷键(Cmd+Z / Cmd+Shift+Z) + tsc + npm run build + DEVLOG | 全链路通过 |

### 1.3 关键约束(贯穿全部 4 个阶段)

| 约束 | 来源 | 影响 |
|---|---|---|
| 后端 100% stateless | 用户铁律 | 无 session_id,无后端 history,响应只含 sentence/phrases/warnings/validation |
| 后端是唯一句法权威 | 用户铁律 | 前端永不自造 PhraseNode、不调 spaCy、不重算 phrase;提交后端→拿完整响应→替换 |
| Quota 是前端派生 | 用户铁律 | 配额 = DFS 数当前 phrase 树的 modifier,对照静态规则表;后端响应永不含 quota 字段 |
| 1 apply = 1 SentenceVersion | 用户铁律 | history[] 存完整快照,不存 patch,不合并 |
| Validator 顾问非权威 | 用户铁律 | /apply 永远 200,Validator 永不阻断;4 级 PASS/INFO/WARNING/ERROR 都是教学信息 |
| 画布 phrase-level 平铺 | 用户铁律 | 画布不出现 token 级卡片;`I like dogs.` → `I like cute dogs.` 是 `[I] [like] [cute dogs]`,**不是** `[I] [like] [cute] [dogs]` |
| M3b 接 Benepar 时不动 apply | 用户铁律 | `phrase_segmenter()` 函数体可换,/apply / history / UI 不受影响 |
| 视觉风格:Apple+Notion+Figma+VSCode,desktop ≥1400px,无 SVG 箭头 | 设计稿 | 中栏 Inspector 化,右栏嵌套卡片,底栏 timeline |
| 拼装规则按 base 句重算位置 | 用户 2026-06-17 | apply_template 不依赖 history[],V1+V2+V3 累加语义自然成立 |
| timeline 支持跳任意版本 + 从中分支 | 用户 2026-06-17 | Undo 跳到 v1 后可 redo 或 apply 新 template(走 history 截断 + 追加) |

### 1.4 不做(明确划线)

- ❌ L2 短语扩展(PP / participle / infinitive)— **M3b**(装 Benepar)
- ❌ L3 从句扩展 + 关系代词匹配 — **M3c**(接 LanguageTool)
- ❌ Validator 5 项完整实现(M3a+1.1 仅接主谓一致 + 4 级包装,其他 4 项仍是占位签名)
- ❌ localStorage 持久化 — **M4**
- ❌ .glab 项目文件 / Version Tree 分支 — **M5**
- ❌ AI 集成 — **M4**

---

## 2. M3a+1.1 后端写路径

### 2.1 API 设计

```
POST /api/expansion/apply
Content-Type: application/json

Request:
{
  "sentence": "I like dogs.",          // 当前句子(M3a 重跑 analyze 后的最新句)
  "phrase_id": "p2",                    // 目标短语 id(必须在 sentence 的 phrases 里)
  "template_id": "tpl_adj_cute",        // 要套的模板 id
  "mode": "offline"
}

Response (HTTP 200, 总是 200,Validator 不阻断):
{
  "sentence": "I like cute dogs.",      // 拼装后的新句
  "phrases": [ ...完整 PhraseNodeInfo[],与 /analyze 同结构... ],
  "warnings": [ "原句已带 'cute' 的近似词" ],     // 来自重识别
  "validation": {
    "severity": "WARNING",              // PASS / INFO / WARNING / ERROR
    "is_valid": false,                  // 兼容旧字段:severity != ERROR 时为 true
    "errors": [ ... ],
    "warnings": [ "主谓不一致:..." ],   // 旧字段保留
    "infos": [ ... ],                   // 新增
    "auto_corrections": [ ... ]
  }
}
```

**关键决策**:
- 请求里**传 sentence + phrase_id**,不传 base_phrases。
- 响应**只含** `sentence / phrases / warnings / validation` 四字段。**不含** quota、**不含** version_id、**不含** session_id。
- Validator severity 是 4 级枚举(M3a 是布尔 is_valid,这是扩展),旧 `is_valid` 字段保留兼容:`severity == ERROR` → `is_valid=false`,否则 `is_valid=true`。

### 2.2 流水线(`/api/expansion/apply` 实现)

```
Input: {sentence, phrase_id, template_id}
        │
        ▼
1. spaCy → doc, segment(doc) → base_phrases
2. 在 base_phrases 里查 phrase_id → 目标 PhraseNode  + 查 template_id → Template
3. 拼装新句: apply_template(phrase, template, sentence) → new_sentence
4. 重跑 analyze(new_sentence) → new_phrases (含新 warnings)
5. 调 Validator(完整 5 项,M3a+1.1 实际只有主谓一致实装,4 项占位)
6. 包装 4 级 severity → ValidationReport
7. 返回 {sentence: new_sentence, phrases: new_phrases, warnings, validation}
```

**步骤 3 的 apply_template**——核心新逻辑,放在 `expansion_engine.py` 同模块,签名 `apply_template(phrase, template, sentence) -> str`。

**拼装规则表**(基于 base 句的当前 phrase 文本,**不依赖 history**):

| kind | 拼装规则 | 例 |
|---|---|---|
| `adjective` | 插到 head 之前,所有已有 adj 之后;num 仍保持在 adj 之前 | `the dogs` + `cute` → `the cute dogs` <br> `the three dogs` + `cute` → `the three cute dogs` |
| `number` | 插到 head 之前,所有 num 之后(quota 已满由前端拦截,后端不再拦) | `the dogs` + `two` → `the two dogs` <br> `a dog` + `two` → `two dogs`(a 移除) |
| `adverb` | 插到 VP 第一个词(aux/modal 之后、main verb 之前);已有 adv 加到最前 | `likes` + `really` → `really likes` <br> `would like` + `really` → `would really like` |
| `degree_adverb` | 插到 ADJP head 之前,所有已有 degree 之后 | `cute` + `very` → `very cute` <br> `very cute` + `extremely` → `very extremely cute` |

**拼装规则的边界**(spec 必填):
- 找不到 phrase_id → HTTP 200 + `warnings: ["phrase_id 'pX' not found"]` + `phrases` = 原 base_phrases,**不抛异常**
- 找不到 template_id → 同上,warnings
- kind 拼装失败(如 kind=adjective 但 target 实际是 PP)— 同上,warnings
- **永不返回 4xx**(除 503 后端未启动外);试错必须允许

### 2.3 Validator 接 /apply(4 级 severity)

`expansion_validator.py` 改造:

```python
Severity = Literal["PASS", "INFO", "WARNING", "ERROR"]

@dataclass
class ValidationReport:
    severity: Severity = "PASS"          # 主字段
    is_valid: bool = True                # 兼容:severity=="ERROR" 时 False
    errors: list[str]
    warnings: list[str]
    infos: list[str]                     # 新增
    auto_corrections: list[dict]
```

**5 项 check 的 severity 映射**(M3a+1.1):
- `validate_subject_verb_agreement`:触发 auto_correction → `WARNING`(教学提示,不是阻断)
- 4 项占位 check:保持原 `is_valid=True`,severity=`PASS`
- `INFO` 留给 M3b/c(目前无 INFO 触发场景)

**`validate(sentence, doc, phrases)` 的 severity 聚合规则**:`max(各 check severity)`,`PASS < INFO < WARNING < ERROR`。

### 2.4 文件改动(M3a+1.1)

| 文件 | 改动 |
|---|---|
| `backend/grammar_engine/expansion_engine.py` | 新增 `apply_template(phrase, template, sentence) -> str` + 新增 `apply(sentence, phrase_id, template_id) -> dict` 顶层入口 |
| `backend/grammar_engine/expansion_validator.py` | 加 `Severity` 类型 + ValidationReport 加 `severity/infos` 字段,severity 聚合逻辑 |
| `backend/grammar_engine/models.py` | 新增 `ApplyRequest` / `ExpansionApplyResponse` / 新版 `ValidationReport`(BaseModel 版) |
| `backend/app.py` | 追加 `POST /api/expansion/apply` 端点 |
| `backend/tests/test_expansion_engine.py` | 追加 §2.5 描述的 8 项测试 |

**M3a 既有 `analyze()` 路径不动**。`apply` 是新入口。

### 2.5 测试策略

`test_expansion_engine.py` 追加(共 8 项,M3a 11 项保留):

1. `test_apply_adjective_prepend`:`I like dogs.` + phrase `p2`(NP dogs) + `tpl_adj_cute` → 新句 `I like cute dogs.`,phrases 数量 ≥ 3,新句里 `cute` 出现
2. `test_apply_adverb_prepend_after_aux`:`She would like it.` + VP(like) + `tpl_adv_really` → `She would really like it.`(really 插到 aux 后、main 前)
3. `test_apply_degree_adverb`:`The dog is cute.` + ADJP(cute) + `tpl_dadv_very` → `The dog is very cute.`
4. `test_apply_number_replaces_determiner`:`I saw a dog.` + NP(a dog) + `tpl_num_two` → `I saw two dogs.`(a 移除)
5. `test_apply_phrase_id_not_found`:`I like dogs.` + `p99` + `tpl_adj_cute` → 200 + warnings 含 `phrase_id 'p99' not found` + phrases=原句 phrases
6. `test_apply_template_id_not_found`:`I like dogs.` + `p2` + `tpl_adj_nonexistent` → 200 + warnings 含 `template_id 'tpl_adj_nonexistent' not found` + phrases=原句 phrases
7. `test_apply_validator_subject_agreement_warning`:在 M3a 既有 `He like dogs.` 测例基础上,触发 `validate_subject_verb_agreement` 后 severity == "WARNING",`is_valid` 字段保留
8. `test_apply_response_shape`:`I like dogs.` + `p2` + `tpl_adj_cute` → 响应含 `sentence / phrases / warnings / validation` 四字段,validation.severity ∈ {PASS, INFO, WARNING, ERROR}

### 2.6 不在 M3a+1.1 做的

- Quota 校验(配额是前端 DFS,后端不查)
- 持久化(version_id / session_id)
- Validator 4 项占位的真实实现(留 M3b/c)
- AI 生成(template 是 L1 模板集,无 AI)

---

## 3. M3a+1.2 前端最小闭环

> 范围:在 M3a 浮层基础上加"应用"按钮接 IPC,前端 history 启动。**保持 M3a 视觉不变**(Inspector 化留 M3a+1.3)。
> 目标:点 [+] → 选模板 → 点"应用" → 画布 phrase 重画;点 Undo → 回退。

### 3.1 数据流总览

```
用户点 ExtensionMenu「应用」
       │
       ▼
ExtensionMenu 调用 onApply(phraseId, templateId) 回调
       │
       ▼
ExpandScene.handleApply(phraseId, templateId)
       │
       ▼
actions.applyExpansion(currentSentence, phraseId, templateId)  // appState
       │
       ▼
window.electronAPI.applyExpansion(sentence, phraseId, templateId)  // preload
       │
       ▼
IPC: 'apply-expansion'  // main process
       │
       ▼
fetch POST /api/expansion/apply  // backend (M3a+1.1)
       │
       ▼
返回完整 ExpansionApplyResponse
       │
       ▼
appState 收到响应 → 推入 history[] → 更新 currentIndex
       │
       ▼
setCurrentAnalysis 合并 expansion.backend → 触发 ExpandScene 重渲染
       │
       ▼
SentenceCanvas 用新 phrases 渲染(画布自动重画)
```

### 3.2 前端 history 模型(类型扩展)

`src/renderer/types/index.ts` 新增:

```typescript
// 一次 apply 操作的元信息(用于底栏 timeline 展示 + Undo/Redo 跳转)
export interface ApplyActionSummary {
  phrase_id: string;       // 目标短语
  phrase_text: string;     // 目标短语文本(快照时不需重跑)
  template_id: string;     // 套用模板
  template_surface: string;// 模板词(cute / really ...)
  kind: string;            // adjective / adverb / number / degree_adverb
  kind_label_cn: string;   // 形容词 / 副词 / ...
}

// 一个 SentenceVersion 快照(history 数组里的一项)
export interface SentenceVersion {
  version_id: string;      // 前端生成(uuid),仅用于 timeline 标识
  sentence: string;        // 该版本的完整句子
  phrases: PhraseNodeInfo[]; // 该版本的完整 phrases
  warnings: string[];
  validation: ValidationReport;  // 后端返回的验证报告
  action_summary: ApplyActionSummary | null;  // null = 原句(第一个版本)
  timestamp: number;       // Date.now()
}

// ValidationReport 类型也新增到前端
export type ValidationSeverity = 'PASS' | 'INFO' | 'WARNING' | 'ERROR';

export interface ValidationReport {
  severity: ValidationSeverity;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  infos: string[];
  auto_corrections: Array<{ from: string; to: string; reason: string }>;
}
```

**`appState.ts` 新增**:

```typescript
// 新增 state 字段
interface AppState {
  // ... 既有字段
  expansionHistory: SentenceVersion[];   // history 数组
  expansionCurrentIndex: number;          // currentIndex 指针
}

// 新增 actions
interface AppActions {
  // ... 既有 actions
  applyExpansion: (sentence: string, phraseId: string, templateId: string) => Promise<void>;
  undoExpansion: () => void;
  redoExpansion: () => void;
}
```

**history 数组规则**:
- `expansionHistory[0]` = 原句(初始 `/analyze` 响应,`action_summary: null`)
- `expansionHistory[N]` = 第 N 次 apply 后的快照
- `expansionCurrentIndex` 初始 0,apply 后 +1
- **新 apply 会截断** future:如果 `currentIndex < length - 1` 时 apply,先截断 `[currentIndex+1:]` 再追加(标准 Undo 栈行为)
- **50 步上限**:`expansionHistory.length > 50` 时,从头部截断(保留最新 50),`currentIndex` 同步调整(M3a+1.4 实现,M3a+1.2 先不卡)
- `Undo` → `currentIndex--`,把 `expansionHistory[currentIndex]` 写到 `currentAnalysis.expansion.backend`
- `Redo` → `currentIndex++`,同上
- **支持跳任意版本 + 从中分支**(2026-06-17 确认):Undo 到 v1 后可 redo 或 apply 新 template,新 apply 走 history 截断 + 追加 = 产生分支

**关键:Undo/Redo 绝不调后端**。只改 currentIndex + 替换 `currentAnalysis.expansion.backend`。**完全 stateless**。

### 3.3 IPC 链路(沿用 M3a 复制粘贴模式,M3 结束后再抽)

`src/main/ipc/index.ts` 新增 handler:
```typescript
ipcMain.handle('apply-expansion', async (_event, sentence: string, phraseId: string, templateId: string) => {
  // 与 M3a 的 analyze-expansion handler 复制粘贴变体
  const response = await fetch(`${BACKEND_URL}/api/expansion/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sentence, phrase_id: phraseId, template_id: templateId, mode: 'offline' }),
  });
  // 同样的 ok 判断 + 503 错误处理
});
```

`src/preload/index.ts` 新增:
```typescript
applyExpansion: (s: string, p: string, t: string) =>
  ipcRenderer.invoke('apply-expansion', s, p, t),
// 类型同步扩展 ElectronAPI
```

### 3.4 浮层"应用"按钮接 handler

`ExtensionMenu.tsx` 修改:
- 移除 disabled + tooltip "提交功能 M3a+1 开放"
- props 加 `onApply: (templateId: string) => void` + `isApplying: boolean`
- 模板 chip 从 `<div>` 改为 `<button>`,点击调 `onApply(t.template_id)`
- "应用"按钮删除(单个 chip 点击即应用,**不弹二次确认**——M3a+1.1 已经 accept 试错)
- 应用中状态:`isApplying=true` 时所有 chip 显示 loading

`ExpandScene.tsx` 新增 handler + 透传:
```typescript
const handleApply = useCallback(async (phraseId: string, templateId: string) => {
  if (!backend) return;
  await onApplyExpansion(backend.sentence, phraseId, templateId);
  setMenuOpenFor(null);  // 关闭浮层
  setHighlightedId(phraseId);  // 持续高亮该短语
}, [backend, onApplyExpansion]);
```

**注**:`onApplyExpansion` 这个 prop 名是 M3a 现有的,语义是"触发重新 analyze",现在改名 `onApplyExpansion(sentence, phraseId, templateId)`,签名变化(从单参变三参)。App.tsx 调用处同步改。

### 3.5 浮层选中态(简单的"上一选"视觉)

`ExtensionMenu` 收到当前选中的 templateId(从 `appState` 或 prop 传),让该 chip 显示选中样式(蓝底)。**M3a+1.2 不做"已应用"持久视觉**(那是 M3a+1.3 的"已扩展"卡),只做"本次选择"的临时高亮。**应用成功后 chip 立即消失**(因为浮层关闭 + 画布重画),无需"已应用"态。

### 3.6 底栏简单 Undo/Redo(M3a+1.2 占位)

**M3a+1.2 不做设计稿的 timeline**——只放最简单的两个按钮。

`ExpandScene` 渲染时,在底部加一行:
```tsx
<div className="flex items-center gap-2 mt-4">
  <button disabled={!canUndo} onClick={onUndo}>↶ 撤销</button>
  <button disabled={!canRedo} onClick={onRedo}>↷ 重做</button>
  <span className="text-xs">已应用 {expansionCurrentIndex} 个扩展</span>
</div>
```

`canUndo/canRedo/expansionCurrentIndex` 从 `appState` 取值。`App.tsx` 透传 `onUndoExpansion / onRedoExpansion` 到 ExpandScene。

**M3a+1.3 替换**为设计稿的 vertical timeline(纵向时间线,展开看每步 action_summary)。

### 3.7 状态机补充(M3a + M3a+1.2)

```
空态 ──[analyze]──> loaded(phrases)
loaded ──[点 [+] ]──> loaded + menuOpenFor=phraseId
menuOpenFor ──[点 chip]──> loaded + isApplying
isApplying ──[成功]──> loaded + 画布重画(backend 已替换)+ menuOpenFor=null
isApplying ──[失败]──> loaded + error + menuOpenFor 不变(用户可重试)
loaded ──[点 Undo]──> loaded(history[currentIndex-1] 替换 backend)
loaded ──[点 Redo]──> loaded(history[currentIndex+1] 替换 backend)
```

### 3.8 文件改动(M3a+1.2)

| 文件 | 改动 |
|---|---|
| `src/renderer/types/index.ts` | 新增 `SentenceVersion / ApplyActionSummary / ValidationReport / ValidationSeverity` |
| `src/renderer/state/appState.ts` | 新增 `expansionHistory / expansionCurrentIndex` state + `applyExpansion / undoExpansion / redoExpansion` actions |
| `src/main/ipc/index.ts` | 新增 `apply-expansion` handler(M3a analyze 的复制粘贴变体) |
| `src/preload/index.ts` | 新增 `applyExpansion(s, p, t)` + 类型扩展 |
| `src/renderer/components/expand/ExtensionMenu.tsx` | 启用"应用"按钮 → 模板 chip 可点 |
| `src/renderer/components/expand/ExpandScene.tsx` | 新增 handleApply + 透传 onApplyExpansion + 底栏简单 Undo/Redo |
| `src/renderer/App.tsx` | 透传 `onApplyExpansion / onUndoExpansion / onRedoExpansion` 到 ExpandScene |

### 3.9 验证(端到端)

1. `npm run build` 零错
2. 启动后端 + Electron,默认句 `I usually get up at seven every morning.`
3. 切到「句扩展」,等加载
4. 找到 `morning` 对应的 NP 卡片,点 [+]
5. 弹浮层,点 `cute` chip → 画布自动刷新,`morning` 变成 `cute morning`,`已应用 1 个扩展`
6. 再点同一个 NP 的 [+] → 点 `early` → `cute early morning`,`已应用 2 个扩展`
7. 点「↶ 撤销」→ 回到 `cute morning`,`已应用 1 个扩展`
8. 点「↶ 撤销」→ 回到原句,`已应用 0 个扩展`
9. 点「↷ 重做」→ 回到 `cute morning`
10. 切到 timeline / anatomy 场景再切回 expand,history 应保留(M3a+1.2 不持久化,刷新页面会丢)

### 3.10 不在 M3a+1.2 做的

- Inspector 化(中栏下方面板)— M3a+1.3
- 嵌套卡片右栏 — M3a+1.3
- 底栏 timeline — M3a+1.3
- Quota DFS + 卡片 chip — M3a+1.3
- 已扩展视觉态(蓝边+金色角标)— M3a+1.3
- history 50 步上限 — M3a+1.4
- 键盘快捷键(Cmd+Z)— M3a+1.4

---

## 4. M3a+1.3 视觉重塑(本次设计稿落地)

> 范围:1.2 跑通闭环后,按设计稿重塑中栏 / 右栏 / 底栏,加 Quota DFS 派生 + 已扩展视觉态。
> 原则:**画布 phrase-level 平铺永远不变**,所有变更在 Inspector 化 + 嵌套卡片 + 底栏 timeline。

### 4.1 整体 Layout(≥1400px desktop)

```
┌────────────────────────────────────────────────────────────────────┐
│  Top toolbar (64px)                                                │
├──────────┬───────────────────────────────────┬─────────────────────┤
│          │   Center (flex)                   │                     │
│  Left    │   ┌─────────────────────────┐     │  Right (360px)      │
│  280px   │   │ Sentence Canvas (画布)  │     │                     │
│          │   │  句子画布              │     │  ┌──────────────┐  │
│  扩展类型│   │  点击短语查看可扩展项    │     │  │ 短语结构图    │  │
│  库      │   │  [I] [like] [cute dogs] │     │  │ 嵌套卡片      │  │
│  (L1)    │   │  DET NP VP NP           │     │  │ Sentence     │  │
│          │   └─────────────────────────┘     │  │  ├─ NP(blue) │  │
│  NOUN    │   ┌─────────────────────────┐     │  │  ├─ VP(blue) │  │
│  adj   7 │   │ Expansion Inspector      │     │  │  └─ NP(green)│  │
│  num   4 │   │  扩展选项: cute dogs(NP)│     │  │     ├─ adj:7 │  │
│  pp 🔒   │   │  形容词(已选 1/2)        │     │  │     ├─ num:4 │  │
│  ...     │   │  [cute✓] [black] [big]  │     │  │     └─ ...    │  │
│          │   │                          │     │  └──────────────┘  │
│  VERB    │   │  数量词(0/1)             │     │                     │
│  adv   6 │   │  [two] [three] [many]    │     │  ┌──────────────┐  │
│  modal🔒 │   │                          │     │  │ 短语信息面板  │  │
│  ...     │   │  介词短语 🔒              │     │  │ current:     │  │
│          │   └─────────────────────────┘     │  │  cute dogs   │  │
│  ADJ     │                                   │  │  type: NP    │  │
│  deg   3 │                                   │  │  head: dogs  │  │
│          │                                   │  │  pos: NOUN   │  │
│          │                                   │  │  role: Obj   │  │
│          │                                   │  │  features:   │  │
│          │                                   │  │  [Plural]    │  │
│          │                                   │  │  [3rd]       │  │
│          │                                   │  │  [Common]    │  │
│          │                                   │  └──────────────┘  │
├──────────┴───────────────────────────────────┴─────────────────────┤
│  Status bar (32px) — Sentence | Phrase count | Expandable | State  │
│  + Vertical Timeline (展开) — 已应用 N 个扩展  [↶] [↷]               │
└────────────────────────────────────────────────────────────────────┘
```

三栏宽度:左 280 / 中 flex / 右 360。Top 64 + Status 32 = 96 固定。背景 `#f8fafc`,卡片 `rounded-xl` (12px),shadow 极淡。

### 4.2 中栏 Sentence Canvas(画布)— 永远 phrase-level 平铺

**承接 M3a+1.2 的 PhraseCard 渲染**。变化点:

1. **取消 [+]** 按钮 — 短语卡片整体可点击,选中态走绿边
2. **新增 Quota chip**(卡片左上角)— `2/2 adj` 灰底,小号字
3. **新增「已扩展」视觉态** — 蓝边 + 右上角金色已扩展徽章
4. **新增「选中」视觉态** — 绿边
5. **hover 态** — soft shadow

**四种 PhraseCard 视觉态** × 三种 type(NP=蓝 / VP=绿 / PP=琥珀):

| 状态 | 边框 | 角标 | 说明 |
|---|---|---|---|
| `default` (不可扩展) | 灰 1px,opacity-50 | 无 | M3a 现状 |
| `expandable` (可扩展未选未加) | 蓝 2px | 右上绿点 ● | M3a 现状,**[+] 按钮移除** |
| `selected` (可扩展,当前 focus) | 绿 2px | 右上绿点 ● | 替换 M3a 的 `+ 扩展` 文本 |
| `extended` (已套过 ≥1 个扩展) | 蓝 2px | 右上金色已扩展徽章 ★ | 蓝边保留以示仍可扩展 |

**画布不变**:
- 画布只显示当前句子的 phrase 列表,**永远是 phrase-level**。`I like dogs.` 加 cute 后画布 = `[I] [like] [cute dogs]`,**不是** `[I] [like] [cute] [dogs]`。
- 短语卡片下方显示 `DET / NP / VP / PP / ADVP` 类型 badge(M3a 现状保留)。
- 不画 SVG / 箭头 / 连线。**所有 Parent-Child 关系只在右栏结构图展示**。

### 4.3 中栏 Expansion Inspector(画布下方)— 全面替换 M3a 浮层

**M3a 的 ExtensionMenu 组件重写为 `ExpansionInspector.tsx`**(M3a+1.3 改文件名,原 `ExtensionMenu.tsx` 替换)。Inspector 永远画在画布下方,**始终在视野内**,不需要弹出。

**Inspector 内容**(对应画布选中的短语):

```
┌─────────────────────────────────────────────────────────────┐
│ 扩展选项: cute dogs (NP)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 形容词 (已选 1/2)                          ←  Accordion L1  │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│ │ cute │ │ black│ │ big  │ │friendly│ │young│ │smart│ ... │
│ │  ✓   │ │      │ │      │ │      │ │      │ │      │     │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │
│                                                             │
│ 数量词 (0/1)                              ←  Accordion L1  │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│ │ two  │ │three │ │ five │ │ many │                       │
│ └──────┘ └──────┘ └──────┘ └──────┘                       │
│                                                             │
│ ▸ 介词短语  (上限已满 / 未开放)              ←  Accordion L2  │
│ ▸ 非谓语短语 (未开放)                        ←  Accordion L2  │
│ ▸ 定语从句  (未开放)                        ←  Accordion L3  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Accordion 行为**:
- L1 类别默认展开(adjective/number/adverb/degree_adverb)
- L2/L3 类别默认折叠 + 灰显 + "未开放" 徽章;若配额已满 0,L1 也折叠 + 灰显 + "Maximum expansion reached"
- 折叠时显示 ✓ 标记的已选数量(如 `介词短语 (上限已满)`)
- 选过 chip 的类别顶部加绿色"已选 N"标签(实时反映 quota used)

**Chip 视觉态**:
- `default`:灰底,圆角 8px
- `hover`:浅色描边
- `selected`(本次选择,等后端响应):蓝底
- `disabled`(配额已满):opacity-50,cursor-not-allowed
- `locked`(L2/L3 未开放):灰底斜纹

**Inspector 顶部空态**(画布无选中):`选中画布中任一短语查看可扩展项`(占位)。

**Inspector 与画布选中联动**:
- 点画布卡片 → 选中态绿边 + 下方 Inspector 滚到 + 渲染该短语的候选
- 点 Inspector 内的 chip → 调 `applyExpansion` → 后端响应 → 画布重画 + Inspector 内容更新(因为选中短语的 phrases 已变)
- 不画布选中态时(用户切到别的场景后回来)— Inspector 重置为空态

### 4.4 右栏 Phrase Structure(嵌套卡片,无箭头)

**承接 M3a 的 ExpansionTree**。M3a+1.3 组件文件名 `ExpansionTree.tsx` 保留(承载内容随阶段演进),内部 UI 标题文案保持"短语结构图"。

**结构**:Sentence → 嵌套短语卡片,无限层级(但 Quota 限了实际增长)。

**视觉规则**:
- 每层 `padding-left: 16px`(缩进,无连线)
- 短语卡片:小卡 + 类型 badge + 文本 + feature chip 缩略
- **可扩展短语**(Quota used < max):蓝边框
- **选中短语**:绿边框 + 软阴影
- **不可扩展短语**:opacity-50

**当 `NP(cute dogs)` 选中时,右栏结构图展开它的子项**:
```
Sentence: "I like cute dogs."

├─ NP(I)         [gray, not expandable]
│   1sg
│
├─ VP(like)      [blue, expandable, 0/2 adv]
│   simple_present
│
└─ NP(cute dogs) [green, selected, 1/2 adj, 0/1 num]
    ├─ adj ✓ cute    (1/2)
    ├─ num     two/three/many  (0/1)
    ├─ pp      ▸ 介词短语  (0/1, locked)
    ├─ part    ▸ 非谓语短语  (0/1, locked)
    └─ relcl   ▸ 定语从句  (0/1, locked)
```

子项按 kind 分组排列,每组:
- L1 可扩展 kind:`形容词 (1/2)` + chip 列表(cute 是已选,灰底带 ✓)
- L2/L3 kind:折叠行,标"未开放"或 quota 状态

**所有点击行为**:
- 短语卡片点击 → 选中(中栏画布同步绿边 + Inspector 更新)
- adj 已选 chip 点击 → **M3a+1.3 不做**撤销——撤销走底栏 timeline 统一,chip 只读显示已选

### 4.5 右栏 Phrase Info(短语信息面板)

固定在右栏下方,展示当前选中短语:

```
┌─────────────────────────────────┐
│ 短语信息                         │
├─────────────────────────────────┤
│ 当前短语:   cute dogs            │
│ 短语类型:   NP                   │
│ 中心词:     dogs                │
│ POS:        NOUN                 │
│ 语法角色:   Object              │
│                                 │
│ 特征:                          │
│ [Plural] [3rd Person] [Common] │
│                                 │
│ 时态(若 VP):                    │
│ [simple_present]                │
└─────────────────────────────────┘
```

**信息全部从 `PhraseNode` 现有字段读**,不需后端新增。

### 4.6 底栏 Status Bar(32px)— 横向 + 纵向 timeline

**两行布局**:
- 第一行(32px 固定):Sentence | Phrase count | Expandable | State
- 第二行(纵向 timeline,**展开** / 折叠,默认折叠):`已应用 N 个扩展  [↶] [↷]  ▾ 历史`

**横向 4 字段**:
```
Sentence: I like cute dogs.   |   短语: 3   |   可扩展: 2   |   State: Analysis completed
```

**纵向 timeline**(展开后):
```
已应用 2 个扩展                                    [↶ Undo]  [↷ Redo]  [▴ 折叠]
┌────────────────────────────────────────────────────────────┐
│ ●  v3  I like cute dogs.                  形容词 cute      │
│ │   16:42:13   NP(dogs)  ←  cute                          │
│ │                                                           │
│ ●  v2  I like three dogs.                 数量词 three    │
│ │   16:41:55   NP(dogs)  ←  three                          │
│ │                                                           │
│ ●  v1  I like dogs.                      (原句)            │
│     16:41:30   —                                          │
└────────────────────────────────────────────────────────────┘
```

**timeline 交互**:
- 当前版本:实心圆 ● + 高亮背景
- 历史版本:空心圆 ○
- 鼠标 hover 显示完整 action_summary
- 点击历史版本:Undo/Redo 直接跳到该版本(不调后端,改 currentIndex)
- 上限 50 步:超出截断,头部不显示

### 4.7 Quota DFS 派生(关键逻辑)

**Quota 是前端派生,绝不调后端**。`utils/expansionQuota.ts` 新增:

```typescript
// 静态规则表(对齐 spec)
const QUOTA_RULES: Record<PhraseType, Partial<Record<ExpansionKind, number>>> = {
  NP:  { adjective: 2, number: 1, prepositional_phrase: 1, relative_clause: 1 },
  VP:  { adverb: 2, modal: 1, perfect: 1, progressive: 1 },
  ADJP: { degree_adverb: 2 },
  ADVP: { degree_adverb: 2 },
  PP:  {},  // M3a+1.3 暂不开
};

interface PhraseQuota {
  used: number;
  max: number;
  reached: boolean;  // used >= max
}

type QuotaMap = Record<string /* phrase_id */, Record<ExpansionKind, PhraseQuota>>;

/**
 * 从当前 phrases 树 DFS 数每个短语各 kind 的已用配额。
 * 数法:遍历该 phrase 的 children_ids(若有) + 该 phrase 自身 type 决定的 kind 配额。
 * 简化:M3a+1.3 不做 Benepar 嵌套,只看 children_ids 递归。
 */
function computeQuotas(phrases: PhraseNodeInfo[]): QuotaMap;
```

**DFS 算法**(M3a+1.3 简化版):
1. 遍历 `phrases` 数组
2. 对每个 phrase,初始化一个空 `Record<kind, {used:0, max:0}>` + 查 QUOTA_RULES 填 max
3. 递归:对该 phrase 的 `children_ids`,数每个 child 的 type 对应 kind 配额
4. M3a+1.3 简化:直接把每个 phrase 的 children_ids 数累加到父 phrase(例如 `NP(dogs)` 有 child `ADJ(cute)`,number+1 到 adjective kind)

**应用配额到 UI**:
- PhraseCard 顶部 chip:`2/2 adj`(从 quota 派生)
- Inspector 类别头部:`形容词 (已选 1/2)`(从 quota 派生)
- Inspector chip 禁用:配额 reached 的 kind 的所有 chip 灰显 + tooltip
- 右栏结构图子项:显示 `形容词 (1/2)`

**关键**:`computeQuotas` 必须在 `SentenceCanvas` 渲染前调,**纯函数**,输入 `phrases` 输出 `quotaMap`,**不存任何状态**。每次画布重画都重算。

### 4.8 已扩展视觉态 + 金色角标

`getPhraseVisualState(phrase, quotaMap, selectedId)` 派生:

```typescript
type VisualState = 'default' | 'expandable' | 'selected' | 'extended';

function getVisualState(phrase, quotaMap, selectedId): VisualState {
  if (!phrase.is_expandable) return 'default';
  if (phrase.id === selectedId) return 'selected';
  // 配额任一 kind used > 0 视为已扩展
  const hasAnyUsed = Object.values(quotaMap[phrase.id] ?? {}).some(q => q.used > 0);
  return hasAnyUsed ? 'extended' : 'expandable';
}
```

**金色角标** ★ 写在 `extended` 态的 PhraseCard 右上角(替换可扩展态的绿点 ●,**两者不共存**——M3a 的绿点 ● 仅在 `expandable` 态显示)。

### 4.9 文件改动(M3a+1.3)

| 文件 | 改动 |
|---|---|
| `src/renderer/components/expand/SentenceCanvas.tsx` | 取消 [+],加 visual state + Quota chip + 金角标 |
| `src/renderer/components/expand/ExtensionMenu.tsx` | **重写** 为 `ExpansionInspector.tsx`(删除 ExtensionMenu.tsx) |
| `src/renderer/components/expand/ExpandScene.tsx` | 透传 onSelectPhrase,接 Inspector 替代浮层 |
| `src/renderer/components/expand/ExpansionTree.tsx` | 子树改嵌套卡片 + 缩进,删除线条 |
| `src/renderer/components/expand/PhraseInfoPanel.tsx` | **新增**,右栏下面板 |
| `src/renderer/components/expand/StatusBar.tsx` | **新增**,底栏两行 |
| `src/renderer/components/expand/ExpansionTimeline.tsx` | **新增**,底栏纵向 timeline |
| `src/renderer/utils/expansionQuota.ts` | **新增**,`computeQuotas` DFS 派生 |
| `src/renderer/types/index.ts` | 加 `VisualState` / `PhraseQuota` / `QuotaMap` |
| `src/renderer/App.tsx` | 三栏宽度 / 底栏布局调整 |

### 4.10 验证(端到端)

1. `npm run build` 零错
2. 启动 Electron,默认句 `I usually get up at seven every morning.`,切到「句扩展」
3. 中栏画布:看到 `I usually get up at seven every morning.` 切出的若干 phrase 卡片(NP/VP/PP/ADVP),可扩展的蓝边
4. 点 `morning` 的 NP → 画布卡片绿边 + 下方 Inspector 出 `cute black big friendly ...` chips
5. 点 chip `cute` → 画布自动刷新为 `I usually get up at seven cute morning`,`morning` 卡片变 `extended` 态(蓝边 + 金角标 ★ + 顶部 chip `1/2 adj`)
6. Inspector 重新渲染该 NP 的候选,`cute` 灰显带 ✓
7. 再点 `early` → 画布变 `I usually get up at seven cute early morning`,`morning` 卡片 chip 变 `2/2 adj`
8. 第三次点 `big` → 画布卡片 仍 `2/2 adj`,Inspector 中 `big` chip 灰显 + tooltip "Maximum expansion reached"
9. 切到右栏结构图 → `NP(cute early morning)` 选中,展开子项:形容词 (2/2) / 数量词 (0/1) / 介词短语 (未开放) ...
10. 底栏 status 显示 `State: 2 extensions applied`,展开 timeline 看到 3 个版本
11. 点 timeline 第一个版本 → Undo 跳回原句
12. 点 ↷ → 跳到 v2 / v3
13. 切到 anatomy / timeline 场景,再切回 expand → history 保留(M3a+1.3 不持久化,刷新页面会丢)

### 4.11 不在 M3a+1.3 做的

- history 50 步上限 + 截断逻辑 — M3a+1.4
- 键盘快捷键(Cmd+Z / Cmd+Shift+Z)— M3a+1.4
- 已选 chip 点击撤销(右栏 / Inspector)— 留 M3b(关联 M5 Version Tree)
- 右栏结构图深层嵌套(>2 层)— M3b(装 Benepar 后)
- Validator 4 项占位实装 — M3b/c

---

## 5. M3a+1.4 收尾

> 范围:补齐 50 步上限 + 键盘快捷键 + 全链路验证 + DEVLOG/PROGRESS 文档。
> 预估:半天到一天工时,**单 commit 收尾**。

### 5.1 history 50 步上限

**`appState.ts` 的 `applyExpansion` action 内**追加截断:

```typescript
// 在 history 截断 + 追加后
let newHistory = [...expansionHistory.slice(0, expansionCurrentIndex + 1), newVersion];
let newIndex = newHistory.length - 1;

// 50 步上限:从头部截断
if (newHistory.length > 50) {
  const drop = newHistory.length - 50;
  newHistory = newHistory.slice(drop);
  newIndex -= drop;  // currentIndex 同步调整
}
```

**行为细节**:
- `newHistory[0]` 永远是**原句**,即使截断也不删原句——所以实际是"保留原句 + 最近 49 步 apply"
- 50 步触发后,顶栏 status 短暂显示 toast:`已自动清理最旧的 X 步历史`(X = drop)
- **截断只发生在 apply 时**——Undo/Redo 不触发

**测试**:
- `appState.test.ts`(新文件,Vitest + React Testing Library):
  - 测:连续 apply 51 次,`expansionHistory.length == 50`,`newIndex == 49`,`expansionHistory[0]` 还是原句

### 5.2 键盘快捷键

**全局监听**(在 `App.tsx` 顶层 `useEffect`):

| 快捷键 | 行为 | 范围 |
|---|---|---|
| `Cmd/Ctrl + Z` | Undo | 仅当 `activeScene === 'expand'` 且 `canUndo` |
| `Cmd/Ctrl + Shift + Z` | Redo | 仅当 `activeScene === 'expand'` 且 `canRedo` |
| `Cmd/Ctrl + Y` | Redo(Windows 习惯) | 同上 |

**实现位置**:`App.tsx` 顶层 `useEffect`(M3a 已有的暗色模式 useEffect 旁边):

```typescript
useEffect(() => {
  if (activeScene !== 'expand') return;
  const handler = (e: KeyboardEvent) => {
    const isMac = navigator.platform.includes('Mac');
    const cmd = isMac ? e.metaKey : e.ctrlKey;
    if (!cmd) return;
    if (e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      actions.undoExpansion();
    } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
      e.preventDefault();
      actions.redoExpansion();
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [activeScene, ...]);
```

**注**:Electron 默认不绑系统快捷键,窗口内 `window.addEventListener('keydown')` 直接生效。

### 5.3 全链路验证(出 commit 前必跑)

按顺序跑通:

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -m pytest backend/tests/test_expansion_engine.py -v` | 19/19 全过(M3a 11 + M3a+1.1 8) |
| 2 | `cd backend && python app.py`(后台跑) | spaCy 加载完成,听 `18765` |
| 3 | `curl -X POST http://127.0.0.1:18765/api/expansion/analyze -d '{"sentence":"I like dogs."}' -H 'Content-Type: application/json'` | 200 + `phrases` 3 项 |
| 4 | `curl -X POST http://127.0.0.1:18765/api/expansion/apply -d '{"sentence":"I like dogs.","phrase_id":"p2","template_id":"tpl_adj_cute"}' -H 'Content-Type: application/json'` | 200 + `sentence: "I like cute dogs."` |
| 5 | `npx tsc --noEmit` | 零错 |
| 6 | `npm run build` | electron-vite 全链路 build 成功 |
| 7 | Electron 端到端 4 步(1.1→1.4 各阶段的 verification list 都跑一遍) | 全通 |

### 5.4 文档

**`docs/DEVLOG.md`** 追加(阶段倒序):

```markdown
## 2026-06-17 M3a+1 — 句扩展写路径与视觉重塑

[按倒序记]

### 阶段切分(方案 B:垂直切分,后端优先)

- M3a+1.1 后端写路径:`/api/expansion/apply` 端点 + apply_template 拼装器 + Validator 4 级包装
- M3a+1.2 前端最小闭环:history[] + SentenceVersion 快照 + Undo/Redo
- M3a+1.3 视觉重塑:Inspector 化 + 嵌套右栏 + Quota DFS + 底栏 timeline
- M3a+1.4 收尾:50 步上限 + 键盘快捷键 + 全链路验证

### 架构铁律(用户已确认)

- 后端 100% stateless(无 session_id,响应只含 sentence/phrases/warnings/validation)
- 后端是唯一句法权威(前端永不自造 PhraseNode)
- 1 apply = 1 SentenceVersion 快照(不存 patch,不合并)
- Quota 是前端 DFS 派生(后端响应永不含 quota 字段)
- Validator 顾问非权威(/apply 永远 200,severity 4 级包装)
- 画布 phrase-level 平铺(永远不出现 token 卡片)
- M3b 接 Benepar 时只换 phrase_segmenter 函数体,不动 apply / history / UI

### 踩坑/决策

- 拼装���则按 base 句重算位置(不依赖 history[]),V1+V2+V3 累加语义自然成立
- timeline 支持跳任意版本 + 从中分支(M5 Version Tree 演化留接口)
- 50 步上限触发截断后顶栏弹 toast,原句永远保留

### 验证

- pytest 19/19 通过
- curl 4 端点全 200
- tsc --noEmit 零错
- npm run build 全链路
- Electron 端到端 4 阶段联测
```

**`docs/PROGRESS.md`** 阶段 3 整行从 "M3a 完成" 升到 "M3a + M3a+1 完成"。

### 5.5 commit 信息

**4 个 commit**(对应 4 阶段):

```
feat(M3a+1.4): history 50 步上限 + 键盘快捷键 + 全链路收尾
feat(M3a+1.3): 视觉重塑 - Inspector 化 + 嵌套右栏 + Quota DFS + 底栏 timeline
feat(M3a+1.2): 前端最小闭环 - history[] + Undo/Redo + ExtensionMenu 接 /apply
feat(M3a+1.1): 后端写路径 - /api/expansion/apply + apply_template + Validator 4 级
```

`co-authored` Claude(沿用 M3a 风格)。

### 5.6 不在 M3a+1.4 做的

- localStorage 持久化 — M4
- .glab 项目文件 — M5
- Version Tree 分支 UI — M5
- AI 集成 — M4
- L2/L3 扩展 — M3b/c
- Validator 4 项占位实装 — M3b/c

### 5.7 风险与缓解

| 风险 | 缓解 |
|---|---|
| 1.1 阶段 apply_template 拼装规则边界 case 漏掉(英文词序特殊句) | M3a+1.1 单测覆盖 8 case,主谓不一致 / 介词短语 / 数量词替换 a/an 都测 |
| 1.3 阶段 Quota DFS 漏数 modifier(嵌套 PP 套 NP 场景) | M3a+1.3 单测覆盖简单 NP/VP/ADJP 三类 + 嵌套 1 层 |
| 1.3 阶段 Inspector / 嵌套右栏 / 底栏 timeline 三者联动,任一卡死全屏 | 单组件先单独跑通(直接 Electron 单测),再串 |
| 1.4 阶段 50 步截断 bug(currentIndex 算错导致跳到非原句) | 截断逻辑单测覆盖,expansionHistory[0] 永远是原句不变 |
| 整轮 4 commit 累积 diff 大(估 +1500 行) | 每个 commit 单独可回滚;1.2 后立即可玩(用户能加 cute dogs),1.3 是体验升级 |

---

## 6. 文件清单(汇总)

### 新增(后端)
- 无新文件(`expansion_engine.py` / `expansion_validator.py` / `models.py` 追加;`test_expansion_engine.py` 追加)

### 新增(前端 M3a+1.2)
- 无新文件(ExtensionMenu.tsx / ExpandScene.tsx / appState.ts / types/index.ts 改造)

### 新增(前端 M3a+1.3)
- `src/renderer/components/expand/ExpansionInspector.tsx`(替换 M3a ExtensionMenu.tsx)
- `src/renderer/components/expand/PhraseInfoPanel.tsx`
- `src/renderer/components/expand/StatusBar.tsx`
- `src/renderer/components/expand/ExpansionTimeline.tsx`
- `src/renderer/utils/expansionQuota.ts`

### 新增(测试 M3a+1.4)
- `src/renderer/state/appState.test.ts`(Vitest + RTL)

### 修改
- `backend/grammar_engine/expansion_engine.py` — `apply_template` + `apply` 入口
- `backend/grammar_engine/expansion_validator.py` — Severity 枚举 + ValidationReport 扩展
- `backend/grammar_engine/models.py` — `ApplyRequest / ExpansionApplyResponse / ValidationReport`(BaseModel)
- `backend/app.py` — `POST /api/expansion/apply` 端点
- `backend/tests/test_expansion_engine.py` — +8 项测试
- `src/renderer/types/index.ts` — `SentenceVersion / ApplyActionSummary / ValidationReport / ValidationSeverity / VisualState / PhraseQuota / QuotaMap`
- `src/renderer/state/appState.ts` — `expansionHistory / expansionCurrentIndex` + `applyExpansion / undoExpansion / redoExpansion` actions
- `src/main/ipc/index.ts` — `apply-expansion` handler
- `src/preload/index.ts` — `applyExpansion(s, p, t)`
- `src/renderer/components/expand/SentenceCanvas.tsx` — 取消 [+],加 visual state + Quota chip + 金角标
- `src/renderer/components/expand/ExtensionMenu.tsx` — 重写为 ExpansionInspector.tsx
- `src/renderer/components/expand/ExpandScene.tsx` — 接 Inspector + 底栏 timeline
- `src/renderer/components/expand/ExpansionTree.tsx` — 子树改嵌套卡片 + 缩进,删除线条
- `src/renderer/App.tsx` — 透传 + 键盘快捷键 useEffect
- `docs/PROGRESS.md` — 阶段 3 整行更新
- `docs/DEVLOG.md` — M3a+1 阶段记录

### 已知问题(沿用 M3a,留待后续)
1. `ipc/index.ts` / `appState.ts` 多段 handler / action 复制粘贴(M3 结束后抽工具重构)
2. `ExtensionMenu.tsx` 在 M3a+1.3 被重写为 `ExpansionInspector.tsx`,**文件删除**(组件改名)
3. pytest 未列入 requirements.txt(M3a 已知问题 #3,留 M3b)
4. `He like dogs.` 类的 spaCy 误标靠 Validator + VERB_LEMMA_FALLBACK 兜底(M3a 已知问题 #2,留 M3b Benepar)

---

## 7. Spec Self-Review

> 按 SKILL.md checklist 第 7 项:placeholder / 矛盾 / 歧义 / 范围

- [x] **没有 placeholder**:所有 Pydantic 字段、Validator severity 映射、拼装规则表、Quota 规则表、commit 信息都列了具体值
- [x] **没有矛盾**:
  - §1.3 关键约束表(后端 stateless / quota 派生 / validator 顾问 / phrase-level 平铺)与 §2-§5 各章实现细节完全一致
  - §2.2 拼装规则表与 §4.7 Quota DFS 算法都基于 phrase-level 树,不依赖 token 序列
  - §3.2 history 模型与 §4.6 timeline 形态对齐(都基于 SentenceVersion 快照)
- [x] **没有歧义**:
  - "画布 phrase-level 平铺"已明确定义(§1.3、§4.2):不出现 token 级卡片,不嵌套
  - "支持跳任意版本 + 从中分支"已定义(§1.3、§3.2):Undo 跳到旧版后 apply 走 history 截断 + 追加
  - "后端 100% stateless"已定义(§1.3、§2.1):响应只含 sentence/phrases/warnings/validation,无 quota/version_id/session_id
  - "Quota 是前端 DFS 派生"已定义(§1.3、§4.7):静态规则表 + 每次重算,不存进 history[]
  - "Validator 4 级 severity"已定义(§2.3):PASS/INFO/WARNING/ERROR,/apply 永远 200
- [x] **范围清晰**:§1.4 「不做」枚举 L2/L3/persistence/AI/Version Tree,§5.6 收尾阶段再列一次
- [x] **阶段切分明确**:§1.2 4 阶段表,每阶段独立可玩/可回滚
- [x] **测试覆盖**:§2.5 后端 8 项,§5.1 前端 quota 截断测试,§3.9 + §4.10 端到端清单

---

## 8. 路线图(对齐 M3a 路线图)

| Phase | 内容 | M3a+1 关系 |
|---|---|---|
| Phase 1(读) | Word-level phrase-level 数据模型 + 规则 + 模板 + Validator 主谓一致 | **M3a 已交付** |
| **Phase 1(写)** | 提交扩展闭环 + 新增高亮 + 连线 + 动态 Expansion Tree + Depth 限制 | **M3a+1 = 本 spec** |
| Phase 2 | Phrase-level(PP / participle / infinitive phrase) | M3b:装 Benepar,`phrase_segmenter` 换实现;接 PP/participle/infinitive 扩展;Validator tense_consistency 实现;右栏升级命名 |
| Phase 3 | Clause-level(relative / adverbial / noun clause) + 关系代词匹配 | M3c:接 LanguageTool;相对/状语/名词性从句扩展;Validator 其他 3 项实现 |
| Phase 4 | Sentence restructuring(句式重构) | M4+:AI 集成 + localStorage 持久化 |
| Phase 5 | Grammar knowledge graph | M5+:.glab 项目文件 + Version Tree 分支 UI |

**接缝预留**:`phrase_segmenter.segment(doc)` 返回契约固定,M3b 装 Benepar 只换函数体;`apply` 端点 / history / UI / Quota DFS 都不受 Benepar 替换影响。
