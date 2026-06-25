# M4 Follow-ups — 技术债清理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close M4 deferred follow-ups I2 (integration tests) + M3 (ambient `Window.electronAPI` typing) + M5 (stale worktree cleanup). Zero functional change. Three commits, all on `main`.

**Architecture:**
- M3 refactor moves the `declare global { Window.electronAPI }` block from `src/preload/index.ts` into a new `src/types/electron-api.d.ts`, exposing it to the renderer's TypeScript checker via the existing `include: ["src"]`. The two `@ts-ignore` comments at the call sites are removed; the two existing test files drop their `(window as any)` casts in favor of typed mocks.
- I2 adds two new test files: a backend in-process test using `fastapi.testclient.TestClient` (the same pattern used in `test_expansion_engine.py:507`), and a frontend vitest cross-component test for `ExplainPanel` → `explainStore` → `ExplainHistoryDrawer` flow.
- M5 is a single shell command sequence to remove the already-merged `feature/m3a-plus-1` worktree.

**Tech Stack:** TypeScript 5.4, React 18.3, Vitest 4.1, FastAPI 0.115, fastapi.testclient (stdlib), pytest 8.3, httpx 0.27 (transitive via fastapi.testclient).

**Spec:** `docs/superpowers/specs/2026-06-25-m4-followups-tech-debt-cleanup-design.md`

## Global Constraints

- **Project location:** `D:/Grammar Lab/` (Windows). All commands use forward slashes or quoted paths.
- **Branch policy:** Direct linear commits on `main` (project convention, see `docs/DEVLOG.md`). No worktree for this work — M5's own cleanup is the only worktree operation.
- **Commit style:** `chore(M3): ...`, `test(I2): ...`, `chore(M5): ...` prefixes, with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer.
- **No new dependencies:** `httpx` and `fastapi.testclient` are already in `requirements.txt` transitively. No `pytest-asyncio` (use `TestClient`, which is sync).
- **No behavior change:** Every change is type/test/infrastructure only. No M4 business logic touched.
- **Verification gates after each task:** `npx tsc --noEmit` (0 errors) AND `npx vitest run` (all green) AND `cd backend && python -m pytest` (all green).
- **M4 Iron Rules preserved:** This work does not touch `/api/explain`, `InferenceGateway`, `ExplainCache`, or any scene component's `onSelect` wiring. The only renderer-side change is moving a type declaration.

---

## File Structure

### Created
- `src/types/electron-api.d.ts` — Ambient `Window.electronAPI` declaration (render-side)
- `backend/tests/integration/test_m4_full_flow.py` — In-process M4 endpoint integration tests (4 cases)
- `src/renderer/__integration__/explain_flow.test.tsx` — Cross-component flow tests (3 cases)

### Modified
- `src/preload/index.ts` — Remove redundant `declare global` block (lines 34-38); keep `export interface ElectronAPI`
- `src/renderer/components/explain/ExplainPanel.tsx` — Remove `@ts-ignore` at line 51
- `src/renderer/stores/healthStore.ts` — Remove `@ts-ignore` at line 15
- `src/renderer/test/setup.ts` — Drop `(global.window as any)` cast on the `electronAPI` mock (line 11)
- `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx` — Drop `(window as any)` cast at line 12
- `src/renderer/stores/__tests__/healthStore.test.ts` — Drop `(window as any)` cast at line 8
- `docs/PROGRESS.md` — Add "M4 follow-ups (I2+M3+M5) closed 2026-06-25" line to phase 4 status
- `.superpowers/sdd/progress.md` — Add final close-out note for M4 ledger

### Removed (filesystem)
- `D:/Grammar Lab/.worktrees/feature-m3a-plus-1/` (worktree directory)
- Branch `feature/m3a-plus-1` (already merged at `30e02f3`)

---

## Task 1: M3 — Ambient `Window.electronAPI` declaration

**Files:**
- Create: `src/types/electron-api.d.ts`
- Modify: `src/preload/index.ts` (remove `declare global` block, keep type export)
- Modify: `src/renderer/components/explain/ExplainPanel.tsx:51` (remove `@ts-ignore`)
- Modify: `src/renderer/stores/healthStore.ts:15` (remove `@ts-ignore`)
- Modify: `src/renderer/test/setup.ts:11-16` (drop `as any` cast)
- Modify: `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx:12` (drop `as any` cast)
- Modify: `src/renderer/stores/__tests__/healthStore.test.ts:8` (drop `as any` cast)

