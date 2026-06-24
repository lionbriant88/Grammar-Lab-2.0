# M4 — AI Explain Layer: Grammar Lab 的 AI 教师层

> 设计稿日期: 2026-06-24
> 状态: 待实施
> 前置: 阶段 0/1/2/3 全部完成（M3a-M3c5, 32 个从句模板, Benepar + LanguageTool 集成）
> 阶段: M4（AI 解释层）

---

## 0. 执行摘要

M4 在现有三个场景（Timeline / Anatomy / Expansion）之上叠加 **AI 解释层**，把 Grammar Lab 从"可视化语法实验室"升级为"可视化 + AI 教师"。

### 核心任务

1. **AIExplainService** 后端核心：把规则引擎结果翻译成自然语言解释
2. **InferenceGateway** 抽象层：M4-M7 共享的推理入口
3. **可插拔 Provider 架构**：Ollama 本地 + OpenAI/Anthropic 云端，零代码切换
4. **ExplainPanel 前端组件**：常驻右栏、Pin、History、Skeleton、降级显示
5. **SelectionEvent + ExplainContextBuilder**：Scene 与 Explain 完全解耦

### 架构原则（M4 铁律）

- **AI 永远只读**：AI 不解析句子、不决定语法结构、不修改 phrase tree
- **Grammar Engine 是唯一权威**：所有 grammar decisions 来自确定性引擎
- **/api/explain 永远 HTTP 200**：任何异常降级到 fallback result，前端只处理一种响应模式
- **AI 加载不阻塞场景渲染**：ExplainPanel 是异步第四层，场景先显示
- **InferenceGateway 单一入口**：M5/M6/M7 复用，不重复接 provider

### M4 完成后

- ✅ 三场景每个节点都有"为什么？"解释
- ✅ AI 可用/降级/离线三态透明显示
- ✅ Pin + History 让学生流式学习
- ✅ Provider 切换零代码改动（改 config.json）
- ✅ M5 Shadow Rewrite / M6 Chat 复用 InferenceGateway

---

## 1. 架构总览

### 1.1 数据流

```
┌──────────────────────────────────────────────────────────────┐
│ Renderer (React + Electron)                                  │
│                                                              │
│  TimelineScene    AnatomyScene    ExpandScene                │
│       │                │              │                      │
│       └──── emit SelectionEvent ──────┘                      │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                              │
│              │  App.tsx        │                              │
│              │  (selection)    │                              │
│              └────────┬────────┘                              │
│                       │ prop                                 │
│                       ▼                                      │
│              ┌─────────────────┐                              │
│              │  ExplainPanel   │  (常驻右栏 400px)            │
│              │  ─────────────  │                              │
│              │  📌 🕘 Health   │                              │
│              │  ─────────────  │                              │
│              │  Inspector      │  (现有)                       │
│              │  Explain        │  (新)                        │
│              │   - Title       │                              │
│              │   - Summary     │                              │
│              │   - Why         │                              │
│              │   - Example     │                              │
│              │   - Mistakes    │                              │
│              │   - Tips        │                              │
│              └─────────────────┘                              │
└──────────────────────┬───────────────────────────────────────┘
                       │  IPC: explain-node
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Main process (Electron)                                      │
└──────────────────────┬───────────────────────────────────────┘
                       │  HTTP POST /api/explain
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Backend (FastAPI :18765)                                     │
│                                                              │
│   /api/tense/analyze  /api/anatomy/analyze  /api/expansion/  │
│        │                    │                    │           │
│        └────── rule engine (现有) ─────────────┘             │
│                         │                                    │
│                         ▼                                    │
│   /api/explain  ──►  AIExplainService                        │
│                          │                                   │
│                          ▼                                   │
│                   InferenceGateway                           │
│                          │                                   │
│                          ▼                                   │
│                   ProviderFactory                            │
│                          │                                   │
│              ┌───────────┼───────────┐                       │
│              ▼           ▼           ▼                       │
│        OllamaProvider  CloudProvider  NullProvider           │
│        (本地)          (云)          (fallback)              │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
backend/ai/
├── inference/                       # M4-M7 共享
│   ├── inference_gateway.py
│   ├── provider_factory.py
│   └── providers/
│       ├── provider_base.py
│       ├── ollama_provider.py
│       ├── cloud_provider.py        # OpenAI + Anthropic 统一封装
│       ├── # M5+ stub
│       └── gemma_provider.py        # M5+ stub
├── explain/                         # M4 业务
│   ├── explain_service.py
│   ├── prompt_templates.py
│   ├── explain_cache.py
│   ├── fallback_explanations.py
│   └── snapshot.py
└── config.json                      # provider 配置

src/renderer/components/explain/
├── ExplainPanel.tsx
├── ExplainContextBuilder.ts
├── ExplainHistoryDrawer.tsx
├── ExplainSkeleton.tsx
├── SourceBadge.tsx
└── DegradedBanner.tsx
```

---

## 2. 核心数据契约

### 2.1 ExplainContext（前端构造，发给后端）

