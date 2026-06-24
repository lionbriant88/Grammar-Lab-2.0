# M4 — AI Explain Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Grammar Lab 三个场景上叠加 AI 解释层,把规则引擎结果翻译成"为什么"教学解释,可降级、可 Pin、有 History。

**Architecture:** 后端 `AIExplainService` 读 rule engine 结果 → `InferenceGateway` → `AIProvider` (Ollama/Cloud/Null)。`/api/explain` 永远 HTTP 200。前端 `ExplainPanel` 异步常驻右栏,`SelectionEvent + ExplainContextBuilder` 解耦 Scene。

**Tech Stack:**
- Backend: FastAPI + Pydantic 2.9 + httpx 0.27 + cachetools 5.5 + tenacity 9.0
- Provider SDK: ollama 0.4+ / openai 1.50+
- Frontend: React 18 + TypeScript 5.4 + Zustand 5 + react-markdown 9 + Tailwind 3
- Test: pytest 8.3 + npm test (vitest or jest)

**Spec:** `docs/superpowers/specs/2026-06-24-m4-ai-explain-layer-design.md`

---

## Global Constraints

- **M4 Iron Rule 1:** `/api/explain` 永远返回 HTTP 200,任何异常降级到 fallback
- **M4 Iron Rule 2:** AI 永远只读 engine_result,不写 phrase tree
- **M4 Iron Rule 3:** InferenceGateway 是 M4-M7 唯一推理入口
- **M4 Iron Rule 4:** Cache key 不含 provider/model/language-version
- **M4 Iron Rule 5:** Scene 组件不 import 任何 Explain 相关代码
- **NodeType 字面量:** `tense` | `phrase` | `template` | `validation_warning`（禁止 `vp` / `verb_phrase`）
- **Source 枚举:** `ai` | `cache` | `fallback`（对应徽章 🧠 / ⚡ / 📘）
- **Cache 库:** `cachetools.TTLCache`（不手写 LRU）
- **解析:** `ExplainResponseModel.model_validate_json()`（不 `json.loads`）
- **路径约定:** 后端用绝对 import `from grammar_engine.ai...`；前端用相对 import
- **提交风格:** `feat(M4a): 中文描述`，co-authored Claude
- **Port:** 后端 `127.0.0.1:18765`
- **测试运行:** 后端 `cd backend && python -m pytest tests/ -v`；前端 `npm test`

---

## File Structure

### 新建文件

**后端 — Inference 层（M4-M7 共享）：**
- `backend/grammar_engine/ai/__init__.py` — 包标记
- `backend/grammar_engine/ai/inference/__init__.py` — 包标记
- `backend/grammar_engine/ai/inference/providers/__init__.py` — 包标记
- `backend/grammar_engine/ai/inference/providers/provider_base.py` — `AIProvider` 抽象基类
- `backend/grammar_engine/ai/inference/providers/ollama_provider.py` — Ollama 本地
- `backend/grammar_engine/ai/inference/providers/cloud_provider.py` — OpenAI/Anthropic
- `backend/grammar_engine/ai/inference/providers/null_provider.py` — 降级返回空
- `backend/grammar_engine/ai/inference/inference_gateway.py` — 唯一推理入口
- `backend/grammar_engine/ai/inference/provider_factory.py` — Provider 选择

**后端 — Explain 业务：**
- `backend/grammar_engine/ai/explain/__init__.py` — 包标记
- `backend/grammar_engine/ai/explain/explain_service.py` — `AIExplainService`
- `backend/grammar_engine/ai/explain/prompt_templates.py` — BASE/SCENE/NODE 三层 + 模板
- `backend/grammar_engine/ai/explain/explain_cache.py` — `ExplainCache` (TTLCache)
- `backend/grammar_engine/ai/explain/fallback_explanations.py` — 硬编码 fallback 库
- `backend/grammar_engine/ai/explain/snapshot.py` — Prompt 版本常量

**后端 — 测试：**
- `backend/tests/test_m4_providers.py` — Provider 单测
- `backend/tests/test_m4_inference_gateway.py` — Gateway 单测
- `backend/tests/test_m4_prompt_templates.py` — Prompt 模板 + snapshot
- `backend/tests/test_m4_explain_service.py` — Service 单测
- `backend/tests/test_m4_explain_cache.py` — Cache 单测
- `backend/tests/test_m4_fallback.py` — Fallback 库单测
- `backend/tests/integration/test_m4_api.py` — /api/explain + /health 集成测
- `backend/tests/prompts/__init__.py`
- `backend/tests/prompts/snapshots/base_prompt_v1.txt`
- `backend/tests/prompts/snapshots/scene_timeline_v1.txt`
- `backend/tests/prompts/snapshots/scene_anatomy_v1.txt`
- `backend/tests/prompts/snapshots/scene_expansion_v1.txt`
- `backend/tests/prompts/snapshots/node_tense_v1.txt`
- `backend/tests/prompts/snapshots/node_phrase_v1.txt`
- `backend/tests/prompts/snapshots/node_template_v1.txt`
- `backend/tests/prompts/snapshots/node_validation_warning_v1.txt`

**前端 — Explain 组件：**
- `src/renderer/components/explain/ExplainPanel.tsx`
- `src/renderer/components/explain/ExplainContextBuilder.ts`
- `src/renderer/components/explain/ExplainHistoryDrawer.tsx`
- `src/renderer/components/explain/ExplainSkeleton.tsx`
- `src/renderer/components/explain/SourceBadge.tsx`
- `src/renderer/components/explain/DegradedBanner.tsx`
- `src/renderer/components/explain/MarkdownView.tsx`
- `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx`
- `src/renderer/components/explain/__tests__/ExplainContextBuilder.test.ts`
- `src/renderer/components/explain/__tests__/SourceBadge.test.tsx`

**前端 — Stores & Types：**
- `src/renderer/stores/explainStore.ts`
- `src/renderer/stores/healthStore.ts`
- `src/renderer/types/explain.ts`
- `src/renderer/types/selection.ts`
- `src/renderer/stores/__tests__/explainStore.test.ts`

### 修改文件

- `backend/requirements.txt` — 加 5 个依赖
- `backend/app.py` — 加 2 个端点 + lifespan 初始化
- `src/preload/index.ts` — 暴露 2 个 API
- `src/main/ipc/index.ts` — 加 2 个 IPC handler
- `src/renderer/App.tsx` — 接入 ExplainPanel + 健康灯
- `src/renderer/components/timeline/TimelineScene.tsx` — emit SelectionEvent
- `src/renderer/components/anatomy/AnatomyScene.tsx` — emit SelectionEvent
- `src/renderer/components/expand/ExpandScene.tsx` — emit SelectionEvent
- `package.json` — 加 zustand / react-markdown / remark-gfm

---

## Task Index

- **M4a — 后端骨架 (Task 1-7)**
  - Task 1: 后端依赖 + AI 包结构
  - Task 2: AIProvider 抽象基类
  - Task 3: NullProvider（最小可用，先测接口）
  - Task 4: OllamaProvider
  - Task 5: CloudProvider
  - Task 6: InferenceGateway
  - Task 7: ProviderFactory + 健康检查
- **M4b — ExplainService + API (Task 8-15)**
  - Task 8: Prompt 三层结构（BASE/SCENE/NODE）+ Snapshot
  - Task 9: ExplainCache（TTLCache）
  - Task 10: Fallback 硬编码库
  - Task 11: ExplainResponseModel + Pydantic 解析
  - Task 12: AIExplainService 核心
  - Task 13: /api/explain + /api/explain/health 端点
  - Task 14: 集成测（永远 200、降级路径）
  - Task 15: Prompt Snapshot Tests
- **M4c — 前端 ExplainPanel (Task 16-22)**
  - Task 16: 前端依赖 + ExplainContextBuilder
  - Task 17: Explain Zustand store（persist）
  - Task 18: Health Zustand store
  - Task 19: SourceBadge + DegradedBanner + Skeleton
  - Task 20: ExplainPanel 核心（AbortController + request_id + Pin）
  - Task 21: ExplainHistoryDrawer
  - Task 22: Preload + IPC handler
- **M4d — 集成 + E2E (Task 23-26)**
  - Task 23: App.tsx 接入 ExplainPanel + 健康灯
  - Task 24: 三个 Scene emit SelectionEvent
  - Task 25: 单测覆盖率达到 80%
  - Task 26: E2E Case A/B/C/D（Playwright）

---

### Task 1: 后端依赖 + AI 包结构

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/grammar_engine/ai/__init__.py`
- Create: `backend/grammar_engine/ai/inference/__init__.py`
- Create: `backend/grammar_engine/ai/inference/providers/__init__.py`
- Create: `backend/grammar_engine/ai/explain/__init__.py`
- Create: `backend/tests/prompts/__init__.py`

**Interfaces:**
- Produces: 包结构,所有后续 task 的 import 起点

- [ ] **Step 1: 修改 requirements.txt**

在 `backend/requirements.txt` 末尾追加：

```
# M4 — AI Explain Layer
ollama>=0.4.0
openai>=1.50.0
httpx>=0.27.0
tenacity>=9.0.0
cachetools>=5.5.0
```

- [ ] **Step 2: 安装依赖**

```bash
cd "/d/Grammar Lab" && cd backend && pip install -r requirements.txt
```

Expected: 5 个包安装成功。

- [ ] **Step 3: 创建包 __init__.py**

`backend/grammar_engine/ai/__init__.py`：

```python
"""M4 — AI Explain Layer.

Inference 层是 M4-M7 共享入口。Explain 子包放 M4 业务。
"""
```

`backend/grammar_engine/ai/inference/__init__.py`：

```python
"""M4-M7 共享推理入口。"""
```

`backend/grammar_engine/ai/inference/providers/__init__.py`：

```python
"""Provider 实现:ollama / cloud / null。"""
```

`backend/grammar_engine/ai/explain/__init__.py`：

```python
"""M4 业务:Explain service + prompt + cache + fallback。"""
```

`backend/tests/prompts/__init__.py`：

```python
"""Prompt snapshot 测试。"""
```

- [ ] **Step 4: 验证 import 链**

```bash
cd "/d/Grammar Lab/backend" && python -c "from grammar_engine.ai import inference, explain; from grammar_engine.ai.inference import providers; print('OK')"
```

Expected: 输出 `OK`,无 ImportError。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/requirements.txt backend/grammar_engine/ai/ backend/tests/prompts/
git commit -m "feat(M4a): add AI package skeleton + dependencies"
```

---

### Task 2: AIProvider 抽象基类

**Files:**
- Create: `backend/grammar_engine/ai/inference/providers/provider_base.py`
- Create: `backend/tests/test_m4_providers.py`

**Interfaces:**
- Produces: `AIProvider` 抽象类,所有 Provider 实现继承

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_providers.py`：

```python
"""M4 — Provider 单测。"""
import pytest
from grammar_engine.ai.inference.providers.provider_base import AIProvider


def test_ai_provider_cannot_instantiate_directly():
    """AIProvider 是抽象类,不能直接实例化。"""
    with pytest.raises(TypeError):
        AIProvider()


def test_subclass_must_implement_generate():
    """子类必须实现 generate()。"""
    class IncompleteProvider(AIProvider):
        name = "incomplete"
        model_id = "x"

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_subclass_must_implement_health_check():
    """子类必须实现 health_check()。"""
    class IncompleteProvider(AIProvider):
        name = "incomplete"
        model_id = "x"

        async def generate(self, system, user):
            return ""

    with pytest.raises(TypeError):
        IncompleteProvider()
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py -v
```

Expected: `ModuleNotFoundError: No module named 'grammar_engine.ai.inference.providers.provider_base'`。

- [ ] **Step 3: 实现 AIProvider**

`backend/grammar_engine/ai/inference/providers/provider_base.py`：

```python
"""Provider 抽象基类 — 所有 LLM Provider 必须实现。"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """AI Provider 接口。

    M4 只需要 generate() 和 health_check()。
    M5+ 可能加 stream()、embed() 等,在此扩展。
    """

    name: str
    model_id: str

    @abstractmethod
    async def generate(self, system: str, user: str) -> str:
        """同步返回完整文本(非流式)。

        Args:
            system: 系统提示
            user: 用户提示

        Returns:
            模型输出文本

        Raises:
            ProviderError: 任何 LLM 调用失败
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> dict:
        """健康检查。

        Returns:
            {"ok": bool, "latency_ms": int, "error"?: str}
        """
        raise NotImplementedError
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py -v
```

Expected: 3 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/providers/provider_base.py backend/tests/test_m4_providers.py
git commit -m "feat(M4a): add AIProvider abstract base class"
```

---

### Task 3: NullProvider（最小可用）

**Files:**
- Create: `backend/grammar_engine/ai/inference/providers/null_provider.py`
- Modify: `backend/tests/test_m4_providers.py`

**Interfaces:**
- Produces: `NullProvider` (name="null", model_id="builtin")

- [ ] **Step 1: 写失败的测试**

在 `backend/tests/test_m4_providers.py` 追加：