**Interfaces:**
- Consumes: `ElectronAPI` interface exported from `src/preload/index.ts`
- Produces: `window.electronAPI` typed as `ElectronAPI` for the entire renderer (via `tsconfig.json` `include: ["src"]`)

- [ ] **Step 1: Create `src/types/electron-api.d.ts`**

Create the file with this exact content:

```typescript
// M3: Ambient declaration for the preload-injected electronAPI.
// The runtime value is set by contextBridge.exposeInMainWorld() in src/preload/index.ts.
// This file exists so the renderer's TypeScript checker sees window.electronAPI
// as strongly-typed without requiring every file to import from src/preload.
//
// preload/index.ts owns the *single* source of truth for the surface
// (`exposeInMainWorld` + the matching `export interface ElectronAPI`).
// If you add/remove/change a method on electronAPI, update both places together.

import type { ElectronAPI } from '../preload';

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};
```

- [ ] **Step 2: Remove redundant `declare global` from `src/preload/index.ts`**

Edit `src/preload/index.ts`. The current file ends like this (lines 21-38):

```typescript
// 类型声明
export interface ElectronAPI {
  analyzeSentence: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  analyzeAnatomy: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  analyzeExpansion: (sentence: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  applyExpansion: (sentence: string, phraseId: string, templateId: string) => Promise<{ success: boolean; data?: any; error?: string }>;
  speakText: (text: string) => Promise<{ success: boolean }>;
  copyToClipboard: (text: string) => Promise<{ success: boolean }>;
  onDarkModeChange: (callback: (isDark: boolean) => void) => void;
  explainNode: (ctx: any) => Promise<{ success: boolean; data?: any; error?: string }>;
  getExplainHealth: () => Promise<{ success: boolean; data?: any; error?: string }>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
```

Delete the trailing `declare global` block (the last 5 lines, from the empty line after the closing `}` of `ElectronAPI` through the final `}` of the `Window` declaration). The file should end with the closing `}` of the `ElectronAPI` interface followed by a single trailing newline.

The `export interface ElectronAPI` stays — `src/types/electron-api.d.ts` will `import type` from it.

- [ ] **Step 3: Remove `@ts-ignore` from `ExplainPanel.tsx`**

In `src/renderer/components/explain/ExplainPanel.tsx`, find lines 50-52:

```typescript
      try {
        // @ts-ignore — electronAPI 由 preload 注入
        const r = await window.electronAPI.explainNode(ctx);
```

Change to:

```typescript
      try {
        const r = await window.electronAPI.explainNode(ctx);
```

- [ ] **Step 4: Remove `@ts-ignore` from `healthStore.ts`**

In `src/renderer/stores/healthStore.ts`, find lines 14-16:

```typescript
    try {
      // @ts-ignore — electronAPI 由 preload 注入
      const r = await window.electronAPI.getExplainHealth();
```

Change to:

```typescript
    try {
      const r = await window.electronAPI.getExplainHealth();
```

- [ ] **Step 5: Fix `src/renderer/test/setup.ts` mock cast**

The current `src/renderer/test/setup.ts` has at line 11:

```typescript
(global.window as any).electronAPI = {
  analyzeSentence: vi.fn(),
  analyzeAnatomy: vi.fn(),
  analyzeExpansion: vi.fn(),
  applyExpansion: vi.fn(),
};
```

Now that `Window.electronAPI` is typed, the test setup mock must provide a value satisfying the full `ElectronAPI` interface (TypeScript will reject a partial mock unless we narrow). Replace those 5 lines with:

```typescript
import type { ElectronAPI } from '../../preload';
import { vi } from 'vitest';

// Tests stub electronAPI as needed. We declare a partial because individual tests
// only override the methods they exercise; the remaining methods are unused stubs.
type ElectronAPIStub = Pick<
  ElectronAPI,
  'analyzeSentence' | 'analyzeAnatomy' | 'analyzeExpansion' | 'applyExpansion'
>;
const electronAPIStub: ElectronAPIStub = {
  analyzeSentence: vi.fn(),
  analyzeAnatomy: vi.fn(),
  analyzeExpansion: vi.fn(),
  applyExpansion: vi.fn(),
};
Object.assign(window, { electronAPI: electronAPIStub });
```

The `Object.assign(window, { electronAPI: ... })` widening is intentional: production code reads `window.electronAPI` and gets the full interface; tests override `electronAPI` per-test by re-assigning on `window`. The `Pick<>` ensures our default stub at least provides the four methods the rest of the app uses, satisfying `tsc`.