```python
@dataclass
class ExplainContext:
    scene: Literal["timeline", "anatomy", "expansion"]
    input_sentence: str
    selected_node_id: str
    node_type: NodeType            # "tense" | "phrase" | "template" | "validation_warning"
    selected_node: dict            # 当前节点: {type, text, role, ...} 最小子集
    engine_result_summary: dict    # 5-10 个 key 的极简统计,不含整棵 tree
    language: Literal["zh", "en"] = "zh"
    student_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
```

**铁律**：
- 不传整棵 phrase tree 给 AI
- `selected_node` 由 `ExplainContextBuilder.projectNode()` 投影得到
- `engine_result_summary` 由 `ExplainContextBuilder.summarizeEngine()` 构造

### 2.2 NodeType 显式枚举

```python
NodeType = Literal["tense", "phrase", "template", "validation_warning"]
```

- 禁止动态推断（`ctx.node_type(ctx)` 删掉）
- 禁止命名漂移（`vp` / `verb_phrase` / `phrase_vp` 一律用 `phrase`）

### 2.3 ExplainResult

```python
class ExplainSource(str, Enum):
    AI = "ai"
    CACHE = "cache"
    FALLBACK = "fallback"

@dataclass
class ExplainResult:
    title: str
    summary: str
    why: str
    example: str
    common_mistakes: list[str]
    tips: list[str]
    source: ExplainSource
    provider: str                 # "ollama" | "openai" | "anthropic" | "fallback"
    model: str                    # "llama3.1:8b" | "gpt-4o-mini"
    prompt_version: str           # "M4a_v1"
    cached: bool
    generated_at: datetime
```

### 2.4 API Response

```python
class ExplainAPIResponse(BaseModel):
    ok: bool = True
    degraded: bool = False
    result: ExplainResult
```

**M4 铁律：`/api/explain` 永远 HTTP 200**。前端只处理这一种响应模式。

---

## 3. Provider 层

### 3.1 AIProvider 抽象基类

```python
# backend/ai/inference/providers/provider_base.py
from abc import ABC, abstractmethod

class AIProvider(ABC):
    name: str
    model_id: str
    
    @abstractmethod
    async def generate(self, system: str, user: str) -> str: ...
    
    @abstractmethod
    async def health_check(self) -> dict:
        """返回 {ok: bool, latency_ms: int, error?: str}"""
        ...
```

### 3.2 OllamaProvider（本地）

```python
class OllamaProvider(AIProvider):
    name = "ollama"
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self.model_id = model
    
    async def is_available(self) -> bool:
        """探测 GET /api/tags，3 秒超时"""
        ...
    
    async def generate(self, system: str, user: str) -> str:
        """POST /api/generate, stream=false, 30 秒超时"""
        ...
    
    async def health_check(self) -> dict:
        """测 latency"""
        ...
```

### 3.3 CloudProvider（OpenAI / Anthropic）

```python
class CloudProvider(AIProvider):
    """OpenAI / Anthropic 统一封装,按 env 决定具体厂商。"""
    
    def __init__(self):
        # 读 env:
        #   AI_CLOUD_PROVIDER=openai|anthropic
        #   AI_CLOUD_MODEL=gpt-4o-mini|claude-haiku-4-5-20251001
        #   AI_CLOUD_API_KEY=sk-...
        ...
```

**API key 不存文件，从环境变量读取**。前端设置页提供输入框，存到 Electron `app.getPath('userData')` 加密文件。

### 3.4 Provider 选择逻辑

```python
# backend/ai/inference/provider_factory.py
async def get_provider() -> AIProvider:
    cfg = load_config()  # 读 backend/ai/config.json
    
    # 优先级: cloud (如果配了 key) > ollama (如果运行中) > fallback
    if cfg.cloud_api_key:
        return CloudProvider(...)
    if await OllamaProvider().is_available():
        return OllamaProvider(...)
    return NullProvider()
```

### 3.5 NullProvider（fallback）

```python
class NullProvider(AIProvider):
    name = "fallback"
    model_id = "builtin"
    
    async def generate(self, system: str, user: str) -> str:
        raise NotImplementedError("NullProvider only supports fallback")
    
    async def health_check(self) -> dict:
        return {"ok": False, "error": "no provider configured"}
```

### 3.6 配置文件

`backend/ai/config.json`：

```json
{
  "default_provider": "auto",
  "ollama": {
    "base_url": "http://127.0.0.1:11434",
    "model": "llama3.1:8b"
  },
  "cloud": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key_env": "AI_CLOUD_API_KEY"
  },
  "cache": {
    "ttl_seconds": 86400,
    "max_entries": 500
  },
  "timeout_seconds": 30
}
```

### 3.7 降级矩阵

| 场景 | 行为 |
|---|---|
| Ollama 未启动 | 自动切到 NullProvider (fallback) |
| Ollama 启动但模型未拉 | 返回 ERROR + 提示 `ollama pull llama3.1:8b` |
| Cloud 无 API key | NullProvider |
| Cloud API 超时/429 | tenacity 重试 1 次 → fallback |
| 所有 provider 失败 | NullProvider + 硬编码解释库 |

### 3.8 依赖更新

`backend/requirements.txt` 新增：

```
ollama>=0.4.0
openai>=1.50.0
httpx>=0.27.0
tenacity>=9.0.0
cachetools>=5.5.0
pydantic>=2.9.2     # 已有
```

