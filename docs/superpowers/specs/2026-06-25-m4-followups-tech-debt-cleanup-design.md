# M4 Follow-ups — 技术债清理 设计

**Date:** 2026-06-25
**Status:** Draft
**Scope:** Refactor / 收尾 (无功能变更)
**Estimated effort:** 半天以内

---

## 1. 背景

M4 (AI Explain Layer) 已全量交付,commit `7ab48a3`,98% 覆盖率,整分支审查通过。

最终 ledger 列出 4 个 deferred follow-ups:

| ID | 项目 | 状态 |
|---|---|---|
| I2 | M4 后端补全集成测(端到端 happy path + cache hit + fallback) | 现有 `test_m4_api.py` 仅打 live HTTP,无 in-process 全路径 |
| M3 | 消除 2 处 `@ts-ignore`(M4c review 遗留) | 散落在 `ExplainPanel.tsx:51` / `healthStore.ts:15` |
| M5 | 清理陈旧 worktree `.worktrees/feature-m3a-plus-1` | 分支 `feature/m3a-plus-1` 已合并入 main(commit `30e02f3` 即 10 次前),留着无意义 |
| M6 | i18n | 跳过(本批次仅做技术债,产品向改动另起 spec) |

**本 spec 仅覆盖 I2 + M3 + M5。** M6 后续独立处理。

---

## 2. 目标 / 非目标

### 目标

- **类型安全:** 消除全部 `@ts-ignore`,让 `window.electronAPI` 在渲染端有正式类型声明,TypeScript 编译期就能发现 preload API 不匹配。
- **测试网加固:** 增加 in-process 集成测,覆盖 `/api/explain` happy path + cache hit + fallback path,以及前端 ExplainPanel + explainStore + HistoryDrawer 联动。
- **仓库卫生:** 移除已合并的 worktree,worktree 列表只剩 main。

### 非目标

- 不改任何 M4 业务逻辑、UI、文案。
- 不引入新依赖。
- 不改 `preload/index.ts` 运行时行为(`contextBridge.exposeInMainWorld` 仍照原样挂载)。
- 不动 i18n / 多语言。
- 不动现有 live HTTP 集成测 `test_m4_api.py`(保持作为 smoke test,继续 `_wait_for_service` skip 语义)。

---

## 3. 设计

### 3.1 M3 — Ambient `Window.electronAPI` 声明(类型安全)

**问题:** `src/renderer/components/explain/ExplainPanel.tsx:51` 和 `src/renderer/stores/healthStore.ts:15` 各有 `// @ts-ignore — electronAPI 由 preload 注入`,绕过类型检查。

**根本原因:** TypeScript 编译时不知道 `Window` 上有 `electronAPI`。`src/preload/index.ts:34-38` 虽然有 `declare global { interface Window { electronAPI: ElectronAPI } }`,但这文件是 Electron 入口(Vite 在主进程构建产物里跑,渲染端 `import` 它只是为了取 `ElectronAPI` *类型*);render 端实际并不 `import` preload —— 所以 `global` 声明未被传递到 render 端 type-check。

**方案:** 把 `declare global` 从 `src/preload/index.ts` 抽出,放到 `src/types/electron-api.d.ts`,作为纯声明文件(`include: ["src"]` 覆盖到)。preload 自身继续导出 `ElectronAPI` *interface*(`type-only`),d.ts `import type` 引用。

**改动文件:**

| 文件 | 动作 |
|---|---|
| `src/types/electron-api.d.ts` | **新** — `import type { ElectronAPI } from '../preload'`,`declare global { interface Window { electronAPI: ElectronAPI } }`,`export {}` |
| `src/preload/index.ts` | 移除 line 34-38 的 `declare global`(重复声明 TS 报 "Subsequent property declarations must have the same type" 错误) |
| `src/preload/index.ts` | 保留 `export interface ElectronAPI` (type-only, render 端 `import type` 引用) |
| `src/renderer/components/explain/ExplainPanel.tsx:51` | 删 `// @ts-ignore`,直接 `const r = await window.electronAPI.explainNode(ctx)` |
| `src/renderer/stores/healthStore.ts:15` | 删 `// @ts-ignore`,直接 `const r = await window.electronAPI.getExplainHealth()` |
| `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx:12` | `(window as any).electronAPI` → `window.electronAPI = { ... } as Partial<typeof window.electronAPI>` (或保留 `as any`,因为 mock 故意不全) |
| `src/renderer/stores/__tests__/healthStore.test.ts` | 同上 |
| `vitest.config.ts` | (无改动) — happy-dom 环境,`window` 全局已可用,`src/types/electron-api.d.ts` 自动 include |

**验收:**
- `npx tsc --noEmit` 0 errors,且 0 `@ts-ignore` (可用 `grep -r '@ts-ignore' src/` 验证为空)
- 现有 `ExplainPanel.test.tsx` / `healthStore.test.ts` 全部通过
- `npm test -- --run` 全绿

### 3.2 I2 — In-process 全流程集成测

**问题:** 现有 `backend/tests/integration/test_m4_api.py` 是 live HTTP smoke test(需后端运行,否则 skip)。缺一个 in-process、CI 友好的全路径覆盖。

**方案:** 新增 `backend/tests/integration/test_m4_full_flow.py`,用 `httpx.AsyncClient` + `ASGITransport` 启 FastAPI app,**不**真实启 uvicorn。所有依赖(nlp、provider、cache)走真实模块,但 provider 强制 `null` 即可控。

**测试用例(4 条):**