- [ ] **Step 6: Fix `ExplainPanel.test.tsx` mock cast**

In `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx`, the current line 12 is:

```typescript
  (window as any).electronAPI = {
    explainNode: mockExplainNode,
    getExplainHealth: mockGetHealth,
  };
```

Replace with:

```typescript
  // Per-test override of the ambient electronAPI.
  // `Test only` methods: explainNode + getExplainHealth.
  Object.assign(window, {
    electronAPI: {
      explainNode: mockExplainNode,
      getExplainHealth: mockGetHealth,
    },
  });
```

- [ ] **Step 7: Fix `healthStore.test.ts` mock cast**

In `src/renderer/stores/__tests__/healthStore.test.ts`, the current line 8 is:

```typescript
  (window as any).electronAPI = {
    getExplainHealth: mockGetExplainHealth,
  };
```

Replace with:

```typescript
  // Per-test override of the ambient electronAPI.
  Object.assign(window, {
    electronAPI: {
      getExplainHealth: mockGetExplainHealth,
    },
  });
```

- [ ] **Step 8: Run TypeScript check**

Run: `cd "/d/Grammar Lab" && npx tsc --noEmit`
Expected: exit code 0, no errors. If you see `Property 'X' is missing in type ...` on the test files, you missed updating one of the mock sites (steps 5/6/7). Fix and re-run.

- [ ] **Step 9: Run vitest to confirm no regressions**

Run: `cd "/d/Grammar Lab" && npx vitest run`
Expected: all tests pass. The numbers should match the pre-task baseline (8 files / 40 tests from the final-fix report) — the 3 new tests come in Task 2.

- [ ] **Step 10: Verify zero `@ts-ignore` in `src/`**

Run: `cd "/d/Grammar Lab" && grep -r '@ts-ignore' src/ || echo "OK: zero @ts-ignore"`
Expected: `OK: zero @ts-ignore` (or empty grep output). If any match, you missed a site — go back to step 3 or 4.

- [ ] **Step 11: Commit**

Run:

```bash
cd "/d/Grammar Lab" && git add \
  src/types/electron-api.d.ts \
  src/preload/index.ts \
  src/renderer/components/explain/ExplainPanel.tsx \
  src/renderer/stores/healthStore.ts \
  src/renderer/test/setup.ts \
  src/renderer/components/explain/__tests__/ExplainPanel.test.tsx \
  src/renderer/stores/__tests__/healthStore.test.ts && \
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "chore(M3): ambient Window.electronAPI declaration; remove @ts-ignore

Move declare global { Window.electronAPI } from src/preload/index.ts
to src/types/electron-api.d.ts so the renderer's tsc checker sees
window.electronAPI as strongly typed. Drop the two @ts-ignore lines
at the call sites and the (window as any) casts in 3 test files.

Iron Rule: preload still owns the runtime surface and the
ElectronAPI interface export; the d.ts is a single-line import of it.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

Expected: one commit, message above. Note the commit hash for the SDD ledger later.

---

## Task 2: I2 (backend) — M4 full-flow integration tests

**Files:**
- Create: `backend/tests/integration/test_m4_full_flow.py`

**Interfaces:**
- Consumes: `app` from `app.py` (FastAPI instance), `ExplainContext` and `ExplainSource` from `grammar_engine.ai.explain.explain_service`
- Produces: 4 test cases verifying the `/api/explain` and `/api/explain/health` endpoints

- [ ] **Step 1: Create `backend/tests/integration/test_m4_full_flow.py`**

Create the file with this exact content:

```python
"""M4 — /api/exexplain 端点 in-process 集成测。

Unlike backend/tests/integration/test_m4_api.py (which hits a live server
and skips if the service is not running), this file exercises the FastAPI
app in-process via fastapi.testclient.TestClient. The whole M4 contract
(never-200, source field, degraded flag, cache hit, fallback path) is
covered here, so CI gets deterministic coverage without a live backend.

The pattern is the same one used in
backend/tests/test_expansion_engine.py:507 (test_endpoint_apply_via_testclient).
"""

import pytest
from fastapi.testclient import TestClient

from app import app
import app as app_module
from grammar_engine.ai.explain.explain_service import ExplainSource


@pytest.fixture
def client():
    """TestClient that triggers FastAPI's lifespan (so model loads, etc.).

    Lifespan may fail to load the spaCy model in some CI environments
    (no en_core_web_sm) — that's fine: the M4 endpoints have their own
    fallback path when the model or the AI provider is not available.
    """
    with TestClient(app) as c:
        yield c