---

## 4. InferenceGateway（M4-M7 共享入口）

```python
# backend/ai/inference/inference_gateway.py
class InferenceError(Exception):
    """Provider 失败时抛出,由调用方决定降级策略。"""
    pass


class InferenceGateway:
    """M4-M7 共享的唯一推理入口。
    
    M4: AIExplainService 调用 complete()
    M5: RewriteService 调用 complete() (Shadow Mode)
    M6: ChatService 调用 complete() 流式
    M7: 任何新 AI 功能复用
    """
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
    
    async def complete(self, system: str, user: str) -> str:
        try:
            return await self.provider.generate(system, user)
        except Exception as e:
            logger.warning(f"[Inference] Provider failed: {e}")
            raise InferenceError(str(e))
    
    async def health(self) -> dict:
        return await self.provider.health_check()
```

**M4 不在此层做降级**：降级由调用方（AIExplainService）决定，保留 M5/M6 各自不同的降级策略灵活性。

---

## 5. ExplainService

### 5.1 完整签名

```python
class AIExplainService:
    def __init__(self, gateway: InferenceGateway, cache: ExplainCache):
        self.gateway = gateway
        self.cache = cache
        self.prompts = PromptTemplateRegistry()
    
    async def explain(self, ctx: ExplainContext) -> ExplainResult: ...
    def fallback_for(self, ctx: ExplainContext) -> ExplainResult: ...
    
    # 内部
    def _build_system(self, ctx: ExplainContext) -> str: ...
    def _build_user(self, ctx: ExplainContext) -> str: ...
    def _parse_response(self, raw: str) -> ExplainResponseModel: ...
    def _cache_key(self, ctx: ExplainContext) -> str: ...
    def _to_result(self, parsed, source, cached) -> ExplainResult: ...
```

### 5.2 explain() 主流程

```python
async def explain(self, ctx: ExplainContext) -> ExplainResult:
    # 1. 构造 prompt
    system = self._build_system(ctx)
    user = self._build_user(ctx)
    
    # 2. 查缓存
    key = self._cache_key(ctx)
    if cached := await self.cache.get(key):
        return self._to_result(cached, source=ExplainSource.CACHE, cached=True)
    
    # 3. 调 LLM
    try:
        raw = await self.gateway.complete(system, user)
        parsed = self._parse_response(raw)
        result = self._to_result(parsed, source=ExplainSource.AI, cached=False)
    except Exception as e:
        logger.warning(f"[Explain] Failed: {e}, fallback")
        return self.fallback_for(ctx)
    
    # 4. 写缓存 + 返回
    await self.cache.set(key, result)
    return result
```

### 5.3 Cache Key 设计

```python
def _cache_key(self, ctx: ExplainContext) -> str:
    # 缓存的是"教学解释",不是某模型输出
    # provider/model 不进 key
    payload = (
        f"{ctx.scene}|"
        f"{ctx.selected_node_id}|"
        f"{ctx.input_sentence}|"
        f"{ctx.student_level}|"
        f"{ctx.language}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()
```

切换 →Gemma3→ 不会因 key 不匹配导致 cache 失效，跨 provider 复用。

### 5.4 Prompt 三层结构

```python
BASE_PROMPT = """你是 Grammar Lab 的 AI 语法教师。
规则:① 严禁自己重新解析句子 ② 严禁修改引擎结果 ③ 只解释,不决定。
输出严格 JSON: {title, summary, why, example, common_mistakes:[], tips:[]}。"""

SCENE_PROMPTS = {
    "timeline":  "场景:时间轴。任务:解释为什么识别为这个时态。",
    "anatomy":   "场景:句剖析。任务:解释这个短语为什么是某个角色。",
    "expansion": "场景:句扩展。任务:解释为什么推荐这个扩展方式。",
}

NODE_PROMPTS = {
    "tense":              "节点类型:时态。说明与相近时态的区别、信号词。",
    "phrase":             "节点类型:短语。说明为什么是这个 syntactic_role、修饰什么。",
    "template":           "节点类型:扩展模板。说明为什么这个扩展合适、不扩展会怎样。",
    "validation_warning": "节点类型:校验警告。说明语法问题、如何修正。",
}

def _build_system(self, ctx: ExplainContext) -> str:
    return f"{BASE_PROMPT}\n{SCENE_PROMPTS[ctx.scene]}\n{NODE_PROMPTS[ctx.node_type]}"
```

每条 prompt 模板只负责 **user 部分**，system 由三层拼接。

### 5.5 Pydantic 解析

```python
class ExplainResponseModel(BaseModel):
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)

def _parse_response(self, raw: str) -> ExplainResponseModel:
    try:
        return ExplainResponseModel.model_validate_json(raw)
    except (ValidationError, ValueError) as e:
        logger.warning(f"[AI] Parse failed: {e}")
        raise ParseFail()
```

解析失败抛 `ParseFail()` 内部异常，外层 try/except 捕获走 fallback。**永远不向外抛**。

### 5.6 Cache 实现（cachetools.TTLCache）