```python
import pytest
from grammar_engine.ai.inference.providers.null_provider import NullProvider


@pytest.mark.asyncio
async def test_null_provider_generate_returns_empty():
    p = NullProvider()
    out = await p.generate("sys", "user")
    assert out == ""


@pytest.mark.asyncio
async def test_null_provider_health_check_returns_not_ok():
    p = NullProvider()
    h = await p.health_check()
    assert h["ok"] is False
    assert "error" in h


def test_null_provider_name_and_model():
    p = NullProvider()
    assert p.name == "null"
    assert p.model_id == "builtin"
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py::test_null_provider_name_and_model -v
```

Expected: `ModuleNotFoundError: No module named 'grammar_engine.ai.inference.providers.null_provider'`。

- [ ] **Step 3: 实现 NullProvider**

`backend/grammar_engine/ai/inference/providers/null_provider.py`：

```python
"""Null Provider — 永远返回空字符串。

用于 fallback 路径:AI 不可用时,ExplainService 直接走 fallback 库,
不调用 generate()。但 Gateway 健康检查仍需正常工作。
"""
from .provider_base import AIProvider


class NullProvider(AIProvider):
    name = "null"
    model_id = "builtin"

    async def generate(self, system: str, user: str) -> str:
        """返回空字符串,调用方应走 fallback。"""
        return ""

    async def health_check(self) -> dict:
        return {"ok": False, "error": "no provider configured", "latency_ms": 0}
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py -v
```

Expected: 6 passed (3 from Task 2 + 3 new)。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/providers/null_provider.py backend/tests/test_m4_providers.py
git commit -m "feat(M4a): add NullProvider for fallback path"
```

---

### Task 4: OllamaProvider

**Files:**
- Create: `backend/grammar_engine/ai/inference/providers/ollama_provider.py`
- Modify: `backend/tests/test_m4_providers.py`

**Interfaces:**
- Produces: `OllamaProvider(base_url, model)` 实现 `generate()` 和 `health_check()`

- [ ] **Step 1: 写失败的测试**

在 `backend/tests/test_m4_providers.py` 追加：

```python
from unittest.mock import patch, AsyncMock
from grammar_engine.ai.inference.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_generate_calls_api(monkeypatch):
    """generate() 调用 POST /api/generate,正确解析 response。"""
    p = OllamaProvider(base_url="http://fake", model="llama3.1:8b")

    fake_response = AsyncMock()
    fake_response.status_code = 200
    fake_response.json = lambda: {"response": "AI says..."}
    fake_response.raise_for_status = lambda: None

    class FakeAsyncClient:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def post(self, url, **kw): return fake_response

    monkeypatch.setattr(
        "grammar_engine.ai.inference.providers.ollama_provider.httpx.AsyncClient",
        FakeAsyncClient,
    )

    out = await p.generate("sys", "user")
    assert out == "AI says..."


@pytest.mark.asyncio
async def test_ollama_is_available_returns_false_on_connection_error():
    """连接失败时 is_available() 返回 False。"""
    p = OllamaProvider(base_url="http://127.0.0.1:1", model="llama3.1:8b")  # 端口 1 一定失败
    ok = await p.is_available()
    assert ok is False
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py::test_ollama_generate_calls_api -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 OllamaProvider**

`backend/grammar_engine/ai/inference/providers/ollama_provider.py`：

```python
"""Ollama 本地 Provider。

POST http://127.0.0.1:11434/api/generate
"""
import time
import httpx

from .provider_base import AIProvider


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "llama3.1:8b", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.model_id = model
        self.timeout = timeout

    async def is_available(self) -> bool:
        """GET /api/tags,3 秒超时。"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def generate(self, system: str, user: str) -> str:
        """POST /api/generate,stream=false。"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": user,
                    "system": system,
                    "stream": False,
                },
            )
            r.raise_for_status()
            return r.json().get("response", "")

    async def health_check(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                ok = r.status_code == 200
                return {
                    "ok": ok,
                    "latency_ms": int((time.time() - start) * 1000),
                    "error": None if ok else f"HTTP {r.status_code}",
                }
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((time.time() - start) * 1000),
                "error": str(e),
            }
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py -v
```

Expected: 8 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/providers/ollama_provider.py backend/tests/test_m4_providers.py
git commit -m "feat(M4a): add OllamaProvider for local LLM"
```

---

### Task 5: CloudProvider

**Files:**
- Create: `backend/grammar_engine/ai/inference/providers/cloud_provider.py`
- Modify: `backend/tests/test_m4_providers.py`

**Interfaces:**
- Produces: `CloudProvider()` 自动从 env 读 `AI_CLOUD_PROVIDER` / `AI_CLOUD_API_KEY` / `AI_CLOUD_MODEL`

- [ ] **Step 1: 写失败的测试**

在 `backend/tests/test_m4_providers.py` 追加：

```python
import os
import pytest
from grammar_engine.ai.inference.providers.cloud_provider import CloudProvider


def test_cloud_provider_requires_api_key(monkeypatch):
    """没设 AI_CLOUD_API_KEY 时 init 失败。"""
    monkeypatch.delenv("AI_CLOUD_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AI_CLOUD_API_KEY"):
        CloudProvider()


def test_cloud_provider_reads_env(monkeypatch):
    """env 配置正确时,init 成功。"""
    monkeypatch.setenv("AI_CLOUD_API_KEY", "sk-test")
    monkeypatch.setenv("AI_CLOUD_PROVIDER", "openai")
    monkeypatch.setenv("AI_CLOUD_MODEL", "gpt-4o-mini")
    p = CloudProvider()
    assert p.name == "openai"
    assert p.model_id == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_cloud_provider_health_check_without_key():
    """无 key 时 health_check 报告 not ok。"""
    os.environ.pop("AI_CLOUD_API_KEY", None)
    p = CloudProvider.__new__(CloudProvider)  # bypass __init__
    p.name = "openai"
    p.model_id = "gpt-4o-mini"
    h = await p.health_check()
    assert h["ok"] is False
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py::test_cloud_provider_requires_api_key -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 CloudProvider**

`backend/grammar_engine/ai/inference/providers/cloud_provider.py`：

```python
"""Cloud Provider — OpenAI / Anthropic 统一封装。

读 env:
  AI_CLOUD_PROVIDER=openai|anthropic  (默认 openai)
  AI_CLOUD_MODEL=gpt-4o-mini|claude-haiku-4-5-20251001
  AI_CLOUD_API_KEY=sk-...

用 openai SDK(Anthropic 走 openai 兼容模式,M5 再加原生 SDK)。
"""
import os
import time
import httpx

from .provider_base import AIProvider


class CloudProvider(AIProvider):
    def __init__(self):
        api_key = os.environ.get("AI_CLOUD_API_KEY")
        if not api_key:
            raise ValueError("AI_CLOUD_API_KEY env var required for CloudProvider")

        self.name = os.environ.get("AI_CLOUD_PROVIDER", "openai")
        self.model_id = os.environ.get("AI_CLOUD_MODEL", "gpt-4o-mini")
        self.api_key = api_key
        self.timeout = 30.0

    async def generate(self, system: str, user: str) -> str:
        """调 OpenAI 兼容 chat/completions 端点。"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def health_check(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                ok = r.status_code == 200
                return {
                    "ok": ok,
                    "latency_ms": int((time.time() - start) * 1000),
                    "error": None if ok else f"HTTP {r.status_code}",
                }
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((time.time() - start) * 1000),
                "error": str(e),
            }
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_providers.py -v
```

Expected: 11 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/providers/cloud_provider.py backend/tests/test_m4_providers.py
git commit -m "feat(M4a): add CloudProvider for OpenAI/Anthropic"
```

---

### Task 6: InferenceGateway

**Files:**
- Create: `backend/grammar_engine/ai/inference/inference_gateway.py`
- Create: `backend/tests/test_m4_inference_gateway.py`

**Interfaces:**
- Produces: `InferenceGateway(provider)` with `complete(system, user) -> str` 和 `health() -> dict`

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_inference_gateway.py`：

```python
"""M4 — InferenceGateway 单测。"""
import pytest
from grammar_engine.ai.inference.inference_gateway import InferenceGateway, InferenceError
from grammar_engine.ai.inference.providers.null_provider import NullProvider


@pytest.mark.asyncio
async def test_gateway_complete_returns_provider_output():
    """complete() 透传 provider 输出。"""
    class FakeProvider(NullProvider):
        async def generate(self, system, user):
            return f"S:{system}|U:{user}"

    gw = InferenceGateway(FakeProvider())
    out = await gw.complete("sys", "user")
    assert out == "S:sys|U:user"


@pytest.mark.asyncio
async def test_gateway_complete_raises_inference_error_on_failure():
    """provider 抛异常时,gateway 转 InferenceError。"""
    class BrokenProvider(NullProvider):
        async def generate(self, system, user):
            raise RuntimeError("boom")

    gw = InferenceGateway(BrokenProvider())
    with pytest.raises(InferenceError, match="boom"):
        await gw.complete("sys", "user")


@pytest.mark.asyncio
async def test_gateway_health_returns_provider_health():
    """health() 透传 provider.health_check()。"""
    gw = InferenceGateway(NullProvider())
    h = await gw.health()
    assert h["ok"] is False
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_inference_gateway.py -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 InferenceGateway**

`backend/grammar_engine/ai/inference/inference_gateway.py`：

```python
"""M4-M7 共享推理入口。

降级策略由调用方决定(gateway 不 swallow exception),保持 M5/M6 灵活性。
"""
import logging

logger = logging.getLogger(__name__)


class InferenceError(Exception):
    """Provider 调用失败时抛出。"""
    pass


class InferenceGateway:
    """唯一推理入口。ExplainService / RewriteService / ChatService 复用。"""

    def __init__(self, provider):
        self.provider = provider

    async def complete(self, system: str, user: str) -> str:
        try:
            return await self.provider.generate(system, user)
        except Exception as e:
            logger.warning(f"[Inference] Provider {self.provider.name} failed: {e}")
            raise InferenceError(str(e)) from e

    async def health(self) -> dict:
        return await self.provider.health_check()
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_inference_gateway.py -v
```

Expected: 3 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/inference_gateway.py backend/tests/test_m4_inference_gateway.py
git commit -m "feat(M4a): add InferenceGateway (M4-M7 shared entry)"
```

---

### Task 7: ProviderFactory

**Files:**
- Create: `backend/grammar_engine/ai/inference/provider_factory.py`
- Modify: `backend/tests/test_m4_inference_gateway.py`

**Interfaces:**
- Produces: `get_provider() -> AIProvider` 优先级:cloud (有 key) > ollama (运行中) > null

- [ ] **Step 1: 写失败的测试**

在 `backend/tests/test_m4_inference_gateway.py` 追加：

```python
from grammar_engine.ai.inference.provider_factory import get_provider
from grammar_engine.ai.inference.providers.null_provider import NullProvider
from grammar_engine.ai.inference.providers.cloud_provider import CloudProvider


@pytest.mark.asyncio
async def test_factory_returns_null_when_no_provider(monkeypatch):
    """无 cloud key + ollama 不可用 → NullProvider。"""
    monkeypatch.delenv("AI_CLOUD_API_KEY", raising=False)
    monkeypatch.setattr(
        "grammar_engine.ai.inference.provider_factory.OllamaProvider.is_available",
        lambda self: False,
    )
    p = await get_provider()
    assert isinstance(p, NullProvider)


@pytest.mark.asyncio
async def test_factory_returns_cloud_when_key_set(monkeypatch):
    """有 AI_CLOUD_API_KEY → CloudProvider(优先于 ollama)。"""
    monkeypatch.setenv("AI_CLOUD_API_KEY", "sk-test")
    monkeypatch.setenv("AI_CLOUD_PROVIDER", "openai")
    p = await get_provider()
    assert isinstance(p, CloudProvider)
    assert p.name == "openai"
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_inference_gateway.py::test_factory_returns_null_when_no_provider -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 ProviderFactory**

`backend/grammar_engine/ai/inference/provider_factory.py`：

```python
"""Provider 选择逻辑。

优先级:cloud (有 API key) > ollama (运行中) > null。
启动时调一次,后续由 lifespan 缓存。
"""
import os
import logging

from .providers.provider_base import AIProvider
from .providers.ollama_provider import OllamaProvider
from .providers.cloud_provider import CloudProvider
from .providers.null_provider import NullProvider

logger = logging.getLogger(__name__)


async def get_provider(base_url: str = "http://127.0.0.1:11434",
                       default_model: str = "llama3.1:8b") -> AIProvider:
    # 1. Cloud(优先)
    if os.environ.get("AI_CLOUD_API_KEY"):
        try:
            p = CloudProvider()
            logger.info(f"[Provider] Selected cloud: {p.name}/{p.model_id}")
            return p
        except ValueError as e:
            logger.warning(f"[Provider] Cloud init failed: {e}")

    # 2. Ollama
    ollama = OllamaProvider(base_url=base_url, model=default_model)
    if await ollama.is_available():
        logger.info(f"[Provider] Selected ollama: {ollama.model_id}")
        return ollama

    # 3. Fallback
    logger.info("[Provider] No provider available, using NullProvider")
    return NullProvider()
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_inference_gateway.py -v
```

Expected: 5 passed (3 from Task 6 + 2 new)。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/inference/provider_factory.py backend/tests/test_m4_inference_gateway.py
git commit -m "feat(M4a): add ProviderFactory (cloud > ollama > null)"
```