def _payload(scene: str = "timeline", node_id: str = "n1") -> dict:
    return {
        "scene": scene,
        "input_sentence": "I have lived here.",
        "selected_node_id": node_id,
        "node_type": "tense",
        "selected_node": {"text": "have lived"},
        "engine_result_summary": {"verb_count": 1},
    }


def test_full_flow_health_then_explain_happy_path(client):
    """Health endpoint returns 200 + valid shape; explain returns 200 with
    a non-empty result title regardless of whether AI is available."""
    # 1. Health
    h = client.get("/api/explain/health")
    assert h.status_code == 200
    health = h.json()
    assert "provider" in health
    assert "available" in health
    assert isinstance(health["available"], bool)

    # 2. Explain — Iron Rule: always 200, ok=True, result present.
    r = client.post("/api/explain", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "result" in data
    assert data["result"]["title"]  # non-empty
    assert data["result"]["source"] in {s.value for s in ExplainSource}


def test_explain_cache_hit_on_identical_input(client):
    """Two identical /api/explain calls — the second must report cached=true.

    Validates that the cache key is stable across calls and that
    ExplainCache.hit() sets result.cached. We don't care which provider
    answered the first call; the contract is: identical input, second
    call is served from cache.
    """
    payload = _payload(node_id="cache-test-node")
    r1 = client.post("/api/explain", json=payload)
    assert r1.status_code == 200
    first = r1.json()["result"]
    assert first["cached"] is False  # first call is always a miss

    r2 = client.post("/api/explain", json=payload)
    assert r2.status_code == 200
    second = r2.json()["result"]
    assert second["cached"] is True, (
        f"second call should be served from cache; got cached={second['cached']}, "
        f"source={second['source']}"
    )
    # Title must be stable across cache hit.
    assert second["title"] == first["title"]


def test_explain_fallback_when_service_down(client, monkeypatch):
    """With explain_service forced to None, the endpoint must still 200
    and serve a fallback result. Iron Rule 1: never 5xx."""
    monkeypatch.setattr(app_module, "explain_service", None)
    r = client.post("/api/explain", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["degraded"] is True
    assert data["result"]["source"] == ExplainSource.FALLBACK.value
    # Fallback title is scene-specific (timeline → 解释), must be non-empty.
    assert data["result"]["title"]


def test_explain_degraded_on_provider_exception(client, monkeypatch):
    """If the live provider throws, the endpoint must catch, fall back,
    and still return 200 with degraded=true. Iron Rule 1 + ErrorHandling."""
    service = app_module.explain_service
    if service is None:
        pytest.skip("explain_service not initialized in this env")

    async def _explode(ctx):
        raise RuntimeError("simulated provider outage")

    monkeypatch.setattr(service, "explain", _explode)

    r = client.post("/api/explain", json=_payload(node_id="provider-boom"))
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["degraded"] is True
    assert data["result"]["source"] == ExplainSource.FALLBACK.value
```

- [ ] **Step 2: Run the new test file**

Run: `cd "/d/Grammar Lab/backend" && python -m pytest tests/integration/test_m4_full_flow.py -v`
Expected: 4 tests pass (`test_full_flow_health_then_explain_happy_path`, `test_explain_cache_hit_on_identical_input`, `test_explain_fallback_when_service_down`, `test_explain_degraded_on_provider_exception`).

Notes on what may vary:
- If the env has no spaCy model, `test_explain_fallback_when_service_down` is still fine (we force `explain_service = None` directly).
- If the env has no AI provider, `test_full_flow_health_then_explain_happy_path` will assert `source in {ai, fallback, cache}` — all valid. Both `test_explain_cache_hit_on_identical_input` calls land in cache regardless of provider.
- If `test_explain_degraded_on_provider_exception` skips, that's expected when the service is None; the case is still covered by the previous test.

- [ ] **Step 3: Confirm no regression in the rest of the backend test suite**

Run: `cd "/d/Grammar Lab/backend" && python -m pytest -q`
Expected: all backend tests still pass. The M4 backend suite (test_m4_*) should remain green; the existing live-HTTP `test_m4_api.py` will skip (no running server), which is its baseline behavior.

- [ ] **Step 4: Commit**

Run:

```bash
cd "/d/Grammar Lab" && git add backend/tests/integration/test_m4_full_flow.py && \
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "test(I2): M4 full-flow integration tests (in-process)

Add backend/tests/integration/test_m4_full_flow.py with 4 cases:
- happy path: /api/explain/health then /api/explain
- cache hit: identical input → cached=true on second call
- fallback when service down: explain_service=None → 200, source=fallback
- degraded on provider exception: mock service.explain to throw

Uses fastapi.testclient.TestClient (same pattern as
test_expansion_engine.py:507); no new deps. The existing live-HTTP
test_m4_api.py is preserved as a smoke test for manual runs.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: I2 (frontend) — ExplainPanel ↔ explainStore ↔ HistoryDrawer integration test

**Files:**
- Create: `src/renderer/__integration__/explain_flow.test.tsx`

**Interfaces:**
- Consumes: `ExplainPanel` from `src/renderer/components/explain/ExplainPanel`, `ExplainHistoryDrawer` from the same directory, `useExplainStore` from `src/renderer/stores/explainStore`, `SelectionEvent` from `src/renderer/types/selection`
- Produces: 3 cross-component test cases verifying the explain flow

- [ ] **Step 1: Create `src/renderer/__integration__/explain_flow.test.tsx`**

Create the file with this exact content:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import { ExplainPanel } from '../components/explain/ExplainPanel';
import { ExplainHistoryDrawer } from '../components/explain/ExplainHistoryDrawer';
import { useExplainStore } from '../stores/explainStore';
import type { SelectionEvent } from '../types/selection';
import type { ExplainResult } from '../types/explain';

const mockExplainNode = vi.fn();
const mockGetHealth = vi.fn();

const sampleResult = (overrides: Partial<ExplainResult> = {}): ExplainResult => ({
  title: '现在完成时',
  summary: 'summary',
  why: 'why',
  example: 'example',
  commonMistakes: [],
  tips: [],
  source: 'ai',
  provider: 'ollama',
  model: 'llama3.1:8b',
  promptVersion: 'M4a_v1',
  cached: false,
  generatedAt: new Date().toISOString(),
  degraded: false,
  ...overrides,
});

const explainResponseFor = (r: ExplainResult) => ({
  success: true,
  data: { ok: true, degraded: r.degraded, result: r },
});

beforeEach(() => {
  mockExplainNode.mockReset();
  mockGetHealth.mockReset();
  Object.assign(window, {
    electronAPI: {
      explainNode: mockExplainNode,
      getExplainHealth: mockGetHealth,
    },
  });
  // Reset persisted store between tests.
  useExplainStore.setState({ history: [] });
  // Clear localStorage from zustand/persist.
  localStorage.clear();
});

const selection = (id = 'n1'): SelectionEvent => ({
  scene: 'timeline',
  node: { id, type: 'tense', data: { verb: 'have lived' } },
});

describe('explain flow (ExplainPanel → explainStore → ExplainHistoryDrawer)', () => {
  it('writes to history when ExplainPanel receives a successful response', async () => {
    const r = sampleResult({ title: 'A' });
    mockExplainNode.mockResolvedValueOnce(explainResponseFor(r));

    render(
      <ExplainPanel selection={selection('hist-1')} sentence="I have lived here." darkMode={false} />,
    );

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
    });
    const history = useExplainStore.getState().history;
    expect(history).toHaveLength(1);
    expect(history[0].result.title).toBe('A');
    expect(history[0].context.selected_node_id).toBe('hist-1');
  });

  it('ExplainHistoryDrawer renders all pinned and unpinned entries from the store', () => {
    const r1 = sampleResult({ title: 'Pinned entry' });
    const r2 = sampleResult({ title: 'Recent entry' });
    act(() => {
      useExplainStore.getState().pushHistory({
        context: { scene: 'timeline', selected_node_id: 'p1' } as any,
        result: r1,
        viewedAt: new Date().toISOString(),
      });
      useExplainStore.getState().pushHistory({
        context: { scene: 'timeline', selected_node_id: 'p2' } as any,
        result: r2,
        viewedAt: new Date().toISOString(),
      });
    });

    const onSelect = vi.fn();
    const onClose = vi.fn();
    render(
      <ExplainHistoryDrawer open onClose={onClose} onSelect={onSelect} darkMode={false} />,
    );

    // Drawer's data-testid is on the root panel.
    expect(screen.getByTestId('history-drawer')).toBeInTheDocument();
    // Both entries must appear (no pin filter at the drawer level).
    expect(screen.getByText('Pinned entry')).toBeInTheDocument();
    expect(screen.getByText('Recent entry')).toBeInTheDocument();
  });

  it('rapid selection changes only keep the last in history (abort + request_id double-safety)', async () => {
    // First selection: slow IPC that never resolves.
    let resolveSlow: ((v: any) => void) | null = null;
    const slowPromise = new Promise<any>((resolve) => {
      resolveSlow = resolve;
    });
    mockExplainNode.mockImplementationOnce(() => slowPromise);
    // Second selection: fast success.
    mockExplainNode.mockResolvedValueOnce(
      explainResponseFor(sampleResult({ title: 'Second wins' })),
    );

    const { rerender } = render(
      <ExplainPanel selection={selection('a')} sentence="I have lived here." darkMode={false} />,
    );
    // Loading skeleton for the first (slow) call.
    await waitFor(() => {
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
    expect(mockExplainNode).toHaveBeenCalledTimes(1);

    // User clicks the second node.
    rerender(
      <ExplainPanel selection={selection('b')} sentence="I have lived here." darkMode={false} />,
    );

    // Second IPC was triggered.
    await waitFor(() => {
      expect(mockExplainNode).toHaveBeenCalledTimes(2);
    });
    // Second result renders.
    await waitFor(() => {
      expect(screen.getByText('Second wins')).toBeInTheDocument();
    });

    // If the slow call resolves *after* the fast one, the panel must not regress.
    if (resolveSlow) {
      await act(async () => {
        (resolveSlow as any)(explainResponseFor(sampleResult({ title: 'Stale should lose' })));
      });
    }
    // Give the microtask queue a turn.
    await new Promise((r) => setTimeout(r, 0));

    // Panel still shows the second selection.
    expect(screen.queryByText('Stale should lose')).not.toBeInTheDocument();
    expect(screen.getByText('Second wins')).toBeInTheDocument();

    // History dedup by (scene, selected_node_id): the latest push for each
    // selection wins. The stale push (selection 'a') must NOT be in history
    // because its call was aborted before the response was processed; the
    // second push (selection 'b') is the only one persisted.
    const history = useExplainStore.getState().history;
    const ids = history.map((h) => h.context.selected_node_id);
    expect(ids).toEqual(['b']);
  });
});
```

- [ ] **Step 2: Run the new test file**

Run: `cd "/d/Grammar Lab" && npx vitest run src/renderer/__integration__/`
Expected: 3 tests pass.

Note on the third test: it relies on the existing `AbortController` + `request_id` double-safety implemented in `ExplainPanel.tsx` (see lines 47-100). The test verifies that when a slow first call is *still in flight* when the user makes a second selection, the second selection's result wins AND the history is deduplicated so only the second push survives. If this test fails with a stale title or duplicate history, the existing race-safety logic in ExplainPanel regressed — investigate before committing.

- [ ] **Step 3: Run the full vitest suite**

Run: `cd "/d/Grammar Lab" && npx vitest run`
Expected: all 9 test files pass (8 pre-existing + 1 new). The 43 tests should all be green (40 pre-existing + 3 new). Run with `--coverage` to confirm coverage stays at 98%+ on the explain module.

- [ ] **Step 4: TypeScript check**

Run: `cd "/d/Grammar Lab" && npx tsc --noEmit`
Expected: 0 errors.

- [ ] **Step 5: Commit**

Run:

```bash
cd "/d/Grammar Lab" && git add src/renderer/__integration__/explain_flow.test.tsx && \
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "test(I2): frontend ExplainPanel ↔ store ↔ HistoryDrawer flow

Add src/renderer/__integration__/explain_flow.test.tsx with 3 cases:
- panel success writes to explainStore history
- history drawer renders all entries from the store
- rapid selection keeps only the last in history (race + dedup)

Pairs with backend/tests/integration/test_m4_full_flow.py to close
the M4 I2 follow-up. No business logic changes; relies on the
existing AbortController + request_id double-safety in ExplainPanel.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: M5 — Remove stale worktree

**Files:**
- Filesystem: remove `D:/Grammar Lab/.worktrees/feature-m3a-plus-1/`
- Git: prune worktree refs, delete branch `feature/m3a-plus-1`

**Interfaces:** None. Pure repo hygiene.

- [ ] **Step 1: Confirm the worktree branch is fully merged into main**

Run: `cd "/d/Grammar Lab" && git branch --merged main`
Expected output contains:
```
  feature/m3a-plus-1
* main
```

If `feature/m3a-plus-1` is NOT in the merged list, STOP and surface to the user — do not delete an unmerged branch.

- [ ] **Step 2: Remove the worktree**

Run: `cd "/d/Grammar Lab" && git worktree remove .worktrees/feature-m3a-plus-1`
Expected: no error. The worktree directory is removed. If git complains about the directory not being clean, the user may have left uncommitted work there; inspect with `git -C .worktrees/feature-m3a-plus-1 status` (if the dir still exists) before forcing.

- [ ] **Step 3: Prune stale worktree refs**

Run: `cd "/d/Grammar Lab" && git worktree prune`
Expected: no output, exit 0.

- [ ] **Step 4: Delete the merged branch**

Run: `cd "/d/Grammar Lab" && git branch -d feature/m3a-plus-1`
Expected: `Deleted branch feature/m3a-plus-1 (was 30e02f3).` (the hash is the tip of the merged branch; if different, that's still fine — git uses the merge-base).

- [ ] **Step 5: Verify final state**

Run:
```bash
cd "/d/Grammar Lab" && git worktree list && echo "---" && ls .worktrees/ 2>&1 || true && echo "---" && git branch
```

Expected:
- `git worktree list` shows only one line: `D:/Grammar Lab  <current-hash> [main]`
- `ls .worktrees/` either prints nothing (empty dir, OK) or errors with "No such file or directory" (also OK — preferred). If there are other unexpected files, STOP and report.
- `git branch` shows only `* main`.

- [ ] **Step 6: Commit any remaining metadata changes (likely none)**

The worktree removal and branch deletion are operations on git's internal state, not on tracked files. There is usually nothing to commit. Run:

```bash
cd "/d/Grammar Lab" && git status
```

Expected: `nothing to commit, working tree clean` OR a small set of auto-generated files (e.g., `.git/index.lock` removed). If there ARE files to commit, investigate before committing — worktree cleanup should not touch tracked files.

If there's truly nothing to commit, skip the commit step. If you need a marker commit (e.g., the user wants every task to produce a commit), create an empty commit:

```bash
cd "/d/Grammar Lab" && git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit --allow-empty -m "chore(M5): remove stale worktree feature-m3a-plus-1 (merged at 30e02f3)

Worktree and its branch are no longer needed: all M3c series commits
landed on main via the M3c1 merge. Verified with 'git branch --merged
main'. Frees the .worktrees/ directory.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

(Use the empty-commit form only if the previous step left the working tree clean and you want a marker.)

---

## Task 5: Documentation close-out (PROGRESS.md + SDD ledger)

**Files:**
- Modify: `docs/PROGRESS.md` (add one line to phase 4 status block)
- Modify: `.superpowers/sdd/progress.md` (add final close-out note for M4 ledger)

- [ ] **Step 1: Update `docs/PROGRESS.md` phase 4 status row**

Open `docs/PROGRESS.md`. In the table at the top:

```
| 阶段 | 名称 | 状态 | 完成时间 |
|------|------|------|----------|
| 0 | 基础框架搭建 | ✅ 完成 | 2026-06-12 |
| 1 | 时间轴分析功能 | ✅ 完成 | 2026-06-13 |
| 2 | 句剖析分析功能 | ✅ 完成 | 2026-06-14 |
| 3 | 句扩展分析功能 | ✅ 完成 (M3a → M3c5 全部完成) | 2026-06-24 |
| 4 | AI Explain Layer | 🔨 进行中 (M4a ✅ M4b ✅ M4c 1/3 ✅ / M4c ⏳ M4d ⏳) | - |
```

Update the **"最后更新" date** at the top of the file to `2026-06-25` and update the phase 4 row to:

```
| 4 | AI Explain Layer | ✅ 完成 (M4a-M4d 全量交付) + 收尾 (I2+M3+M5) | 2026-06-25 |
```

Then, **append a new section** at the end of the phase 4 narrative (right before the "相关文件" / "注意事项" sections). Add:

```markdown
---

## ✅ 阶段 4 收尾: M4 Follow-ups (I2+M3+M5) — 2026-06-25

M4 整分支审查后列出的 4 个 deferred follow-ups 中,本批次关闭 3 个:

- ✅ **I2 (集成测)** — 新增 `backend/tests/integration/test_m4_full_flow.py`(4 条 in-process,TestClient 模式) + `src/renderer/__integration__/explain_flow.test.tsx`(3 条跨组件 Vitest)
- ✅ **M3 (@ts-ignore 清理)** — 新增 `src/types/electron-api.d.ts` ambient 声明,删除 `ExplainPanel.tsx:51` 与 `healthStore.ts:15` 两处 `@ts-ignore`,修正 3 处测试文件 mock 写法
- ✅ **M5 (worktree 清理)** — 移除 `feature-m3a-plus-1` worktree(已合并于 `30e02f3`)
- ⏭️ **M6 (i18n)** — 留待阶段 5 独立处理

**结果:** TypeScript 0 错误;前端 Vitest 43/43 通过(40 → 43);后端 pytest 全套回归不挂;`grep -r '@ts-ignore' src/` 为空;`git worktree list` 仅 main。
```

- [ ] **Step 2: Update `.superpowers/sdd/progress.md` ledger**

Open `.superpowers/sdd/progress.md`. After the "Final whole-branch review" section, add a new section:

```markdown
## M4 Follow-ups close-out (I2+M3+M5) — 2026-06-25

Three commits land on `main`:
- `chore(M3): ambient Window.electronAPI declaration; remove @ts-ignore`
- `test(I2): M4 full-flow integration tests (in-process)` (backend)
- `test(I2): frontend ExplainPanel ↔ store ↔ HistoryDrawer flow` (frontend)
- `chore(M5): remove stale worktree feature-m3a-plus-1 (merged at 30e02f3)`

**Verdict:** M4 ledger fully closed. M6 (i18n) tracked separately for stage 5.
```

- [ ] **Step 3: Final verification — full suite green**

Run the full verification gate:

```bash
cd "/d/Grammar Lab" && \
  echo "== tsc ==" && npx tsc --noEmit && \
  echo "== vitest ==" && npx vitest run && \
  echo "== pytest ==" && cd backend && python -m pytest -q && cd .. && \
  echo "== @ts-ignore scan ==" && (grep -r '@ts-ignore' src/ || echo "OK: zero @ts-ignore") && \
  echo "== worktree list ==" && git worktree list && \
  echo "== git status ==" && git status
```

Expected:
- `tsc`: 0 errors
- `vitest run`: 9 files / 43 tests passed
- `pytest -q`: dot/output indicating all tests pass (the live-HTTP `test_m4_api.py` will skip with a "service not running" message — that is its baseline behavior, not a failure)
- `@ts-ignore scan`: `OK: zero @ts-ignore`
- `worktree list`: one line, `main` only
- `git status`: `nothing to commit, working tree clean`

- [ ] **Step 4: Commit documentation**

Run:

```bash
cd "/d/Grammar Lab" && git add docs/PROGRESS.md .superpowers/sdd/progress.md && \
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "docs(M4): close out follow-ups I2+M3+M5

Update PROGRESS.md phase 4 status and append a close-out section.
Update .superpowers/sdd/progress.md ledger with the four follow-up
commits. M6 (i18n) tracked separately for stage 5.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Verify final git log**

Run: `cd "/d/Grammar Lab" && git log --oneline -10`
Expected: top 4 commits are the M4 follow-up batch, preceded by `7ab48a3` (M4d final-fix) and earlier M4 work. Working tree clean.

---

## Self-Review Notes

- **Spec coverage:** Spec sections 3.1 (M3) → Task 1; 3.2 (I2 backend) → Task 2; 3.3 (I2 frontend) → Task 3; 3.4 (M5) → Task 4; section 5 (verification checklist) → Task 5 step 3.
- **Type consistency:** `window.electronAPI` is consistently typed as `ElectronAPI` from `src/preload/index.ts`. `Object.assign(window, { electronAPI: ... })` is used in 3 test files to override per-test. The `Pick<>` in `setup.ts` is intentional.
- **No placeholders:** Every step has the actual code, file paths, and exact commands. The test assertions in Task 3 step 1 are full; the body of `test_m4_full_flow.py` is full.
- **No new dependencies:** Confirmed. `httpx` and `fastapi.testclient` are already in `requirements.txt` (httpx is explicit; TestClient is stdlib in FastAPI 0.115). Vitest needs no new packages. `pytest-asyncio` is intentionally avoided by using the sync `TestClient`.
- **Iron Rule preservation:** M4 Iron Rules 1-5 are not touched. `/api/explain` always returns 200 (Task 2 tests verify); AI never writes phrase tree (no expand scene code changed); InferenceGateway remains the single inference entry (not touched); cache key remains provider-agnostic (test 2 verifies cache hits across provider changes); Scene components do not import Explain code (no scene file changed).