```python
from cachetools import TTLCache

class ExplainCache:
    def __init__(self, ttl: int = 86400, maxsize: int = 500):
        self._store: TTLCache[str, ExplainResult] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> ExplainResult | None:
        async with self._lock:
            return self._store.get(key)
    
    async def set(self, key: str, result: ExplainResult) -> None:
        async with self._lock:
            self._store[key] = result
```

不用手写 LRU/TTL。cachetools 不是 async-safe，lock 包住 IO 边界。

### 5.7 Fallback 硬编码库

`backend/ai/explain/fallback_explanations.py`：

```python
FALLBACK_LIBRARY: dict[tuple[str, str], ExplainResult] = {
    ("timeline", "tense"): ExplainResult(
        title="时态解释",
        summary="(规则库解释,AI 暂不可用)",
        why="时态由规则引擎根据动词形态和时间状语综合判断。",
        example="...",
        common_mistakes=["与相近时态混淆"],
        tips=["查看时间状语判定时态"],
        source=ExplainSource.FALLBACK,
        provider="fallback",
        model="builtin",
        prompt_version="M4a_v1",
        cached=False,
        generated_at=None,  # 运行时填充
    ),
    # ... 每个 (scene, node_type) 一条
}

FALLBACK_GENERIC = ExplainResult(...)  # 兜底
```

---

## 6. FastAPI 端点

### 6.1 POST /api/explain

```python
class ExplainAPIResponse(BaseModel):
    ok: bool = True
    degraded: bool = False
    result: ExplainResult

@app.post("/api/explain", response_model=ExplainAPIResponse)
async def explain_node(ctx: ExplainContext):
    """M4 铁律:此端点永不抛异常,永不返回 5xx。"""
    try:
        result = await explain_service.explain(ctx)
        return ExplainAPIResponse(
            ok=True,
            degraded=(result.source == ExplainSource.FALLBACK),
            result=result,
        )
    except Exception as e:
        logger.exception(f"[AI] Unexpected error, returning fallback: {e}")
        return ExplainAPIResponse(
            ok=True,
            degraded=True,
            result=explain_service.fallback_for(ctx),
        )
```

**所有降级路径统一**：`{ok: true, degraded: true, result: fallback}`。前端只处理这一种模式。

### 6.2 GET /api/explain/health

```python
@app.get("/api/explain/health", response_model=ExplainHealthResponse)
async def explain_health():
    health = await inference_gateway.health()
    return ExplainHealthResponse(
        provider=inference_gateway.provider.name,
        model=inference_gateway.provider.model_id,
        available=health.get("ok", False),
        latency_ms=health.get("latency_ms", 0),
        error=health.get("error"),
    )
```

前端设置页用此端点显示 provider 状态。

---

## 7. 前端集成

### 7.1 SelectionEvent + ExplainContextBuilder（解耦 Scene）

```typescript
// types/selection.ts
export type NodeType = 'tense' | 'phrase' | 'template' | 'validation_warning';

export type SelectionEvent = {
  scene: 'timeline' | 'anatomy' | 'expansion';
  node: {
    id: string;
    type: NodeType;
    data: SceneNodeData;  // VerbInfo | ChunkInfo | TemplateInfo | WarningInfo
  };
};

// components/explain/ExplainContextBuilder.ts
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
  
  private projectNode(event: SelectionEvent): dict {
    // 从 scene-specific 字段投影到 AI 友好的最小子集
  }
  
  private summarizeEngine(event: SelectionEvent): dict {
    // 5-10 个 key 的极简统计
  }
}
```

**Scene 组件只 emit SelectionEvent**，不构造 ExplainContext，不 import 任何 Explain 相关代码。

### 7.2 三个 Scene 接入示例

```typescript
// TimelineScene.tsx
<TimelineScene
  onSelectNode={(node) => onSelectNode({
    scene: 'timeline',
    node: { id: node.id, type: 'tense', data: node }
  })}
/>

// AnatomyScene.tsx
<AnatomyScene
  onSelectNode={(chunk) => onSelectNode({
    scene: 'anatomy',
    node: { id: chunk.id, type: 'phrase', data: chunk }
  })}
/>

// ExpandScene.tsx
<ExpandScene
  onSelectNode={(event) => onSelectNode({
    scene: 'expansion',
    node: {
      id: event.id,
      type: event.kind === 'validation' ? 'validation_warning' : 'template',
      data: event
    }
  })}
/>
```

### 7.3 ExplainPanel 自治状态

```typescript
// ExplainPanel.tsx
const [state, setState] = useState<ExplainState>({ kind: 'empty' });
const [history] = useExplainStore();  // Zustand persist
const [pinned, setPinned] = useState(false);

useEffect(() => {
  if (pinned || !selection) return;
  
  controllerRef.current?.abort();
  const controller = new AbortController();
  const myId = ++requestIdRef.current;
  controllerRef.current = controller;
  
  fetchExplain(selection, controller.signal)
    .then(result => {
      if (myId !== requestIdRef.current) return;
      if (controller.signal.aborted) return;
      setState({ kind: 'ready', result });
      pushHistory({ context, result, viewedAt: new Date().toISOString() });
    })
    .catch(err => {
      if (err.name === 'AbortError') return;
      if (myId !== requestIdRef.current) return;
      setState({ kind: 'error', message: err.message });
    });
  
  return () => controller.abort();
}, [selection, pinned]);
```