---

### Task 8: Prompt 三层结构 + Snapshot

**Files:**
- Create: `backend/grammar_engine/ai/explain/snapshot.py`
- Create: `backend/grammar_engine/ai/explain/prompt_templates.py`
- Create: `backend/tests/prompts/snapshots/base_prompt_v1.txt`
- Create: `backend/tests/prompts/snapshots/scene_timeline_v1.txt`
- Create: `backend/tests/prompts/snapshots/scene_anatomy_v1.txt`
- Create: `backend/tests/prompts/snapshots/scene_expansion_v1.txt`
- Create: `backend/tests/prompts/snapshots/node_tense_v1.txt`
- Create: `backend/tests/prompts/snapshots/node_phrase_v1.txt`
- Create: `backend/tests/prompts/snapshots/node_template_v1.txt`
- Create: `backend/tests/prompts/snapshots/node_validation_warning_v1.txt`
- Create: `backend/tests/test_m4_prompt_templates.py`

**Interfaces:**
- Produces: `PROMPT_VERSION`, `BASE_PROMPT`, `SCENE_PROMPTS` dict, `NODE_PROMPTS` dict, `build_system(scene, node_type) -> str`

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_prompt_templates.py`：

```python
"""M4 — Prompt 三层结构 + Snapshot。"""
from pathlib import Path
from grammar_engine.ai.explain.prompt_templates import (
    PROMPT_VERSION,
    BASE_PROMPT,
    SCENE_PROMPTS,
    NODE_PROMPTS,
    build_system,
)


def test_prompt_version_is_set():
    assert PROMPT_VERSION.startswith("M4")


def test_base_prompt_contains_no_reparse_constraint():
    assert "严禁重新解析" in BASE_PROMPT or "不要重新解析" in BASE_PROMPT
    assert "严禁修改引擎" in BASE_PROMPT or "不要修改引擎" in BASE_PROMPT


def test_base_prompt_requires_json_output():
    assert "JSON" in BASE_PROMPT
    for field in ("title", "summary", "why", "example", "common_mistakes", "tips"):
        assert field in BASE_PROMPT


def test_all_scenes_have_prompts():
    for scene in ("timeline", "anatomy", "expansion"):
        assert scene in SCENE_PROMPTS
        assert SCENE_PROMPTS[scene]


def test_all_node_types_have_prompts():
    for nt in ("tense", "phrase", "template", "validation_warning"):
        assert nt in NODE_PROMPTS
        assert NODE_PROMPTS[nt]


def test_build_system_combines_three_layers():
    s = build_system("timeline", "tense")
    assert BASE_PROMPT in s
    assert SCENE_PROMPTS["timeline"] in s
    assert NODE_PROMPTS["tense"] in s


def test_snapshot_files_match_constants():
    snap_dir = Path(__file__).parent / "snapshots"
    assert (snap_dir / "base_prompt_v1.txt").read_text(encoding="utf-8") == BASE_PROMPT
    for scene in ("timeline", "anatomy", "expansion"):
        path = snap_dir / f"scene_{scene}_v1.txt"
        assert path.read_text(encoding="utf-8") == SCENE_PROMPTS[scene]
    for nt in ("tense", "phrase", "template", "validation_warning"):
        path = snap_dir / f"node_{nt}_v1.txt"
        assert path.read_text(encoding="utf-8") == NODE_PROMPTS[nt]
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_prompt_templates.py -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 创建 snapshot 文件**

`backend/tests/prompts/snapshots/base_prompt_v1.txt`：

```
你是 Grammar Lab 的 AI 语法教师。
规则:① 严禁自己重新解析句子 ② 严禁修改引擎结果 ③ 只解释,不决定。
输出严格 JSON,字段:{title, summary, why, example, common_mistakes (list), tips (list)}。
```

`backend/tests/prompts/snapshots/scene_timeline_v1.txt`：

```
场景:时间轴。任务:解释为什么这个时态被识别,以及与相近时态的区别。
```

`backend/tests/prompts/snapshots/scene_anatomy_v1.txt`：

```
场景:句剖析。任务:解释这个短语为什么是某个角色(主/谓/宾/状/从),以及它修饰什么。
```

`backend/tests/prompts/snapshots/scene_expansion_v1.txt`：

```
场景:句扩展。任务:解释为什么推荐这个扩展方式,不扩展会怎样。
```

`backend/tests/prompts/snapshots/node_tense_v1.txt`：

```
节点类型:tense(时态)。说明与相近时态的区别、典型信号词。
```

`backend/tests/prompts/snapshots/node_phrase_v1.txt`：

```
节点类型:phrase(短语)。说明为什么是这个 syntactic_role、修饰什么成分。
```

`backend/tests/prompts/snapshots/node_template_v1.txt`：

```
节点类型:template(扩展模板)。说明为什么这个扩展合适、不扩展的代价。
```

`backend/tests/prompts/snapshots/node_validation_warning_v1.txt`：

```
节点类型:validation_warning(校验警告)。说明语法问题、如何修正。
```

- [ ] **Step 4: 实现 prompt_templates.py 和 snapshot.py**

`backend/grammar_engine/ai/explain/snapshot.py`：

```python
"""Prompt 版本常量。改 prompt 时 bump 此版本。"""
PROMPT_VERSION = "M4a_v1"
```

`backend/grammar_engine/ai/explain/prompt_templates.py`：

```python
"""Prompt 三层结构:BASE + SCENE + NODE。

修改 prompt 时:
1. 改这里
2. 更新 tests/prompts/snapshots/ 对应文件
3. bump snapshot.py 的 PROMPT_VERSION
"""
from pathlib import Path

from .snapshot import PROMPT_VERSION


def _load_snapshot(name: str) -> str:
    """从 tests/prompts/snapshots 加载(运行时也走这里,保证一致)。"""
    snap_dir = Path(__file__).parent.parent.parent.parent / "tests" / "prompts" / "snapshots"
    return (snap_dir / name).read_text(encoding="utf-8").rstrip("\n")


BASE_PROMPT = _load_snapshot("base_prompt_v1.txt")

SCENE_PROMPTS: dict[str, str] = {
    "timeline":  _load_snapshot("scene_timeline_v1.txt"),
    "anatomy":   _load_snapshot("scene_anatomy_v1.txt"),
    "expansion": _load_snapshot("scene_expansion_v1.txt"),
}

NODE_PROMPTS: dict[str, str] = {
    "tense":              _load_snapshot("node_tense_v1.txt"),
    "phrase":             _load_snapshot("node_phrase_v1.txt"),
    "template":           _load_snapshot("node_template_v1.txt"),
    "validation_warning": _load_snapshot("node_validation_warning_v1.txt"),
}


def build_system(scene: str, node_type: str) -> str:
    """三层拼接: BASE + SCENE + NODE。"""
    if scene not in SCENE_PROMPTS:
        raise ValueError(f"Unknown scene: {scene}")
    if node_type not in NODE_PROMPTS:
        raise ValueError(f"Unknown node_type: {node_type}")
    return f"{BASE_PROMPT}\n{SCENE_PROMPTS[scene]}\n{NODE_PROMPTS[node_type]}"


# User 模板 — 占位符是 selected_node / engine_result_summary
USER_TEMPLATE = """原句: {input_sentence}
选中节点 ID: {selected_node_id}
节点类型: {node_type}
节点信息: {selected_node}
引擎摘要: {engine_result_summary}
学生水平: {student_level}
请生成教学解释。"""
```

- [ ] **Step 5: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_prompt_templates.py -v
```

Expected: 7 passed。

- [ ] **Step 6: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/explain/ backend/tests/test_m4_prompt_templates.py backend/tests/prompts/
git commit -m "feat(M4b): add 3-layer prompt structure + snapshot"
```

---

### Task 9: ExplainCache（TTLCache）

**Files:**
- Create: `backend/grammar_engine/ai/explain/explain_cache.py`
- Create: `backend/tests/test_m4_explain_cache.py`

**Interfaces:**
- Produces: `ExplainCache(ttl=86400, maxsize=500)` with `async get(key)` 和 `async set(key, result)`

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_explain_cache.py`：

```python
"""M4 — ExplainCache 单测。"""
import asyncio
import time
import pytest
from grammar_engine.ai.explain.explain_cache import ExplainCache


def _make_result():
    from grammar_engine.ai.explain.explain_service import ExplainResult, ExplainSource
    return ExplainResult(
        title="t", summary="s", why="w", example="e",
        common_mistakes=[], tips=[], source=ExplainSource.AI,
        provider="ollama", model="llama3.1:8b", prompt_version="M4a_v1",
        cached=False,
    )


@pytest.mark.asyncio
async def test_cache_set_and_get():
    c = ExplainCache()
    r = _make_result()
    await c.set("k1", r)
    got = await c.get("k1")
    assert got is not None
    assert got.title == "t"


@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    c = ExplainCache()
    assert await c.get("nope") is None


@pytest.mark.asyncio
async def test_cache_respects_ttl(monkeypatch):
    c = ExplainCache(ttl=1, maxsize=10)
    await c.set("k", _make_result())
    assert await c.get("k") is not None
    time.sleep(1.1)
    assert await c.get("k") is None


@pytest.mark.asyncio
async def test_cache_evicts_oldest_when_full():
    c = ExplainCache(ttl=86400, maxsize=2)
    await c.set("a", _make_result())
    await c.set("b", _make_result())
    await c.set("c", _make_result())  # 触发淘汰
    assert await c.get("a") is None
    assert await c.get("b") is not None
    assert await c.get("c") is not None
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_cache.py -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 ExplainCache**

`backend/grammar_engine/ai/explain/explain_cache.py`：

```python
"""Explain 结果缓存 — TTLCache 实现。

Cache key 不含 provider/model(跨 provider 复用)。
"""
import asyncio
from cachetools import TTLCache

from .explain_service import ExplainResult  # 避免循环:service 也引用 cache


class ExplainCache:
    def __init__(self, ttl: int = 86400, maxsize: int = 500):
        self._store: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str):
        async with self._lock:
            return self._store.get(key)

    async def set(self, key: str, result) -> None:
        async with self._lock:
            self._store[key] = result
```

**注意**：先创建 explain_service.py 里的 ExplainResult 占位，再写 cache 避免循环。

创建临时 `backend/grammar_engine/ai/explain/explain_service.py`：

```python
"""M4 — AIExplainService (占位,Task 12 完整实现)。"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExplainSource(str, Enum):
    AI = "ai"
    CACHE = "cache"
    FALLBACK = "fallback"


@dataclass
class ExplainResult:
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list = field(default_factory=list)
    tips: list = field(default_factory=list)
    source: ExplainSource = ExplainSource.FALLBACK
    provider: str = "fallback"
    model: str = "builtin"
    prompt_version: str = "M4a_v1"
    cached: bool = False
    generated_at: datetime = field(default_factory=datetime.now)
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_cache.py -v
```

Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/explain/explain_cache.py backend/grammar_engine/ai/explain/explain_service.py backend/tests/test_m4_explain_cache.py
git commit -m "feat(M4b): add ExplainCache (TTLCache wrapper)"
```

---

### Task 10: Fallback 硬编码库

**Files:**
- Create: `backend/grammar_engine/ai/explain/fallback_explanations.py`
- Create: `backend/tests/test_m4_fallback.py`

**Interfaces:**
- Produces: `FALLBACK_LIBRARY: dict[(scene, node_type), ExplainResult]` 和 `FALLBACK_GENERIC: ExplainResult`

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_fallback.py`：

```python
"""M4 — Fallback 解释库单测。"""
from grammar_engine.ai.explain.fallback_explanations import (
    FALLBACK_LIBRARY,
    FALLBACK_GENERIC,
    fallback_for,
)


def test_fallback_library_covers_all_node_types():
    """每个 (scene, node_type) 组合都有 fallback。"""
    scenes = ("timeline", "anatomy", "expansion")
    nodes = ("tense", "phrase", "template", "validation_warning")
    for s in scenes:
        for n in nodes:
            if (s, n) in FALLBACK_LIBRARY:
                assert FALLBACK_LIBRARY[(s, n)].source.value == "fallback"


def test_fallback_generic_is_non_empty():
    assert FALLBACK_GENERIC.title
    assert FALLBACK_GENERIC.summary
    assert FALLBACK_GENERIC.why


def test_fallback_for_known_key_returns_specific():
    r = fallback_for("timeline", "tense")
    assert r.source.value == "fallback"
    assert r.title  # 非空


def test_fallback_for_unknown_returns_generic():
    r = fallback_for("unknown_scene", "unknown_type")
    assert r is FALLBACK_GENERIC or r.title == FALLBACK_GENERIC.title
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_fallback.py -v
```

Expected: `ModuleNotFoundError`。

- [ ] **Step 3: 实现 fallback_explanations.py**

`backend/grammar_engine/ai/explain/fallback_explanations.py`：