1. `test_full_flow_health_then_explain_happy_path` — 先 `/api/explain/health` 探活,根据 `available` 决定后续断言;再 `/api/explain` 一次 → 200,`ok=true`,`result.source ∈ {ai, fallback}`,`result.title` 非空
2. `test_explain_cache_hit` — 同输入连续两次请求,第二次必须 `cached=true`(强制走 cache,验证缓存逻辑)
3. `test_explain_fallback_when_service_down` — monkey-patch `explain_service = None`,请求必须仍 200,`degraded=true`,`result.source='fallback'`,`result.title` 命中 `fallback_explanations` 的对应 entry
4. `test_explain_degraded_on_provider_exception` — mock provider `explain()` 抛 `RuntimeError`,端点必须 200 + degraded + fallback

**改动文件:**

| 文件 | 动作 |
|---|---|
| `backend/tests/integration/test_m4_full_flow.py` | **新** — 4 条 in-process 集成测 |
| `backend/tests/conftest.py` | 可选新增 fixture:`event_loop`(pytest-asyncio)+ `app` fixture(返回 FastAPI 实例) |
| `backend/requirements.txt` | 需 `httpx`(可能已在,验) + `pytest-asyncio` |

**验收:**
- `python -m pytest backend/tests/integration/test_m4_full_flow.py -v` 4/4 通过
- **不需要** backend 服务运行
- 不破坏现有 `test_m4_api.py`(独立文件,独立 live-HTTP 路径,继续保留 skip 语义)

### 3.3 前端集成测 — ExplainPanel + explainStore + HistoryDrawer 联动

**问题:** 现有 `ExplainPanel.test.tsx` 只测单组件。`explainStore` 与 `HistoryDrawer` 之间、`pushHistory` → 持久化 → 渲染,缺端到端覆盖。

**方案:** 新增 `src/renderer/__integration__/explain_flow.test.tsx`(新建 `__integration__/` 目录,与 `vitest.config.ts` 的 `coverage.exclude` 互不干扰 —— 因为 `**/*.test.{ts,tsx}` 已被 exclude)。

**测试用例(3 条):**

1. `test_panel_success_writes_to_history` — 渲染 `ExplainPanel` + 喂成功响应 → `useExplainStore.getState().history` 长度 +1
2. `test_history_drawer_renders_pinned_entries` — 先 push 2 条 history(其中 1 条 pin) → 渲染 `ExplainHistoryDrawer` → 断言 2 条都出现
3. `test_rapid_selection_only_last_wins` — 复用 M4d 已有 race 测试语义,但升级为跨 store:`explainStore` 不得保存被 abort 的中间结果,只保留最后一条

**改动文件:**

| 文件 | 动作 |
|---|---|
| `src/renderer/__integration__/explain_flow.test.tsx` | **新** — 3 条跨组件测,mock `window.electronAPI` |

**验收:**
- `npx vitest run src/renderer/__integration__/` 3/3 通过
- 不影响现有单组件测

### 3.4 M5 — 清理陈旧 worktree

**操作:**

```bash
cd "/d/Grammar Lab"
git worktree remove .worktrees/feature-m3a-plus-1
git worktree prune
git branch -d feature/m3a-plus-1   # 已 merged,安全
```

**验收:**
- `git worktree list` 仅一行:`D:/Grammar Lab  7ab48a3 [main]`
- `.worktrees/` 目录不存在(或为空)
- 仍能 `git log main` 看到 `30e02f3` 起的所有 M3c 系列 commit(都在 main 上,worktree 删除不影响历史)

---

## 4. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 移动 `declare global` 后,preload ��身无法识别 `window.electronAPI` | preload 是 Node 侧 Electron 入口,不需要 `Window` 类型;仅 render 端需要。preload 端保留 `ElectronAPI` interface 的 type export 即可 |
| d.ts 中 `import type` 在 bundler resolution 下找不到 `../preload` | tsconfig `moduleResolution: "bundler"` + `allowImportingTsExtensions: true` 已就位;preload 路径 `src/preload/index.ts` 可解析 |
| `__integration__/` 目录被 coverage 收进 | vitest.config.ts 已有 `**/*.test.{ts,tsx}` exclude,新文件满足 |
| 集成测在 CI 跑时拿不到真实 provider | 强制 `null` provider 或 mock `InferenceGateway`;test 不依赖外部 |
| 删 worktree 后本地 `.worktrees/` 残留目录 | `git worktree remove` + `git worktree prune`;如仍残留,`rm -rf` 即可 |

---

## 5. 验收清单(本 spec 闭环判定)

- [ ] `npx tsc --noEmit` 0 errors
- [ ] `grep -r '@ts-ignore' src/` 0 hits
- [ ] `grep -r 'declare global' src/preload/` 0 hits(已迁出)
- [ ] `npx vitest run` 全部通过(包含 3 条新集成测)
- [ ] `cd backend && python -m pytest tests/integration/test_m4_full_flow.py -v` 4/4 通过
- [ ] `cd backend && python -m pytest` 全套回归不挂
- [ ] `git worktree list` 仅 main
- [ ] `.worktrees/` 不存在
- [ ] 提交为 3 个独立 commit(每个 task 一个,清晰可回滚):
  - `chore(M3): ambient Window.electronAPI declaration; remove @ts-ignore`
  - `test(I2): M4 full-flow integration tests (backend + frontend)`
  - `chore(M5): remove stale worktree feature-m3a-plus-1`
- [ ] PROGRESS.md 阶段 4 补一行 "M4 follow-ups (I2+M3+M5) closed 2026-06-25"
- [ ] `.superpowers/sdd/progress.md` ledger 加最终闭环说明

---

## 6. 不在本 spec 范围(明确)

- M6 i18n —— 留到阶段 5 独立处理
- M2 review finding: explainStore selector 稳定性 —— 不在本次技术债范围
- M3 review finding: warn rule 复用 —— 同上
- 工作分支管理:本工作在 `main` 直接线性提交(沿用 M3c1 起的约定)