**ExplainPanel 内部 state**：App 只传 `selection`，不持有 Explain 内部状态。

### 7.4 AbortController + request_id 双保险

```typescript
const controllerRef = useRef<AbortController | null>(null);
const requestIdRef = useRef(0);

// 快速切换 node1→node2→node3:
// 1. abort 前两次 controller
// 2. request_id 防护:即使 abort 失败,过期响应也不写
// 3. 最终只有 node3 的响应能 setState
```

### 7.5 State Machine

```
              selection change (unpinned)
        ┌─────────────────────────────────────┐
        │                                     ▼
[empty] ─► [loading] ─► [ready] ─► 用户点 Pin ─► [ready.pinned=true]
              │            │                          │
              │ 失败/超时   │  selection change        │ 再次点 Pin
              ▼            │ (unpinned)               ▼
          [error] ──────────┘                     [ready.pinned=false]
              │                                       │
              │ 5s 后自动 retry                       │
              └───────────────────────────────────────┘
```

### 7.6 Skeleton Loading

```typescript
{state.kind === 'loading' && (
  <div className="space-y-3 animate-pulse">
    <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-3/4 shimmer" />
    <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-full shimmer" />
    <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-5/6 shimmer" />
    <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded shimmer" />
    <div className="h-12 bg-slate-200 dark:bg-slate-700 rounded shimmer" />
  </div>
)}
```

Tailwind config 加 shimmer 动画。绝不放空 box。

### 7.7 Source Badge + Degraded Banner

```typescript
const SOURCE_BADGE = {
  ai:       { icon: '🧠', label: 'AI',    cls: 'bg-purple-100 text-purple-700' },
  cache:    { icon: '⚡', label: 'Cache', cls: 'bg-yellow-100 text-yellow-700' },
  fallback: { icon: '📘', label: 'Rule',  cls: 'bg-slate-100 text-slate-600' },
};

{result.degraded && (
  <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 text-xs text-amber-800">
    AI unavailable. Showing rule-based explanation.
  </div>
)}

<header>
  <h2>{result.title}</h2>
  <span className={`px-2 py-0.5 rounded-full text-xs ${SOURCE_BADGE[result.source].cls}`}>
    {SOURCE_BADGE[result.source].icon} {SOURCE_BADGE[result.source].label}
  </span>
</header>
```

### 7.8 Pin 视觉

```css
.pin-active {
  background: #fef3c7;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.6);
}
.pin-inactive {
  /* 描边 */
}
```

Pinned 时 selection 变化不触发新请求，Pin icon 持续高亮。

### 7.9 History Drawer（不是 `<select>`）

```typescript
// ExplainHistoryDrawer.tsx
<button onClick={toggleHistory}>🕘 History</button>

{drawerOpen && (
  <div className="fixed right-0 top-0 h-full w-80 bg-white shadow-xl z-50">
    <h3>History</h3>
    {groupedByDate(history).map(group => (
      <div>
        <h4>{group.date}</h4>
        {group.items.map(item => (
          <button onClick={() => restoreFromHistory(item)}>
            <SourceBadge source={item.result.source} />
            <span>{item.result.title}</span>
          </button>
        ))}
      </div>
    ))}
  </div>
)}
```

### 7.10 Zustand + Persist 替代 sessionStorage

```typescript
// stores/explainStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const MAX_HISTORY = 30;

interface ExplainStore {
  history: ExplainHistoryItem[];
  pushHistory: (item: ExplainHistoryItem) => void;
  clearHistory: () => void;
}

export const useExplainStore = create<ExplainStore>()(
  persist(
    (set, get) => ({
      history: [],
      pushHistory: (item) => {
        const deduped = get().history.filter(
          i => !sameSelection(i.context, item.context)
        );
        set({ history: [item, ...deduped].slice(0, MAX_HISTORY) });
      },
      clearHistory: () => set({ history: [] }),
    }),
    { name: 'grammar-lab.explain-history' }
  )
);
```

**刷新页面历史不丢**。容量 30，LRU 淘汰。

### 7.11 ExplainPanel 宽度

```css
.explain-panel {
  position: sticky;
  top: 0;
  width: 400px;        /* 380-420 中间值 */
  max-height: 100vh;
  overflow-y: auto;    /* 长内容自己滚 */
  flex-shrink: 0;
}
```

三个场景 grid 布局：`grid-cols-[1fr_400px]`，左场景 + 右 ExplainPanel。无论场景多复杂，ExplainPanel 大小不变。

### 7.12 Health Indicator

```typescript
// AppHeader.tsx 角落
type HealthState =
  | { status: 'unknown' }
  | { status: 'ready'; provider: string; model: string; latencyMs: number }
  | { status: 'degraded'; reason: string }
  | { status: 'offline'; reason: string };

<button title={`${provider} / ${model} / ${latencyMs}ms`}>
  <span className={dotColor(health)} />
</button>
```

四种状态（unknown/ready/degraded/offline），对应四色 dot（灰/绿/黄/红）。

### 7.13 Health Check 不阻塞启动