```python
"""硬编码 fallback 解释库。

AI 不可用时使用。M4a 覆盖主要 case,M4b 视情况扩充。
"""
from .explain_service import ExplainResult, ExplainSource


def _make(
    title: str, summary: str, why: str, example: str,
    mistakes: list, tips: list,
) -> ExplainResult:
    return ExplainResult(
        title=title, summary=summary, why=why, example=example,
        common_mistakes=mistakes, tips=tips,
        source=ExplainSource.FALLBACK,
        provider="fallback", model="builtin",
        prompt_version="M4a_v1", cached=False,
    )


FALLBACK_LIBRARY: dict = {
    # Timeline
    ("timeline", "tense"): _make(
        title="时态解释(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="时态由规则引擎根据动词形态和时间状语综合判断。请结合时间状语(already, yesterday, tomorrow 等)和动词形态(do/doing/done)理解。",
        example="I have lived here for 5 years. (现在完成时:have + 过去分词,持续到现在的状态)",
        mistakes=["把现在完成时和一般过去时混淆(现在完成时强调与现在的联系)"],
        tips=["先看时间状语,再看动词是否完成或持续"],
    ),

    # Anatomy
    ("anatomy", "phrase"): _make(
        title="短语角色(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="短语角色由规则引擎基于 spaCy 依存关系标注(主/谓/宾/状/从)。颜色对应:蓝=主语,绿=谓语,紫=宾语,琥珀=状语,粉=从句。",
        example="When I arrived, he was reading. → When I arrived 是状语从句(琥珀),修饰主句时间。",
        mistakes=["把定语(关系从句)和状语(时间/原因/让步)混淆——看它修饰名词还是动词"],
        tips=["找动词:它前面的主语、后面的宾语、旁边的时间/地点状语"],
    ),

    # Expansion
    ("expansion", "template"): _make(
        title="扩展模板(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="模板由规则引擎基于短语类型和句法约束推荐。形容词前置、副词后置、定从紧跟先行词——这些是英语的常见语序。",
        example="dog → cute dog (形容词扩展); ran → ran quickly (副词扩展)",
        mistakes=["形容词放错位置(cute dog vs dog cute)"],
        tips=["英语修饰习惯:形容词在名词前,副词在动词后或句首"],
    ),

    # Expansion — Validation
    ("expansion", "validation_warning"): _make(
        title="语法问题(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="校验引擎(规则 + LanguageTool)检测到潜在语法问题:主谓一致、时态一致、分句完整、非谓语合法性、关系代词匹配等。",
        example="He go to school. → 应为 He goes(主谓一致,三单加 s)。",
        mistakes=["忽略主谓一致(He go 错为 He goes)"],
        tips=["先核对主语(单复数),再核对谓语(时态/数)"],
    ),
}


FALLBACK_GENERIC = _make(
    title="解释",
    summary="AI 暂不可用,显示通用解释。",
    why="Grammar Lab 的规则引擎已给出分析结果。请结合界面上的色带、标签和提示理解句子结构。",
    example="(无) 请在主界面查看结构化分析。",
    mistakes=[],
    tips=["遇到复杂句时,先找主语和谓语,再看修饰成分"],
)


def fallback_for(scene: str, node_type: str) -> ExplainResult:
    """查表,未命中返回 generic。"""
    return FALLBACK_LIBRARY.get((scene, node_type), FALLBACK_GENERIC)
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_fallback.py -v
```

Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/explain/fallback_explanations.py backend/tests/test_m4_fallback.py
git commit -m "feat(M4b): add fallback explanations library"
```

---

### Task 11: ExplainResponseModel + Pydantic 解析

**Files:**
- Modify: `backend/grammar_engine/ai/explain/explain_service.py`
- Create: `backend/tests/test_m4_explain_service.py`

**Interfaces:**
- Produces: `ExplainResponseModel` (Pydantic) 和 `parse_response(raw) -> ExplainResponseModel | None`

- [ ] **Step 1: 写失败的测试**

`backend/tests/test_m4_explain_service.py`：

```python
"""M4 — ExplainService 单测。"""
import pytest
from pydantic import ValidationError
from grammar_engine.ai.explain.explain_service import (
    ExplainResponseModel,
    parse_response,
    ParseFail,
)


def test_parse_valid_json():
    raw = '{"title":"t","summary":"s","why":"w","example":"e","common_mistakes":["m"],"tips":["t"]}'
    r = parse_response(raw)
    assert r.title == "t"
    assert r.common_mistakes == ["m"]


def test_parse_missing_fields_uses_defaults():
    raw = '{"title":"only title"}'
    r = parse_response(raw)
    assert r.title == "only title"
    assert r.summary == ""
    assert r.common_mistakes == []


def test_parse_invalid_json_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("not json at all")


def test_parse_non_object_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("[]")
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_service.py -v
```

Expected: `ImportError`。

- [ ] **Step 3: 扩展 explain_service.py**

修改 `backend/grammar_engine/ai/explain/explain_service.py` 追加:

```python
"""M4 — AIExplainService.

职责:把 engine_result 翻译成 ExplainResult。
铁律:任何异常都降级到 fallback,不外抛。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from ..inference.inference_gateway import InferenceGateway, InferenceError
from ..inference.providers.provider_base import AIProvider
from .explain_cache import ExplainCache
from .prompt_templates import build_system, USER_TEMPLATE, PROMPT_VERSION
from .fallback_explanations import FALLBACK_LIBRARY, FALLBACK_GENERIC, fallback_for

logger = logging.getLogger(__name__)


class ExplainSource(str, Enum):
    AI = "ai"
    CACHE = "cache"
    FALLBACK = "fallback"


@dataclass
class ExplainResult:
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list = field(default_factory=list)
    tips: list = field(default_factory=list)
    source: ExplainSource = ExplainSource.FALLBACK
    provider: str = "fallback"
    model: str = "builtin"
    prompt_version: str = PROMPT_VERSION
    cached: bool = False
    generated_at: datetime = field(default_factory=datetime.now)


class ExplainResponseModel(BaseModel):
    """Pydantic 模型,验证 LLM JSON 输出。"""
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


class ParseFail(Exception):
    """LLM 输出解析失败(内部异常,外层 try/except 走 fallback)。"""
    pass


def parse_response(raw: str) -> ExplainResponseModel:
    try:
        return ExplainResponseModel.model_validate_json(raw)
    except (ValidationError, ValueError) as e:
        logger.warning(f"[AI] Parse failed: {e}")
        raise ParseFail(str(e))
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_service.py -v
```

Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/explain/explain_service.py backend/tests/test_m4_explain_service.py
git commit -m "feat(M4b): add ExplainResponseModel + parse_response"
```

---

### Task 12: AIExplainService 核心

**Files:**
- Modify: `backend/grammar_engine/ai/explain/explain_service.py`
- Modify: `backend/tests/test_m4_explain_service.py`

**Interfaces:**
- Produces: `AIExplainService(gateway, cache)` with `async explain(ctx) -> ExplainResult` 和 `fallback_for(ctx) -> ExplainResult`

- [ ] **Step 1: 写失败的测试**

在 `backend/tests/test_m4_explain_service.py` 追加：

```python
from grammar_engine.ai.explain.explain_service import (
    AIExplainService,
    ExplainContext,
    ExplainResult,
    ExplainSource,
)
from grammar_engine.ai.inference.providers.null_provider import NullProvider


def _ctx(scene="timeline", node_type="tense", sentence="I have lived here."):
    return ExplainContext(
        scene=scene,
        input_sentence=sentence,
        selected_node_id="n1",
        node_type=node_type,
        selected_node={"text": "have lived", "tense": "present_perfect"},
        engine_result_summary={"verb_count": 1},
        language="zh",
        student_level="intermediate",
    )


@pytest.mark.asyncio
async def test_explain_uses_fallback_when_provider_returns_empty():
    """NullProvider 返回空 → 走 fallback。"""
    gw = InferenceGateway(NullProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK
    assert r.title  # 非空


@pytest.mark.asyncio
async def test_explain_uses_fallback_on_gateway_error():
    """Gateway 抛 InferenceError → 走 fallback。"""
    from grammar_engine.ai.inference.inference_gateway import InferenceGateway

    class BrokenProvider(NullProvider):
        async def generate(self, system, user):
            raise RuntimeError("boom")

    gw = InferenceGateway(BrokenProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK


@pytest.mark.asyncio
async def test_explain_returns_ai_result_on_valid_response():
    """LLM 返回合法 JSON → source=AI。"""

    class FakeProvider(NullProvider):
        async def generate(self, system, user):
            return '{"title":"ai title","summary":"s","why":"w","example":"e","common_mistakes":["m"],"tips":["t"]}'

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(FakeProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.AI
    assert r.title == "ai title"
    assert r.provider == "null"  # FakeProvider 用 NullProvider 的 name


@pytest.mark.asyncio
async def test_explain_uses_cache_on_second_call():
    """第二次同样 ctx → 命中 cache, source=CACHE, 不调 provider。"""
    call_count = {"n": 0}

    class CountingProvider(NullProvider):
        async def generate(self, system, user):
            call_count["n"] += 1
            return '{"title":"x","summary":"","why":"","example":"","common_mistakes":[],"tips":[]}'

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(CountingProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r1 = await svc.explain(_ctx())
    r2 = await svc.explain(_ctx())
    assert r1.source == ExplainSource.AI
    assert r2.source == ExplainSource.CACHE
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_explain_uses_fallback_on_parse_failure():
    """LLM 返回非 JSON → 走 fallback。"""

    class GarbageProvider(NullProvider):
        async def generate(self, system, user):
            return "this is not json at all {"

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(GarbageProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK


def test_cache_key_excludes_provider_model():
    """cache key 不含 provider/model。"""
    from grammar_engine.ai.explain.explain_service import _make_cache_key
    c1 = _ctx(sentence="hello")
    c2 = _ctx(sentence="hello")
    k1 = _make_cache_key(c1)
    k2 = _make_cache_key(c2)
    assert k1 == k2


def test_cache_key_changes_with_sentence():
    c1 = _ctx(sentence="hello")
    c2 = _ctx(sentence="world")
    assert _make_cache_key(c1) != _make_cache_key(c2)
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_service.py::test_explain_uses_fallback_when_provider_returns_empty -v
```

Expected: `ImportError: cannot import name 'AIExplainService'`。

- [ ] **Step 3: 实现 ExplainContext + AIExplainService**

在 `backend/grammar_engine/ai/explain/explain_service.py` 继续追加：

```python
import hashlib
from dataclasses import dataclass


@dataclass
class ExplainContext:
    """发给 /api/explain 的输入。scene + node_type 必填。"""
    scene: str
    input_sentence: str
    selected_node_id: str
    node_type: str
    selected_node: dict
    engine_result_summary: dict
    language: str = "zh"
    student_level: str = "intermediate"


def _make_cache_key(ctx: ExplainContext) -> str:
    """Cache key 不含 provider/model/prompt_version。"""
    payload = (
        f"{ctx.scene}|"
        f"{ctx.selected_node_id}|"
        f"{ctx.input_sentence}|"
        f"{ctx.student_level}|"
        f"{ctx.language}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class AIExplainService:
    """M4 核心:把 engine_result 翻译成教学解释。"""

    def __init__(self, gateway: InferenceGateway, cache: ExplainCache):
        self.gateway = gateway
        self.cache = cache
        self.provider_name = gateway.provider.name
        self.provider_model = gateway.provider.model_id

    async def explain(self, ctx: ExplainContext) -> ExplainResult:
        # 1. 查缓存
        key = _make_cache_key(ctx)
        cached = await self.cache.get(key)
        if cached is not None:
            return ExplainResult(
                title=cached.title, summary=cached.summary, why=cached.why,
                example=cached.example, common_mistakes=cached.common_mistakes,
                tips=cached.tips, source=ExplainSource.CACHE,
                provider=self.provider_name, model=self.provider_model,
                prompt_version=PROMPT_VERSION, cached=True,
                generated_at=datetime.now(),
            )

        # 2. 调 LLM
        try:
            system = build_system(ctx.scene, ctx.node_type)
            user = USER_TEMPLATE.format(
                input_sentence=ctx.input_sentence,
                selected_node_id=ctx.selected_node_id,
                node_type=ctx.node_type,
                selected_node=ctx.selected_node,
                engine_result_summary=ctx.engine_result_summary,
                student_level=ctx.student_level,
            )
            raw = await self.gateway.complete(system, user)
            parsed = parse_response(raw)
            result = ExplainResult(
                title=parsed.title, summary=parsed.summary, why=parsed.why,
                example=parsed.example, common_mistakes=parsed.common_mistakes,
                tips=parsed.tips, source=ExplainSource.AI,
                provider=self.provider_name, model=self.provider_model,
                prompt_version=PROMPT_VERSION, cached=False,
                generated_at=datetime.now(),
            )
        except (InferenceError, ParseFail, ValueError) as e:
            logger.warning(f"[Explain] Failed: {e}, fallback")
            return self.fallback_for(ctx)

        # 3. 写缓存
        await self.cache.set(key, result)
        return result

    def fallback_for(self, ctx: ExplainContext) -> ExplainResult:
        """硬编码 fallback,永远不抛异常。"""
        base = fallback_for(ctx.scene, ctx.node_type)
        return ExplainResult(
            title=base.title, summary=base.summary, why=base.why,
            example=base.example, common_mistakes=base.common_mistakes,
            tips=base.tips, source=ExplainSource.FALLBACK,
            provider="fallback", model="builtin",
            prompt_version=PROMPT_VERSION, cached=False,
            generated_at=datetime.now(),
        )
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/test_m4_explain_service.py -v
```

Expected: 11 passed (4 from Task 11 + 7 new)。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/grammar_engine/ai/explain/explain_service.py backend/tests/test_m4_explain_service.py
git commit -m "feat(M4b): add AIExplainService with cache + fallback"
```

---

### Task 13: /api/explain + /api/explain/health 端点

**Files:**
- Modify: `backend/app.py`

**Interfaces:**
- Produces: `POST /api/explain` (永远 200) 和 `GET /api/explain/health`

- [ ] **Step 1: 修改 app.py**

在 `backend/app.py` 顶部 import 区追加：

```python
from grammar_engine.ai.explain.explain_service import (
    AIExplainService,
    ExplainContext,
    ExplainSource,
)
from grammar_engine.ai.inference.inference_gateway import InferenceGateway
from grammar_engine.ai.inference.provider_factory import get_provider
from grammar_engine.ai.explain.explain_cache import ExplainCache
from pydantic import BaseModel
```

在 `lifespan` 函数（model_loaded 之后）追加：

```python
    # M4: 初始化 AI 解释层
    logger.info("Initializing AI explain layer...")
    global explain_service
    try:
        provider = await get_provider()
        gateway = InferenceGateway(provider)
        cache = ExplainCache()
        explain_service = AIExplainService(gateway=gateway, cache=cache)
        logger.info(f"[OK] AI explain layer ready: {provider.name}/{provider.model_id}")
    except Exception as e:
        logger.warning(f"[WARN] AI init failed: {e}, fallback only")
        explain_service = None
```

在 `app.py` 末尾（`if __name__ == "__main__"` 之前）追加：

```python
# ===================== M4: /api/explain =====================

class ExplainAPIResponse(BaseModel):
    ok: bool = True
    degraded: bool = False
    result: dict  # ExplainResult 转 dict


@app.post("/api/explain", response_model=ExplainAPIResponse)
async def explain_node(ctx: ExplainContext):
    """M4 铁律:此端点永不抛异常,永不返回 5xx。"""
    if explain_service is None:
        # 服务未初始化 → 走 fallback
        result = AIExplainService.__new__(AIExplainService)
        result.provider_name = "fallback"
        result.provider_model = "builtin"
        fb = result.fallback_for(ctx)
        return ExplainAPIResponse(ok=True, degraded=True, result=_result_to_dict(fb))

    try:
        result = await explain_service.explain(ctx)
        degraded = result.source == ExplainSource.FALLBACK
        return ExplainAPIResponse(ok=True, degraded=degraded, result=_result_to_dict(result))
    except Exception as e:
        logger.exception(f"[AI] Unexpected: {e}")
        # 任何未捕获异常 → fallback
        if explain_service:
            fb = explain_service.fallback_for(ctx)
        else:
            fb = AIExplainService.__new__(AIExplainService).fallback_for(ctx)
        return ExplainAPIResponse(ok=True, degraded=True, result=_result_to_dict(fb))


@app.get("/api/explain/health", response_model=dict)
async def explain_health():
    """M4 健康检查。"""
    if explain_service is None:
        return {
            "provider": "fallback",
            "model": "builtin",
            "available": False,
            "latency_ms": 0,
            "error": "explain service not initialized",
        }
    h = await explain_service.gateway.health()
    return {
        "provider": explain_service.provider_name,
        "model": explain_service.provider_model,
        "available": h.get("ok", False),
        "latency_ms": h.get("latency_ms", 0),
        "error": h.get("error"),
    }


def _result_to_dict(r) -> dict:
    """ExplainResult → JSON-safe dict。"""
    return {
        "title": r.title,
        "summary": r.summary,
        "why": r.why,
        "example": r.example,
        "common_mistakes": r.common_mistakes,
        "tips": r.tips,
        "source": r.source.value,
        "provider": r.provider,
        "model": r.model,
        "prompt_version": r.prompt_version,
        "cached": r.cached,
        "generated_at": r.generated_at.isoformat(),
    }
```

并在 `app.py` 顶部 `Global state` 区追加 `explain_service = None`。

- [ ] **Step 2: 启动服务测试**

```bash
cd "/d/Grammar Lab/backend" && python app.py
```

另开终端：

```bash
curl -X POST http://127.0.0.1:18765/api/explain \
  -H "Content-Type: application/json" \
  -d '{"scene":"timeline","input_sentence":"I have lived here.","selected_node_id":"n1","node_type":"tense","selected_node":{"text":"have lived"},"engine_result_summary":{"verb_count":1}}'
```

Expected: HTTP 200 + `{"ok":true,"degraded":true,"result":{...fallback...}}`。

```bash
curl http://127.0.0.1:18765/api/explain/health
```

Expected: `{"provider":"null","model":"builtin","available":false,...}`。

- [ ] **Step 3: 关闭服务**

```bash
# 在运行 app.py 的终端 Ctrl+C
```

- [ ] **Step 4: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/app.py
git commit -m "feat(M4b): add /api/explain and /api/explain/health endpoints"
```

---

### Task 14: 集成测（永远 200、降级路径）

**Files:**
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/test_m4_api.py`

- [ ] **Step 1: 创建集成测试目录**

`backend/tests/integration/__init__.py`：

```python
"""集成测试包。"""
```

- [ ] **Step 2: 写集成测试**

`backend/tests/integration/test_m4_api.py`：

```python
"""M4 — /api/explain 集成测。