```typescript
// App.tsx
const { health, refresh } = useExplainHealth();

useEffect(() => { refresh(); }, []);  // 启动时拉一次
useEffect(() => {
  const timer = setInterval(refresh, 5 * 60 * 1000);  // 每 5 分钟后台刷新
  return () => clearInterval(timer);
}, [refresh]);
```

App 启动不 await health，UI 立即可交互，dot 异步更新。

### 7.14 IPC 接入

`src/main/ipc/index.ts` 新增：

```typescript
ipcMain.handle('explain-node', async (_event, ctx: ExplainContext) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ctx),
      signal: AbortSignal.timeout(35_000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return { success: true, data: await response.json() };
  } catch (error) {
    // 网络层失败 → 返回 ok=true, degraded=true, 内置 fallback
    return {
      success: true,
      data: {
        ok: true, degraded: true,
        result: BUILTIN_FALLBACK,
      },
    };
  }
});
```

`src/preload/index.ts` 新增：

```typescript
contextBridge.exposeInMainWorld('electronAPI', {
  // ... 现有
  explainNode: (ctx: ExplainContext) => ipcRenderer.invoke('explain-node', ctx),
  getExplainHealth: () => ipcRenderer.invoke('explain-health'),
});
```

### 7.15 Scene 节点 → SelectionEvent 映射

| 场景 | 用户点击 | node_type | selected_node.data |
|---|---|---|---|
| Timeline | 时间轴 verb 节点 | `tense` | `{verb, tense, position}` |
| Anatomy | 句剖析 chunk | `phrase` | `{text, role, head}` |
| Expansion | 模板候选 | `template` | `{template_id, surface, kind}` |
| Expansion | 校验警告 | `validation_warning` | `{warning, rule, span}` |

---

## 8. 测试 & 验收

### 8.1 覆盖率目标

```
Unit:        ≥ 80%   (pytest --cov + npm test --coverage)
Integration: 100%    (核心 API 全部覆盖)
E2E:         3~4 条主链
```

不在文档里固定测试数量，避免未来重构导致数量失效。

### 8.2 Unit Tests

**ExplainService 单测**：
- `_cache_key` 不含 provider/model（切换 provider 命中相同 cache）
- `_cache_key` 不含 system/user（prompt 模板版本切换不破坏 cache key）
- `_cache_key` 含 scene/node_id/sentence/student_level/language
- `_parse_response` 合法 JSON → ExplainResponseModel
- `_parse_response` 非法 JSON → fallback
- `_parse_response` 部分字段缺失 → 用默认值
- `_build_system` 拼接 BASE + SCENE + NODE
- `_build_system` 拒绝未知 scene/node_type
- `fallback_for` 永远返回非空 ExplainResult
- `fallback_for` 未知 scene → GENERIC fallback
- `explain` 命中 cache → `source=cached`，不调 gateway
- `explain` gateway 抛 InferenceError → fallback
- `explain` 超时 → fallback
- `explain` 返回空字符串 → fallback
- `explain` 返回 unicode 截断 → fallback

**Provider 单测**：
- `OllamaProvider.is_available` 健康 → True
- `OllamaProvider.is_available` 连接拒绝 → False（3s 超时）
- `OllamaProvider.generate` mock HTTP 返回 → 解析
- `CloudProvider` OpenAI 路径 mock SDK
- `CloudProvider` Anthropic 路径 mock SDK
- `CloudProvider` 无 api_key → init 失败
- `provider_factory` 优先级: cloud 有 key → cloud
- `provider_factory` cloud 无 key + ollama ok → ollama
- `provider_factory` 都不可 → NullProvider
- `NullProvider.generate` 返回空字符串
- `NullProvider.health_check` → `{ok: false}`
- tenacity 重试：第一次失败第二次成功

**Prompt Template 单测**：
- 4 个 NodeType × 3 个 Scene 模板都存在
- 模板渲染不报 KeyError
- 模板不含整棵 tree 引用（grep 验证）
- 模板 BASE 永远包含"严禁重新解析"约束
- 模板输出格式要求包含全部 6 个字段名
- node_type 命名一致（无 vp/verb_phrase 漂移）
- 模板 prompt_version 字段存在

**Frontend 单测**：
- `ExplainPanel` 渲染 empty / loading skeleton / ready / degraded 四种状态
- AbortController：快速切换 selection 只保留最新响应
- Pin toggle：pin 后 selection 变化不触发请求
- History Drawer：item 点击恢复 result，不发新请求
- History 超过 30 条 → LRU 淘汰
- Source badge 三种状态映射
- Degraded banner 仅 `degraded=true` 时显示
- Skeleton 在 loading 时显示，无空 box
- Markdown 渲染（list/code/heading）正确
- 健康指示灯 dot 颜色映射
- Sticky 定位（CSS 检查 `position: sticky`）

### 8.3 Integration Tests

`backend/tests/integration/test_m4_api.py`：

- `POST /api/explain` 合法 ctx → 200 + ok + result
- `POST /api/explain` provider crash → 200 + degraded + fallback
- `POST /api/explain` 非法 JSON 输出 → 200 + degraded + fallback
- `POST /api/explain` 超时 → 200 + degraded + fallback
- `POST /api/explain` spaCy model 未加载 → **200 + degraded**（不返回 503）
- `POST /api/explain` ExplainContext 缺 selected_node_id → 200 + degraded + GENERIC fallback
- `GET /api/explain/health` ollama 在线 → available=true
- `GET /api/explain/health` ollama 离线 → available=false
- `GET /api/explain/health` cloud 无 key → provider=fallback, available=false
- IPC `explain-node` 透传到后端
- IPC `explain-node` 后端挂掉 → 返回内置 fallback（不传 error）
- IPC `explain-health` 缓存结果 5 分钟

### 8.4 E2E Tests (Playwright + Electron)

**Case A — 正常路径**：
启动 → 输入句子 → 三场景自动分析 → Timeline 点 verb → ExplainPanel 显示 🧠 AI → Markdown 正确

**Case B — 降级路径**：
杀掉 Ollama → 启动 → 同样操作 → ExplainPanel 显示 📘 Rule + amber banner → 不报错、不白屏

**Case C — Pin + History**：
点节点 A → 📌 Pin → 切到节点 B → 解释保持 A → 🕘 History → 看到 A 和 B → 点 A → 恢复 A

**Case D — 快速切换**：
50ms 内连续点 5 个不同节点 → 等待 1s → 断言：ExplainPanel 显示最后点击的节点（node5）→ 无 stale 响应覆盖 → History 5 条都在

### 8.5 Prompt Snapshot Tests

```
backend/tests/prompts/
  __init__.py
  test_base_prompt.py
  test_scene_prompts.py
  test_node_prompts.py
  test_full_assembly.py
  snapshots/
    base_prompt_v1.txt
    scene_timeline_v1.txt
    scene_anatomy_v1.txt
    scene_expansion_v1.txt
    node_tense_v1.txt
    node_phrase_v1.txt
    node_template_v1.txt
    node_validation_warning_v1.txt
```

```python
def test_base_prompt_contains_no_reparse_constraint():
    assert "严禁重新解析" in BASE_PROMPT
    assert "严禁修改引擎结果" in BASE_PROMPT

def test_base_prompt_snapshot():
    assert BASE_PROMPT == read_snapshot("base_prompt_v1.txt")

def test_node_template_prompt_contains_tips_field():
    for node_type in NodeType:
        assert "tips" in NODE_PROMPTS[node_type] or "Tips" in NODE_PROMPTS[node_type]
```

**意图**：prompt 是 AI 项目的"产品决策契约"，改 prompt 跟改 schema 一样慎重，snapshot 锁住。

### 8.6 验收清单

**功能验收**：
- [ ] `/api/explain` 任何情况下都返回 HTTP 200
- [ ] 三个场景的节点都能触发 ExplainContext
- [ ] Pin 后切换 selection 不重置
- [ ] History Drawer 至少 20 条记录
- [ ] Skeleton 加载无空 box
- [ ] Degraded 状态下 ExplainPanel 仍可读
- [ ] 健康指示灯四色正确
- [ ] Markdown 列表/代码/标题渲染正常
- [ ] AbortController + request_id：快速连点 5 次，最终显示最后点击

**架构验收**：
- [ ] 三个 scene 组件不 import 任何 Explain 相关代码（grep 验证）
- [ ] `ExplainService` 不接触 phrase tree（grep `engine_result` 在 prompt 模板中不出现整树引用）
- [ ] Provider 切换零代码改动（改 `config.json` 即可）
- [ ] Cache key 不含 provider/model（grep `sha256` 输入验证）
- [ ] InferenceGateway 单一入口（M5 复用接口已就绪）

**性能验收**：
- [ ] 首次 explain 请求 < 5s（Ollama 本地）/ < 8s（cloud）
- [ ] 缓存命中 < 50ms
- [ ] Explain 加载不阻塞场景渲染
- [ ] Pin 切换 < 100ms

**降级验收**：
- [ ] Ollama 离线 → fallback，无白屏
- [ ] Ollama 在线但模型未拉 → ERROR 状态 + 提示 `ollama pull`
- [ ] Cloud API key 失效 → fallback
- [ ] 网络断开 → IPC 层 fallback
- [ ] 后端完全挂掉 → 前端内置 fallback
- [ ] spaCy model 未加载 → API 200 + fallback（不返回 503）

---

## 9. 依赖与配置

### 9.1 后端依赖（新增）

`backend/requirements.txt`：

```
# Inference
ollama>=0.4.0
openai>=1.50.0
httpx>=0.27.0
tenacity>=9.0.0
cachetools>=5.5.0

# 已有
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
spacy==3.8.2
en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
benepar==0.2.0
```

### 9.2 前端依赖（新增）

`package.json`：

```json
{
  "dependencies": {
    "zustand": "^5.0.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0"
  }
}
```

### 9.3 配置文件

`backend/ai/config.json`：

```json
{
  "default_provider": "auto",
  "ollama": {
    "base_url": "http://127.0.0.1:11434",
    "model": "llama3.1:8b"
  },
  "cloud": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key_env": "AI_CLOUD_API_KEY"
  },
  "cache": {
    "ttl_seconds": 86400,
    "max_entries": 500
  },
  "timeout_seconds": 30
}
```

---

## 10. Milestone 拆分