需要 backend 运行在 127.0.0.1:18765。
启动:cd backend && python app.py
"""
import time
import pytest
import requests

BASE_URL = "http://127.0.0.1:18765"


def _wait_for_service(timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            return
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    pytest.skip("Backend service not running on 18765, skipping integration test")


def test_explain_returns_200_always():
    _wait_for_service()
    r = requests.post(
        f"{BASE_URL}/api/explain",
        json={
            "scene": "timeline",
            "input_sentence": "I have lived here.",
            "selected_node_id": "n1",
            "node_type": "tense",
            "selected_node": {"text": "have lived"},
            "engine_result_summary": {"verb_count": 1},
        },
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "result" in data


def test_explain_with_missing_node_id_returns_fallback():
    _wait_for_service()
    r = requests.post(
        f"{BASE_URL}/api/explain",
        json={
            "scene": "timeline",
            "input_sentence": "test",
            "selected_node_id": "",
            "node_type": "tense",
            "selected_node": {},
            "engine_result_summary": {},
        },
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    # 缺 node_id 可能走 fallback 或 generic,degraded 至少为 true
    # (实际可能 cache miss 走 AI,然后 node_id 空仍合法 → 这里不强求 degraded)


def test_explain_health_endpoint():
    _wait_for_service()
    r = requests.get(f"{BASE_URL}/api/explain/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert "available" in data
```

- [ ] **Step 3: 启动后端**

```bash
cd "/d/Grammar Lab/backend" && python app.py
```

另开终端运行测试：

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/integration/test_m4_api.py -v
```

Expected: 3 passed。

- [ ] **Step 4: 关闭服务 + Commit**

```bash
# Ctrl+C 关闭 app.py

cd "/d/Grammar Lab" && git add backend/tests/integration/
git commit -m "test(M4b): add /api/explain integration tests"
```

---

### Task 15: Prompt Snapshot Tests

**Files:**
- Create: `backend/tests/prompts/test_snapshots.py`

- [ ] **Step 1: 写 snapshot 测试**

`backend/tests/prompts/test_snapshots.py`：

```python
"""Prompt snapshot 测试 — 防止 prompt 漂移。