- **M4a — 后端骨架 (Day 1-2)**
  - Provider 抽象 + Ollama/Cloud/Null 实现
  - InferenceGateway
  - Fallback 硬编码库
  - Unit tests ≥ 80%

- **M4b — ExplainService + API (Day 3-4)**
  - Prompt 三层模板（BASE + SCENE + NODE）
  - Pydantic 解析
  - cachetools.TTLCache
  - `/api/explain` + `/api/explain/health` 端点
  - 永远 HTTP 200 兜底
  - Integration tests 100% 核心 API

- **M4c — 前端 ExplainPanel (Day 5-6)**
  - ExplainPanel 组件
  - AbortController + request_id 双保险
  - Pin + History Drawer
  - Skeleton + Source Badge + Degraded Banner
  - SelectionEvent + ExplainContextBuilder
  - Zustand + persist
  - Frontend unit tests

- **M4d — 集成 + E2E (Day 7)**
  - App.tsx 接入（Header 健康灯 + ExplainPanel 布局）
  - IPC `explain-node` + `explain-health`
  - 三个 Scene 接入（emit SelectionEvent）
  - Prompt Snapshot Tests
  - E2E Case A/B/C/D
  - 验收清单逐条对照

---

## 11. 不在 M4 范围内（明确划线）

- ❌ 流式响应（SSE）— M5
- ❌ M5 Shadow-Mode 改写 — M5
- ❌ M6 Chat 助手 — M6
- ❌ //Gemma 实现 — stub 即可
- ❌ 多语言切换 UI — 默认 zh，env 配置改
- ❌ 用户反馈"这条解释不对" — 留到 M5+
- ❌ 解释的 A/B 测试 — 留到 M5+

---

## 12. 附录

### 12.1 命名约定

| 概念 | 命名 | 禁止 |
|---|---|---|
| NodeType 短语 | `phrase` | `vp` / `verb_phrase` / `phrase_vp` |
| 场景 | `timeline` / `anatomy` / `expansion` | `scene1` / `tab2` |
| Source | `ai` / `cache` / `fallback` | `llm` / `cached` / `default` |
| Provider | `ollama` / `openai` / `anthropic` / `fallback` | `local` / `cloud` |

### 12.2 关键文件清单

新增：
- `backend/ai/__init__.py`
- `backend/ai/inference/__init__.py`
- `backend/ai/inference/inference_gateway.py`
- `backend/ai/inference/provider_factory.py`
- `backend/ai/inference/providers/__init__.py`
- `backend/ai/inference/providers/provider_base.py`
- `backend/ai/inference/providers/ollama_provider.py`
- `backend/ai/inference/providers/cloud_provider.py`
- `backend/ai/inference/providers/` (M5+ stub placeholder)
- `backend/ai/inference/providers/gemma_provider.py` (M5+ stub)
- `backend/ai/explain/__init__.py`
- `backend/ai/explain/explain_service.py`
- `backend/ai/explain/prompt_templates.py`
- `backend/ai/explain/explain_cache.py`
- `backend/ai/explain/fallback_explanations.py`
- `backend/ai/config.json`
- `src/renderer/components/explain/ExplainPanel.tsx`
- `src/renderer/components/explain/ExplainContextBuilder.ts`
- `src/renderer/components/explain/ExplainHistoryDrawer.tsx`
- `src/renderer/components/explain/ExplainSkeleton.tsx`
- `src/renderer/components/explain/SourceBadge.tsx`
- `src/renderer/components/explain/DegradedBanner.tsx`
- `src/renderer/stores/explainStore.ts`
- `src/renderer/types/selection.ts`
- `backend/tests/test_m4_explain_service.py`
- `backend/tests/test_m4_providers.py`
- `backend/tests/test_m4_prompt_templates.py`
- `backend/tests/integration/test_m4_api.py`
- `backend/tests/prompts/snapshots/*.txt`
- `src/renderer/components/explain/__tests__/*.test.tsx`

修改：
- `backend/app.py` — 新增 2 个端点
- `backend/requirements.txt` — 新增依赖
- `package.json` — 新增 zustand / react-markdown
- `src/main/ipc/index.ts` — 新增 2 个 handler
- `src/preload/index.ts` — 新增 2 个 API
- `src/renderer/App.tsx` — 接入 ExplainPanel
- `src/renderer/components/timeline/TimelineScene.tsx` — emit SelectionEvent
- `src/renderer/components/anatomy/AnatomyScene.tsx` — emit SelectionEvent
- `src/renderer/components/expand/ExpandScene.tsx` — emit SelectionEvent

### 12.3 风险与缓解

| 风险 | 缓解 |
|---|---|
| Ollama 启动慢 | 异步加载，UI 不阻塞 |
| Cloud API 费用 | 默认本地，cloud 需明确配置 |
| LLM 输出不合法 JSON | Pydantic 解析失败 → fallback |
| Provider 切换影响 cache | cache key 不含 provider/model |
| Prompt 模板漂移 | Snapshot Test 锁住 |
| 三个 Scene 耦合 Explain | SelectionEvent + Builder 隔离 |
| 快速点击产生 stale 响应 | AbortController + request_id 双保险 |
| AI 不可用时体验断裂 | 永远 fallback，UI 永远有内容 |