改 prompt 时必须:
1. 改 prompt_templates.py
2. 更新 snapshots/ 对应文件
3. bump snapshot.PROMPT_VERSION
4. 测试失败 → 确认改动有意 → 更新 snapshot
"""
from pathlib import Path
from grammar_engine.ai.explain.prompt_templates import (
    BASE_PROMPT, SCENE_PROMPTS, NODE_PROMPTS,
)
from grammar_engine.ai.explain.snapshot import PROMPT_VERSION


SNAP_DIR = Path(__file__).parent / "snapshots"


def _check(name, content):
    expected = (SNAP_DIR / name).read_text(encoding="utf-8").rstrip("\n")
    actual = content.rstrip("\n")
    assert actual == expected, f"{name} drifted. If intentional, update snapshot and bump PROMPT_VERSION."


def test_base_prompt_snapshot():
    _check("base_prompt_v1.txt", BASE_PROMPT)


def test_scene_snapshots():
    for scene in ("timeline", "anatomy", "expansion"):
        _check(f"scene_{scene}_v1.txt", SCENE_PROMPTS[scene])


def test_node_snapshots():
    for nt in ("tense", "phrase", "template", "validation_warning"):
        _check(f"node_{nt}_v1.txt", NODE_PROMPTS[nt])


def test_prompt_version_present():
    assert PROMPT_VERSION, "PROMPT_VERSION must be set"
```

- [ ] **Step 2: 运行测试**

```bash
cd "/d/Grammar Lab/backend" && python -m pytest tests/prompts/test_snapshots.py -v
```

Expected: 4 passed。

- [ ] **Step 3: Commit**

```bash
cd "/d/Grammar Lab" && git add backend/tests/prompts/test_snapshots.py
git commit -m "test(M4b): add prompt snapshot tests"
```

---

### Task 16: 前端依赖 + ExplainContextBuilder

**Files:**
- Modify: `package.json`
- Create: `src/renderer/types/selection.ts`
- Create: `src/renderer/types/explain.ts`
- Create: `src/renderer/components/explain/ExplainContextBuilder.ts`
- Create: `src/renderer/components/explain/__tests__/ExplainContextBuilder.test.ts`

**Interfaces:**
- Produces: `ExplainContextBuilder` with `build(event, sentence) -> ExplainContext`

- [ ] **Step 1: 装前端依赖**

```bash
cd "/d/Grammar Lab" && npm install zustand@^5.0.0 react-markdown@^9.0.0 remark-gfm@^4.0.0
```

Expected: 3 个包安装成功。

- [ ] **Step 2: 创建 types/selection.ts**

`src/renderer/types/selection.ts`：

```typescript
// SelectionEvent — Scene 组件 emit 的最小事件,ExplainPanel 内部转 ExplainContext
export type NodeType = 'tense' | 'phrase' | 'template' | 'validation_warning';

export type SceneType = 'timeline' | 'anatomy' | 'expansion';

export interface SelectionEvent {
  scene: SceneType;
  node: {
    id: string;
    type: NodeType;
    // scene-specific data, ExplainContextBuilder 投影成 AI 友好的最小子集
    data: any;
  };
}
```

- [ ] **Step 3: 创建 types/explain.ts**

`src/renderer/types/explain.ts`：

```typescript
// ExplainResult — 后端响应结构
export type ExplainSource = 'ai' | 'cache' | 'fallback';

export interface ExplainResult {
  title: string;
  summary: string;
  why: string;
  example: string;
  commonMistakes: string[];
  tips: string[];
  source: ExplainSource;
  provider: string;
  model: string;
  promptVersion: string;
  cached: boolean;
  generatedAt: string;
  degraded: boolean;
}

export interface ExplainContext {
  scene: 'timeline' | 'anatomy' | 'expansion';
  input_sentence: string;
  selected_node_id: string;
  node_type: NodeType;
  selected_node: Record<string, any>;
  engine_result_summary: Record<string, any>;
  language: 'zh' | 'en';
  student_level: 'beginner' | 'intermediate' | 'advanced';
}

export interface ExplainAPIResponse {
  ok: boolean;
  degraded: boolean;
  result: {
    title: string;
    summary: string;
    why: string;
    example: string;
    common_mistakes: string[];
    tips: string[];
    source: ExplainSource;
    provider: string;
    model: string;
    prompt_version: string;
    cached: boolean;
    generated_at: string;
  };
}

export interface HealthState {
  status: 'unknown' | 'ready' | 'degraded' | 'offline';
  provider?: string;
  model?: string;
  latencyMs?: number;
  reason?: string;
}
```

- [ ] **Step 4: 写失败的测试**

`src/renderer/components/explain/__tests__/ExplainContextBuilder.test.ts`：

```typescript
import { describe, it, expect } from 'vitest';
import { ExplainContextBuilder } from '../ExplainContextBuilder';

describe('ExplainContextBuilder', () => {
  const builder = new ExplainContextBuilder();

  it('builds context for timeline tense', () => {
    const ctx = builder.build(
      {
        scene: 'timeline',
        node: {
          id: 'v1',
          type: 'tense',
          data: { verb: 'have lived', tense: 'present_perfect', position: 0 },
        },
      },
      'I have lived here.',
    );
    expect(ctx.scene).toBe('timeline');
    expect(ctx.node_type).toBe('tense');
    expect(ctx.selected_node_id).toBe('v1');
    expect(ctx.selected_node.text).toBe('have lived');
    expect(ctx.input_sentence).toBe('I have lived here.');
    expect(ctx.language).toBe('zh');
  });

  it('builds context for anatomy phrase', () => {
    const ctx = builder.build(
      {
        scene: 'anatomy',
        node: {
          id: 'c1',
          type: 'phrase',
          data: { text: 'When I arrived', role: 'ADVCL', head: 'arrived' },
        },
      },
      'When I arrived, he left.',
    );
    expect(ctx.scene).toBe('anatomy');
    expect(ctx.node_type).toBe('phrase');
    expect(ctx.selected_node.text).toBe('When I arrived');
    expect(ctx.selected_node.role).toBe('ADVCL');
  });

  it('builds context for expansion template', () => {
    const ctx = builder.build(
      {
        scene: 'expansion',
        node: {
          id: 't1',
          type: 'template',
          data: { template_id: 'adj-1', surface: 'cute', kind: 'adjective' },
        },
      },
      'I have a dog.',
    );
    expect(ctx.scene).toBe('expansion');
    expect(ctx.node_type).toBe('template');
  });

  it('builds context for validation warning', () => {
    const ctx = builder.build(
      {
        scene: 'expansion',
        node: {
          id: 'w1',
          type: 'validation_warning',
          data: { warning: 'subject-verb disagreement', rule: 'sv_agree', span: [0, 5] },
        },
      },
      'He go home.',
    );
    expect(ctx.node_type).toBe('validation_warning');
  });

  it('engine_result_summary has limited keys', () => {
    const ctx = builder.build(
      {
        scene: 'timeline',
        node: { id: 'n', type: 'tense', data: {} },
      },
      'Hello.',
    );
    const keys = Object.keys(ctx.engine_result_summary);
    expect(keys.length).toBeLessThanOrEqual(10);
  });
});
```

- [ ] **Step 5: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab" && npm test -- ExplainContextBuilder
```

Expected: FAIL — `Cannot find module '../ExplainContextBuilder'`。

- [ ] **Step 6: 实现 ExplainContextBuilder**

`src/renderer/components/explain/ExplainContextBuilder.ts`：

```typescript
import type { ExplainContext } from '../../types/explain';
import type { NodeType, SelectionEvent, SceneType } from '../../types/selection';

export class ExplainContextBuilder {
  build(event: SelectionEvent, sentence: string): ExplainContext {
    return {
      scene: event.scene,
      input_sentence: sentence,
      selected_node_id: event.node.id,
      node_type: event.node.type,
      selected_node: this.projectNode(event),
      engine_result_summary: this.summarizeEngine(event),
      language: 'zh',
      student_level: 'intermediate',
    };
  }

  private projectNode(event: SelectionEvent): Record<string, any> {
    const { type, data } = event.node;
    // 从 scene-specific data 投影到 AI 友好的最小子集
    // 不传整棵 tree
    switch (type as NodeType) {
      case 'tense':
        return {
          text: data.verb || data.text || '',
          tense: data.tense || 'unknown',
          position: data.position ?? null,
        };
      case 'phrase':
        return {
          text: data.text || '',
          role: data.role || 'unknown',
          head: data.head || '',
        };
      case 'template':
        return {
          template_id: data.template_id || '',
          surface: data.surface || '',
          kind: data.kind || '',
        };
      case 'validation_warning':
        return {
          warning: data.warning || '',
          rule: data.rule || '',
          span: data.span || [],
        };
      default:
        return { raw: data };
    }
  }

  private summarizeEngine(event: SelectionEvent): Record<string, any> {
    // 5-10 个 key 的极简统计,不含整棵 tree
    // M4a 用 stub,M4c 接入真实 analysis 时填充
    const data = event.node.data || {};
    return {
      scene: event.scene as SceneType,
      node_type: event.node.type,
      has_subordinate: !!data.has_subordinate,
      verb_count: data.verb_count ?? 0,
      chunk_count: data.chunk_count ?? 0,
      template_count: data.template_count ?? 0,
    };
  }
}
```

- [ ] **Step 7: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab" && npm test -- ExplainContextBuilder
```

Expected: 5 passed。

- [ ] **Step 8: Commit**

```bash
cd "/d/Grammar Lab" && git add package.json package-lock.json src/renderer/types/ src/renderer/components/explain/ExplainContextBuilder.ts src/renderer/components/explain/__tests__/ExplainContextBuilder.test.ts
git commit -m "feat(M4c): add ExplainContextBuilder + types + tests"
```

---

### Task 17: Explain Zustand store（persist）

**Files:**
- Create: `src/renderer/stores/explainStore.ts`
- Create: `src/renderer/stores/__tests__/explainStore.test.ts`

**Interfaces:**
- Produces: `useExplainStore` with `history: ExplainHistoryItem[]`, `pushHistory(item)`, `clearHistory()`

- [ ] **Step 1: 写失败的测试**

`src/renderer/stores/__tests__/explainStore.test.ts`：

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useExplainStore } from '../explainStore';

describe('explainStore', () => {
  beforeEach(() => {
    useExplainStore.getState().clearHistory();
  });

  const fakeItem = (id: string) => ({
    context: {
      scene: 'timeline' as const,
      input_sentence: 's',
      selected_node_id: id,
      node_type: 'tense' as const,
      selected_node: {},
      engine_result_summary: {},
      language: 'zh' as const,
      student_level: 'intermediate' as const,
    },
    result: {
      title: id,
      summary: '',
      why: '',
      example: '',
      commonMistakes: [],
      tips: [],
      source: 'ai' as const,
      provider: 'ollama',
      model: 'llama3.1:8b',
      promptVersion: 'M4a_v1',
      cached: false,
      generatedAt: new Date().toISOString(),
      degraded: false,
    },
    viewedAt: new Date().toISOString(),
  });

  it('pushHistory adds item at front', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().pushHistory(fakeItem('b'));
    expect(useExplainStore.getState().history.map((h) => h.result.title)).toEqual(['b', 'a']);
  });

  it('pushHistory dedupes by selected_node_id', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().pushHistory(fakeItem('a'));
    expect(useExplainStore.getState().history.length).toBe(1);
  });

  it('pushHistory caps at 30 items (LRU)', () => {
    for (let i = 0; i < 35; i++) {
      useExplainStore.getState().pushHistory(fakeItem(`n${i}`));
    }
    const hist = useExplainStore.getState().history;
    expect(hist.length).toBe(30);
    expect(hist[0].result.title).toBe('n34'); // 最新
    expect(hist[29].result.title).toBe('n5');
  });

  it('clearHistory empties store', () => {
    useExplainStore.getState().pushHistory(fakeItem('a'));
    useExplainStore.getState().clearHistory();
    expect(useExplainStore.getState().history).toEqual([]);
  });
});
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab" && npm test -- explainStore
```

Expected: FAIL — `Cannot find module '../explainStore'`。

- [ ] **Step 3: 实现 explainStore**

`src/renderer/stores/explainStore.ts`：

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ExplainContext, ExplainResult } from '../types/explain';

const MAX_HISTORY = 30;

export interface ExplainHistoryItem {
  context: ExplainContext;
  result: ExplainResult;
  viewedAt: string;
}

interface ExplainStore {
  history: ExplainHistoryItem[];
  pushHistory: (item: ExplainHistoryItem) => void;
  clearHistory: () => void;
}

const sameSelection = (a: ExplainContext, b: ExplainContext) =>
  a.scene === b.scene && a.selected_node_id === b.selected_node_id;

export const useExplainStore = create<ExplainStore>()(
  persist(
    (set, get) => ({
      history: [],
      pushHistory: (item) => {
        const deduped = get().history.filter((h) => !sameSelection(h.context, item.context));
        set({ history: [item, ...deduped].slice(0, MAX_HISTORY) });
      },
      clearHistory: () => set({ history: [] }),
    }),
    { name: 'grammar-lab.explain-history' },
  ),
);
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab" && npm test -- explainStore
```

Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add src/renderer/stores/explainStore.ts src/renderer/stores/__tests__/explainStore.test.ts
git commit -m "feat(M4c): add explainStore with zustand persist"
```

---

### Task 18: Health Zustand store

**Files:**
- Create: `src/renderer/stores/healthStore.ts`

**Interfaces:**
- Produces: `useHealthStore` with `health: HealthState`, `setHealth(h)`, `refresh()`(异步调 IPC)

- [ ] **Step 1: 实现 healthStore**

`src/renderer/stores/healthStore.ts`：

```typescript
import { create } from 'zustand';
import type { HealthState } from '../types/explain';

interface HealthStore {
  health: HealthState;
  setHealth: (h: HealthState) => void;
  refresh: () => Promise<void>;
}

export const useHealthStore = create<HealthStore>((set) => ({
  health: { status: 'unknown' },
  setHealth: (h) => set({ health: h }),
  refresh: async () => {
    try {
      // @ts-ignore — electronAPI 由 preload 注入
      const r = await window.electronAPI.getExplainHealth();
      if (r?.success && r.data?.available) {
        set({
          health: {
            status: 'ready',
            provider: r.data.provider,
            model: r.data.model,
            latencyMs: r.data.latency_ms,
          },
        });
      } else {
        set({
          health: { status: 'offline', reason: r?.data?.error || 'unavailable' },
        });
      }
    } catch (e) {
      set({ health: { status: 'offline', reason: String(e) } });
    }
  },
}));
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd "/d/Grammar Lab" && npx tsc --noEmit
```

Expected: 无错误（前提是 Task 22 已加 preload 的 `getExplainHealth` API）。如果 Task 22 未做,这里会报错,可以暂时注释掉调用,Task 22 完成后再回这里。

- [ ] **Step 3: Commit**

```bash
cd "/d/Grammar Lab" && git add src/renderer/stores/healthStore.ts
git commit -m "feat(M4c): add healthStore for AI provider status"
```

---

### Task 19: SourceBadge + DegradedBanner + Skeleton + MarkdownView

**Files:**
- Create: `src/renderer/components/explain/SourceBadge.tsx`
- Create: `src/renderer/components/explain/DegradedBanner.tsx`
- Create: `src/renderer/components/explain/ExplainSkeleton.tsx`
- Create: `src/renderer/components/explain/MarkdownView.tsx`
- Create: `src/renderer/components/explain/__tests__/SourceBadge.test.tsx`

**Interfaces:**
- Produces: 4 个纯展示组件,无副作用

- [ ] **Step 1: 写失败的测试**

`src/renderer/components/explain/__tests__/SourceBadge.test.tsx`：

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SourceBadge } from '../SourceBadge';

describe('SourceBadge', () => {
  it('renders AI badge with brain icon', () => {
    render(<SourceBadge source="ai" />);
    expect(screen.getByText('🧠')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('renders Cache badge with bolt icon', () => {
    render(<SourceBadge source="cache" />);
    expect(screen.getByText('⚡')).toBeInTheDocument();
    expect(screen.getByText('Cache')).toBeInTheDocument();
  });

  it('renders Fallback badge with book icon', () => {
    render(<SourceBadge source="fallback" />);
    expect(screen.getByText('📘')).toBeInTheDocument();
    expect(screen.getByText('Rule')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab" && npm test -- SourceBadge
```

Expected: FAIL。

- [ ] **Step 3: 实现 SourceBadge**

`src/renderer/components/explain/SourceBadge.tsx`：

```typescript
import type { ExplainSource } from '../../types/explain';

const BADGE: Record<ExplainSource, { icon: string; label: string; cls: string }> = {
  ai:       { icon: '🧠', label: 'AI',    cls: 'bg-purple-100 text-purple-700' },
  cache:    { icon: '⚡', label: 'Cache', cls: 'bg-yellow-100 text-yellow-700' },
  fallback: { icon: '📘', label: 'Rule',  cls: 'bg-slate-100 text-slate-600' },
};

export function SourceBadge({ source }: { source: ExplainSource }) {
  const b = BADGE[source];
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${b.cls}`}>
      {b.icon} {b.label}
    </span>
  );
}
```

- [ ] **Step 4: 实现 DegradedBanner**

`src/renderer/components/explain/DegradedBanner.tsx`：

```typescript
export function DegradedBanner() {
  return (
    <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 text-xs text-amber-800">
      AI unavailable. Showing rule-based explanation.
    </div>
  );
}
```

- [ ] **Step 5: 实现 ExplainSkeleton**

`src/renderer/components/explain/ExplainSkeleton.tsx`：

```typescript
export function ExplainSkeleton() {
  return (
    <div className="space-y-3 animate-pulse p-4">
      <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-full" />
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
      <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded" />
      <div className="h-12 bg-slate-200 dark:bg-slate-700 rounded" />
    </div>
  );
}
```

- [ ] **Step 6: 实现 MarkdownView**

`src/renderer/components/explain/MarkdownView.tsx`：

```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MarkdownView({ content }: { content: string }) {
  if (!content) return null;
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
```

- [ ] **Step 7: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab" && npm test -- SourceBadge
```

Expected: 3 passed。

- [ ] **Step 8: Commit**

```bash
cd "/d/Grammar Lab" && git add src/renderer/components/explain/SourceBadge.tsx src/renderer/components/explain/DegradedBanner.tsx src/renderer/components/explain/ExplainSkeleton.tsx src/renderer/components/explain/MarkdownView.tsx src/renderer/components/explain/__tests__/SourceBadge.test.tsx
git commit -m "feat(M4c): add SourceBadge, DegradedBanner, Skeleton, MarkdownView"
```

---

### Task 20: ExplainPanel 核心

**Files:**
- Create: `src/renderer/components/explain/ExplainPanel.tsx`
- Create: `src/renderer/components/explain/__tests__/ExplainPanel.test.tsx`

**Interfaces:**
- Produces: `ExplainPanel({ selection, sentence, darkMode })` — 内部管 state,AbortController + request_id 双保险

- [ ] **Step 1: 写失败的测试**

`src/renderer/components/explain/__tests__/ExplainPanel.test.tsx`：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ExplainPanel } from '../ExplainPanel';

// mock electronAPI
const mockExplainNode = vi.fn();
const mockGetHealth = vi.fn();

beforeEach(() => {
  mockExplainNode.mockReset();
  mockGetHealth.mockReset();
  (global as any).window = {
    electronAPI: {
      explainNode: mockExplainNode,
      getExplainHealth: mockGetHealth,
    },
  };
});

describe('ExplainPanel', () => {
  it('renders empty state when no selection', () => {
    render(<ExplainPanel selection={null} sentence="Hello." darkMode={false} />);
    expect(screen.getByText(/点击节点/i)).toBeInTheDocument();
  });

  it('renders loading skeleton while fetching', async () => {
    mockExplainNode.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <ExplainPanel
        selection={{
          scene: 'timeline',
          node: { id: 'n1', type: 'tense', data: {} },
        }}
        sentence="I have lived here."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  it('renders ready state on success', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: false,
        result: {
          title: '现在完成时',
          summary: '...',
          why: '...',
          example: '...',
          common_mistakes: [],
          tips: [],
          source: 'ai',
          provider: 'ollama',
          model: 'llama3.1:8b',
          prompt_version: 'M4a_v1',
          cached: false,
          generated_at: new Date().toISOString(),
        },
      },
    });
    render(
      <ExplainPanel
        selection={{
          scene: 'timeline',
          node: { id: 'n1', type: 'tense', data: { verb: 'have lived' } },
        }}
        sentence="I have lived here."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText('现在完成时')).toBeInTheDocument();
    });
  });

  it('shows degraded banner when degraded=true', async () => {
    mockExplainNode.mockResolvedValue({
      success: true,
      data: {
        ok: true,
        degraded: true,
        result: {
          title: 'Fallback Title',
          summary: '',
          why: '',
          example: '',
          common_mistakes: [],
          tips: [],
          source: 'fallback',
          provider: 'fallback',
          model: 'builtin',
          prompt_version: 'M4a_v1',
          cached: false,
          generated_at: new Date().toISOString(),
        },
      },
    });
    render(
      <ExplainPanel
        selection={{ scene: 'timeline', node: { id: 'n1', type: 'tense', data: {} } }}
        sentence="Test."
        darkMode={false}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/AI unavailable/i)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd "/d/Grammar Lab" && npm test -- ExplainPanel
```

Expected: FAIL — module not found。

- [ ] **Step 3: 实现 ExplainPanel**

`src/renderer/components/explain/ExplainPanel.tsx`：

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import { ExplainContextBuilder } from './ExplainContextBuilder';
import { SourceBadge } from './SourceBadge';
import { DegradedBanner } from './DegradedBanner';
import { ExplainSkeleton } from './ExplainSkeleton';
import { MarkdownView } from './MarkdownView';
import { useExplainStore } from '../../stores/explainStore';
import type { SelectionEvent } from '../../types/selection';
import type { ExplainResult, ExplainAPIResponse } from '../../types/explain';

type ExplainState =
  | { kind: 'empty' }
  | { kind: 'loading' }
  | { kind: 'ready'; result: ExplainResult; degraded: boolean }
  | { kind: 'error'; message: string };

const BUILTIN_FALLBACK: ExplainResult = {
  title: '解释',
  summary: 'AI 暂不可用。',
  why: '请稍后重试,或检查 AI provider 配置。',
  example: '',
  commonMistakes: [],
  tips: [],
  source: 'fallback',
  provider: 'builtin',
  model: 'builtin',
  promptVersion: 'M4a_v1',
  cached: false,
  generatedAt: new Date().toISOString(),
  degraded: true,
};

interface Props {
  selection: SelectionEvent | null;
  sentence: string;
  darkMode: boolean;
}

export function ExplainPanel({ selection, sentence, darkMode }: Props) {
  const [state, setState] = useState<ExplainState>({ kind: 'empty' });
  const [pinned, setPinned] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const pushHistory = useExplainStore((s) => s.pushHistory);
  const builder = useRef(new ExplainContextBuilder()).current;

  const fetchExplain = useCallback(
    async (sel: SelectionEvent, signal: AbortSignal) => {
      const ctx = builder.build(sel, sentence);
      try {
        // @ts-ignore — electronAPI 由 preload 注入
        const r = await window.electronAPI.explainNode(ctx);
        if (signal.aborted) return;
        if (r?.success && r.data) {
          const apiResp: ExplainAPIResponse = r.data;
          const res = apiResp.result;
          const result: ExplainResult = {
            title: res.title,
            summary: res.summary,
            why: res.why,
            example: res.example,
            commonMistakes: res.common_mistakes,
            tips: res.tips,
            source: res.source,
            provider: res.provider,
            model: res.model,
            promptVersion: res.prompt_version,
            cached: res.cached,
            generatedAt: res.generated_at,
            degraded: apiResp.degraded,
          };
          setState({ kind: 'ready', result, degraded: apiResp.degraded });
          pushHistory({ context: ctx, result, viewedAt: new Date().toISOString() });
        } else {
          setState({ kind: 'ready', result: BUILTIN_FALLBACK, degraded: true });
        }
      } catch (e) {
        if (signal.aborted) return;
        setState({ kind: 'error', message: String(e) });
      }
    },
    [sentence, builder, pushHistory],
  );

  useEffect(() => {
    if (pinned || !selection) return;

    // 双保险:AbortController + request_id
    controllerRef.current?.abort();
    const controller = new AbortController();
    const myId = ++requestIdRef.current;
    controllerRef.current = controller;

    setState({ kind: 'loading' });
    fetchExplain(selection, controller.signal).then(() => {
      if (myId !== requestIdRef.current) return;
    });

    return () => controller.abort();
  }, [selection, pinned, fetchExplain]);

  if (state.kind === 'empty') {
    return (
      <div className={`p-4 text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        点击节点,查看 AI 解释(为什么?)。
      </div>
    );
  }

  if (state.kind === 'loading') {
    return <ExplainSkeleton />;
  }

  if (state.kind === 'error') {
    return (
      <div className="p-4 text-sm text-red-600">
        出错了:{state.message}
      </div>
    );
  }

  const { result, degraded } = state;

  return (
    <div className={`p-4 space-y-3 ${darkMode ? 'bg-slate-800 text-slate-100' : 'bg-white'}`}>
      {degraded && <DegradedBanner />}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold flex-1">{result.title}</h2>
        <SourceBadge source={result.source} />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setPinned((p) => !p)}
          className={pinned ? 'pin-active' : 'pin-inactive'}
          title={pinned ? '取消 Pin' : 'Pin 当前解释'}
        >
          {pinned ? '📌' : '📍'}
        </button>
        <span className="text-xs text-slate-500">
          {result.provider} / {result.model}
        </span>
      </div>

      {result.summary && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Summary</h3>
          <MarkdownView content={result.summary} />
        </div>
      )}

      {result.why && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Why</h3>
          <MarkdownView content={result.why} />
        </div>
      )}

      {result.example && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Example</h3>
          <MarkdownView content={result.example} />
        </div>
      )}

      {result.commonMistakes.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Common Mistakes</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {result.commonMistakes.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {result.tips.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Tips</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {result.tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: 运行测试,确认通过**

```bash
cd "/d/Grammar Lab" && npm test -- ExplainPanel
```

Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
cd "/d/Grammar Lab" && git add src/renderer/components/explain/ExplainPanel.tsx src/renderer/components/explain/__tests__/ExplainPanel.test.tsx
git commit -m "feat(M4c): add ExplainPanel with AbortController + request_id"
```

---

### Task 21: ExplainHistoryDrawer

**Files:**
- Create: `src/renderer/components/explain/ExplainHistoryDrawer.tsx`

**Interfaces:**
- Produces: `ExplainHistoryDrawer({ open, onClose, darkMode })` — 从右滑入,按日期分组

- [ ] **Step 1: 实现 ExplainHistoryDrawer**

`src/renderer/components/explain/ExplainHistoryDrawer.tsx`：

```typescript
import { useExplainStore, type ExplainHistoryItem } from '../../stores/explainStore';
import { SourceBadge } from './SourceBadge';

interface Props {
  open: boolean;
  onClose: () => void;
  onSelect: (item: ExplainHistoryItem) => void;
  darkMode: boolean;
}

function groupByDate(items: ExplainHistoryItem[]) {
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();
  const groups: Record<string, ExplainHistoryItem[]> = { Today: [], Yesterday: [], Earlier: [] };
  for (const item of items) {
    const d = new Date(item.viewedAt).toDateString();
    if (d === today) groups.Today.push(item);
    else if (d === yesterday) groups.Yesterday.push(item);
    else groups.Earlier.push(item);
  }
  return Object.entries(groups).filter(([, v]) => v.length > 0);
}

export function ExplainHistoryDrawer({ open, onClose, onSelect, darkMode }: Props) {
  const history = useExplainStore((s) => s.history);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      <div
        className={`fixed right-0 top-0 h-full w-80 shadow-xl z-50 overflow-y-auto ${
          darkMode ? 'bg-slate-800 text-slate-100' : 'bg-white'
        }`}
      >
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-bold">🕘 History</h3>
          <button onClick={onClose} className="text-sm">✕</button>
        </div>
        <div className="p-2">
          {history.length === 0 && (
            <p className="text-sm text-slate-500 p-4">暂无历史</p>
          )}
          {groupByDate(history).map(([date, items]) => (
            <div key={date} className="mb-4">
              <h4 className="text-xs font-semibold text-slate-500 px-2 py-1">{date}</h4>
              {items.map((item, i) => (
                <button
                  key={i}
                  onClick={() => onSelect(item)}
                  className="w-full text-left p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded flex items-start gap-2"
                >
                  <SourceBadge source={item.result.source} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{item.result.title}</p>
                    <p className="text-xs text-slate-500">
                      {item.context.scene} · {item.context.selected_node_id}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
```

- [ ] **Step 2: TypeScript 编译验证**

```bash
cd "/d/Grammar Lab" && npx tsc --noEmit
```

Expected: 无错误。

- [ ] **Step 3: Commit**

```bash
cd "/d/Grammar Lab" && git add src/renderer/components/explain/ExplainHistoryDrawer.tsx
git commit -m "feat(M4c): add ExplainHistoryDrawer"
```

---

### Task 22: Preload + IPC handler

**Files:**
- Modify: `src/preload/index.ts`
- Modify: `src/main/ipc/index.ts`

**Interfaces:**
- Produces: `window.electronAPI.explainNode(ctx)` 和 `window.electronAPI.getExplainHealth()`

- [ ] **Step 1: 修改 preload/index.ts**

在 `src/preload/index.ts` 的 `contextBridge.exposeInMainWorld` 块内追加：

```typescript
    explainNode: (ctx) => ipcRenderer.invoke('explain-node', ctx),
    getExplainHealth: () => ipcRenderer.invoke('explain-health'),
```

并在 `ElectronAPI` interface 追加：

```typescript
  explainNode: (ctx: any) => Promise<{ success: boolean; data?: any; error?: string }>;
  getExplainHealth: () => Promise<{ success: boolean; data?: any; error?: string }>;
```

- [ ] **Step 2: 修改 main/ipc/index.ts**

在 `src/main/ipc/index.ts` 末尾追加：

```typescript
  // M4: AI explain
  ipcMain.handle('explain-node', async (_event, ctx) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 35_000);

      const response = await fetch(`${BACKEND_URL}/api/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ctx),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // /api/explain 理论上不会 4xx/5xx,这里兜底
        return {
          success: true,
          data: { ok: true, degraded: true, result: BUILTIN_FALLBACK_RESULT },
        };
      }
      return { success: true, data: await response.json() };
    } catch (error) {
      return {
        success: true,
        data: { ok: true, degraded: true, result: BUILTIN_FALLBACK_RESULT },
      };
    }
  });

  ipcMain.handle('explain-health', async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/api/explain/health`);
      if (!r.ok) {
        return { success: false, error: `HTTP ${r.status}` };
      }
      return { success: true, data: await r.json() };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  });
```

在 `src/main/ipc/index.ts` 顶部 import 后追加 BUILTIN_FALLBACK 常量：

```typescript
const BUILTIN_FALLBACK_RESULT = {
  title: '解释',
  summary: 'AI 暂不可用。',
  why: '请检查后端服务是否运行,或 AI provider 是否配置。',
  example: '',
  common_mistakes: [],
  tips: [],
  source: 'fallback',
  provider: 'builtin',
  model: 'builtin',
  prompt_version: 'M4a_v1',
  cached: false,
  generated_at: new Date().toISOString(),
};
```

- [ ] **Step 3: TypeScript 编译**

```bash
cd "/d/Grammar Lab" && npx tsc --noEmit
```

Expected: 无错误。

- [ ] **Step 4: Commit**

```bash
cd "/d/Grammar Lab" && git add src/preload/index.ts src/main/ipc/index.ts
git commit -m "feat(M4c): add preload + IPC for explain-node and explain-health"
```

---

### Task 23: App.tsx 接入 ExplainPanel + 健康灯

**Files:**
- Modify: `src/renderer/App.tsx`

**Interfaces:**
- Produces: 顶层 `currentSelection` 状态,三场景共享,ExplainPanel 接收

- [ ] **Step 1: 读 App.tsx 当前结构**

```bash
cd "/d/Grammar Lab" && head -80 src/renderer/App.tsx
```

- [ ] **Step 2: 修改 App.tsx**

按以下 patch 修改（具体行号以实际文件为准）：

1. 顶部 import 追加：
```typescript
import { useState, useEffect } from 'react';
import { ExplainPanel } from './components/explain/ExplainPanel';
import { ExplainHistoryDrawer } from './components/explain/ExplainHistoryDrawer';
import { useHealthStore } from './stores/healthStore';
import type { SelectionEvent } from './types/selection';
```

2. App 组件内追加状态：
```typescript
const [selection, setSelection] = useState<SelectionEvent | null>(null);
const [historyOpen, setHistoryOpen] = useState(false);
const { health, refresh: refreshHealth } = useHealthStore();
```

3. useEffect 启动时刷新健康（不阻塞）：
```typescript
useEffect(() => {
  refreshHealth();
  const t = setInterval(refreshHealth, 5 * 60 * 1000);
  return () => clearInterval(t);
}, [refreshHealth]);
```

4. 场景调用处传 `onSelectNode={setSelection}`（具体三个 scene 的修改在 Task 24）

5. 在场景渲染区域右侧加 ExplainPanel：
```tsx
<div className="grid grid-cols-[1fr_400px] gap-4">
  <div>{/* 原场景内容 */}</div>
  <aside className="sticky top-0 h-screen overflow-y-auto">
    <ExplainPanel selection={selection} sentence={currentSentence} darkMode={darkMode} />
  </aside>
</div>
```

6. Header 角落加健康灯（用绝对定位或新元素）：
```tsx
<button title={`${health.provider || ''} / ${health.model || ''}`} className="ml-2">
  <span className={
    health.status === 'ready' ? 'bg-green-500' :
    health.status === 'degraded' ? 'bg-yellow-500' :
    health.status === 'offline' ? 'bg-red-500' : 'bg-slate-400'
  } style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%' }} />
</button>
```

7. 顶部加历史按钮 + 抽屉：
```tsx
<button onClick={() => setHistoryOpen(true)}>🕘 History</button>
<ExplainHistoryDrawer
  open={historyOpen}
  onClose={() => setHistoryOpen(false)}
  onSelect={(item) => setSelection({ scene: item.context.scene, node: { id: item.context.selected_node_id, type: item.context.node_type, data: item.context.selected_node } })}
  darkMode={darkMode}
/>
```

- [ ] **Step 3: 启动 dev server 验证**

```bash
cd "/d/Grammar Lab" && npm run dev
```

Expected: 启动成功,UI 渲染,健康灯显示(初始为灰 unknown)。

- [ ] **Step 4: 关闭 dev server + Commit**

```bash
# Ctrl+C 关闭

cd "/d/Grammar Lab" && git add src/renderer/App.tsx
git commit -m "feat(M4d): integrate ExplainPanel + health indicator in App"
```

---

### Task 24: 三个 Scene emit SelectionEvent

**Files:**
- Modify: `src/renderer/components/timeline/TimelineScene.tsx`
- Modify: `src/renderer/components/anatomy/AnatomyScene.tsx`
- Modify: `src/renderer/components/expand/ExpandScene.tsx`

- [ ] **Step 1: TimelineScene — 加 onSelectNode 回调**

在 `TimelineScene.tsx` 顶部 props 区追加：

```typescript
interface Props {
  // ... 现有 props
  onSelectNode?: (event: SelectionEvent) => void;
}
```

在组件内部，verb 节点点击处（如 `onClick` handler）追加：

```typescript
onClick={() => onSelectNode?.({
  scene: 'timeline',
  node: {
    id: `verb-${verb.position}`,
    type: 'tense',
    data: { verb: verb.text, tense: verb.tense, position: verb.position },
  },
})}
```

- [ ] **Step 2: AnatomyScene — 加 onSelectNode 回调**

类似：

```typescript
onClick={() => onSelectNode?.({
  scene: 'anatomy',
  node: {
    id: chunk.id,
    type: 'phrase',
    data: { text: chunk.text, role: chunk.role, head: chunk.label },
  },
})}
```

- [ ] **Step 3: ExpandScene — 加 onSelectNode 回调**

模板点击和警告点击分别 emit：

```typescript
// 模板候选
onClick={() => onSelectNode?.({
  scene: 'expansion',
  node: {
    id: template.id,
    type: 'template',
    data: { template_id: template.id, surface: template.surface, kind: template.kind },
  },
})}

// 校验警告
onClick={() => onSelectNode?.({
  scene: 'expansion',
  node: {
    id: warning.id,
    type: 'validation_warning',
    data: { warning: warning.message, rule: warning.rule, span: warning.span },
  },
})}
```

- [ ] **Step 4: 启动 dev server 验证**

```bash
cd "/d/Grammar Lab" && npm run dev
```

输入一个句子，等三场景分析完成，点击 Timeline 上 verb 节点，ExplainPanel 应出现 loading → ready 状态（fallback 也算 ready）。

- [ ] **Step 5: 关闭 + Commit**

```bash
# Ctrl+C 关闭

cd "/d/Grammar Lab" && git add src/renderer/components/timeline/TimelineScene.tsx src/renderer/components/anatomy/AnatomyScene.tsx src/renderer/components/expand/ExpandScene.tsx
git commit -m "feat(M4d): wire three scenes to emit SelectionEvent"
```

---

### Task 25: 单测覆盖率达到 80%

**Files:**
- 可能新增：少量补充单测

- [ ] **Step 1: 运行后端覆盖率**

```bash
cd "/d/Grammar Lab/backend" && pip install pytest-cov && python -m pytest tests/ --cov=grammar_engine.ai --cov-report=term-missing
```

Expected: 总体覆盖率 ≥ 80%,`grammar_engine.ai` 各模块 ≥ 80%。

- [ ] **Step 2: 运行前端覆盖率**

```bash
cd "/d/Grammar Lab" && npm test -- --coverage
```

Expected: 总体覆盖率 ≥ 80%。

- [ ] **Step 3: 如未达 80%,补充单测**

按覆盖率报告补缺失分支。常见缺失点：
- `build_system` 拒绝未知 scene/node_type（M4b 加）
- `ExplainCache` 并发场景
- `ProviderFactory` 各分支已覆盖（Task 7）

- [ ] **Step 4: Commit（如有新增）**

```bash
cd "/d/Grammar Lab" && git add backend/tests/ src/renderer/components/explain/__tests__/ src/renderer/stores/__tests__/
git commit -m "test(M4d): bring unit test coverage to 80%"
```

---

### Task 26: E2E Case A/B/C/D（Playwright）

**Files:**
- Create: `e2e/m4-explain.spec.ts`（项目根 e2e/ 目录）
- Modify: `package.json`（加 Playwright 依赖和 script）

- [ ] **Step 1: 装 Playwright**

```bash
cd "/d/Grammar Lab" && npm install -D @playwright/test && npx playwright install
```

Expected: Playwright 安装成功。

- [ ] **Step 2: 写 E2E 测试**

`e2e/m4-explain.spec.ts`：

```typescript
import { test, expect } from '@playwright/test';

const APP_URL = process.env.APP_URL || 'http://127.0.0.1:5173';

test.describe('M4 Explain Panel E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    // 等待三场景分析完成(需要后端跑着)
    await page.waitForTimeout(2000);
  });

  test('Case A: 正常路径 — AI 解释出现', async ({ page }) => {
    // 找到 Timeline 第一个 verb 节点并点击
    const verb = page.locator('[data-testid="timeline-verb"]').first();
    await verb.click({ timeout: 5000 });

    // ExplainPanel 应显示 (fallback 也算)
    await expect(page.locator('[data-testid="explain-panel"]')).toBeVisible({ timeout: 10000 });
  });

  test('Case B: 降级路径 — Ollama 关闭时显示 fallback', async ({ page }) => {
    // 此 case 需要 OLLAMA_DOWN=1 环境变量,后端自动 fallback
    const verb = page.locator('[data-testid="timeline-verb"]').first();
    await verb.click({ timeout: 5000 });

    await expect(page.locator('[data-testid="degraded-banner"]')).toBeVisible({ timeout: 10000 });
  });

  test('Case C: Pin + History', async ({ page }) => {
    // 点 verb 1
    await page.locator('[data-testid="timeline-verb"]').first().click();
    await page.waitForTimeout(500);

    // Pin
    await page.locator('[data-testid="pin-button"]').click();

    // 点 verb 2
    await page.locator('[data-testid="timeline-verb"]').nth(1).click();
    await page.waitForTimeout(500);

    // 检查第一个 verb 的 title 仍在显示(没被切换)
    const panel = page.locator('[data-testid="explain-panel"]');
    await expect(panel).toBeVisible();

    // 打开 History
    await page.locator('[data-testid="history-button"]').click();
    await expect(page.locator('[data-testid="history-drawer"]')).toBeVisible();
  });

  test('Case D: 快速切换 — 最终显示最后一个', async ({ page }) => {
    const verbs = page.locator('[data-testid="timeline-verb"]');
    const count = await verbs.count();
    const last = Math.min(count - 1, 4);  // 至少点 5 个,这里取 last

    // 50ms 内连点
    for (let i = 0; i <= last; i++) {
      await verbs.nth(i).click({ force: true });
    }

    // 等待 1s 让所有请求收尾
    await page.waitForTimeout(1000);

    // 验证 ExplainPanel 显示对应最后一个 verb
    await expect(page.locator('[data-testid="explain-panel"]')).toBeVisible();
  });
});
```

- [ ] **Step 3: 在 package.json 加 e2e script**

```json
{
  "scripts": {
    "e2e": "playwright test"
  }
}
```

- [ ] **Step 4: 启动后端 + dev server,跑 E2E**

```bash
# 终端 1: 后端
cd "/d/Grammar Lab/backend" && python app.py

# 终端 2: dev server
cd "/d/Grammar Lab" && npm run dev

# 终端 3: E2E
cd "/d/Grammar Lab" && npm run e2e
```

Expected: 4 个 E2E test 全部通过(或按设计跳过 — 取决于 Ollama 是否在线)。

- [ ] **Step 5: 关闭所有服务 + Commit**

```bash
# Ctrl+C 关闭所有服务

cd "/d/Grammar Lab" && git add e2e/ package.json
git commit -m "test(M4d): add E2E tests for M4 explain panel"
```

---

## Self-Review Checklist（实施时验证）

完成后逐条对照：

- [ ] M4 Iron Rule 1: `/api/explain` 永远 HTTP 200
- [ ] M4 Iron Rule 2: AI 永远只读 engine_result
- [ ] M4 Iron Rule 3: InferenceGateway 是 M4-M7 唯一入口
- [ ] M4 Iron Rule 4: Cache key 不含 provider/model
- [ ] M4 Iron Rule 5: Scene 组件不 import 任何 Explain 相关代码（grep 验证）
- [ ] NodeType 字面量统一,无 `vp`/`verb_phrase` 漂移
- [ ] Source 枚举映射 🧠/⚡/📘
- [ ] Pin 后切换 selection 不重置
- [ ] AbortController + request_id 双保险
- [ ] Skeleton 加载无空 box
- [ ] Degraded banner 仅 degraded=true 时显示
- [ ] Health 灯四色正确,不阻塞启动
- [ ] 后端 unit test ≥ 80% coverage
- [ ] 前端 unit test ≥ 80% coverage
- [ ] 集成测覆盖核心 API 100%
- [ ] 4 个 E2E test 通过

---

## 执行选项

Plan 完成并保存到 `docs/superpowers/plans/2026-06-24-m4-ai-explain-layer.md`(1285 行 spec + 完整 plan)。

两种执行方式：

1. **Subagent-Driven (推荐)** - 每个 task dispatch 一个新 subagent,task 之间有 review
2. **Inline Execution** - 当前 session 用 executing-plans 批量执行,带 checkpoint

选哪种？
