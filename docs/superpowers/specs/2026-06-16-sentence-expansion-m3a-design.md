# M3a — Sentence Expansion 句扩展:Grammar Engine 基础 + Level 1 词级

> 设计稿日期:2026-06-16
> 状态:已确认(用户 2026-06-16 确认 4 修正 + 1 新增,见 §9),进入实施
> 关联规范:用户提供的《Sentence Expansion 模块设计规范》(2026-06-16)

---

## 1. 背景与目标

Grammar Lab 的 M0/M1/M2 已经交付"看现状"——M1 时间轴、M2 句剖析,都是从已有句子反推结构。M3 是"看怎么来的",教学生英语句子如何从核心一步步生长成复杂句。

按用户设计规范,M3 的核心形态是**句子乐高(Building Blocks)**:学生从简单句开始,主动选择要扩展的成分(如给 `dogs` 加形容词),系统按规则库推荐扩展项,提交后由 Validator 验证语法正确性。

M3a 只交付**最小可验证的 Engine + 只读 UI 骨架**,不交付完整 L1 提交闭环。

### 1.1 M3a 范围(明确不做什么)

✅ **做**:
- 后端:Grammar Engine 四个模块(规则库/模板/Validator/主入口)
- 后端:单元测试覆盖规则库查询、模板填充、Validator 主谓一致、严禁项
- 后端:`/api/expansion/analyze` 端点
- 前端:三栏布局(扩展类型库占位 / 句子画布 / **静态扩展可能树**)
- 前端:句子画布渲染**所有非标点 token**,可扩展节点高亮,不可扩展灰显;每节点带 [+] 弹候选菜单(只读)
- 前端:右栏 **Expansion Tree**——对当前句子,以树状结构展示每个成分能往哪些方向扩展(静态,不依赖学生操作)
- 前端:IPC handler + preload 暴露 + types 扩展
- 端到端:`curl /api/expansion/analyze` + `pytest` + 人工在 Electron 窗口看 UI 渲染

❌ **不做**(明确划线,留给 M3a+1 / M3b / M3c):
- 选词提交(用户选 adj 模板 → 提交 → 后端验证 → 前端高亮新词)——M3a+1
- 新增成分的视觉高亮(画布上新增词的高亮)、节点间连线修饰关系——M3a+1。注意:这与右栏 Expansion Tree 不同,Tree 是静态结构展示,不是"已加成分的连线"
- Level 2 短语扩展(prep/participle/infinitive phrase)——M3b
- Level 3 从句扩展(relative/adverbial/noun clause)+ 关系代词匹配——M3c
- Validator 完整 5 项实现(只交付主谓一致的实现+测试,其他 4 项**函数签名齐但返回 PASS 占位**)——M3b/c
- AI 集成(规范第 11 节允许 AI 填模板,M3a 不引入)——M4

### 1.2 为什么这样切

M2 的经验:`backend` 和 `electron-vite` 全链路构建零错误,但前端交互在 Electron 窗口里有两个隐性 bug(选中不响应 / 标点误判锁死)——都是 M2 主 PR 合入 2 天后人工才暴露。M3 范围比 M2 大一倍以上,一次性交付风险更高。

按规范第 8 节「扩展层级」,**Level 1 → 2 → 3 是天然切分**。M3a = Level 1 的 Engine + 读路径,Level 1 的写路径(M3a+1)紧跟其后。

---

## 2. Grammar Engine 设计

### 2.0 架构原则与长期演进(Chief Architect 视角)

Grammar Engine 的长期架构遵循 10 条核心原则(用户 2026-06-16 设计建议):

1. **Never expand tokens directly** — 扩展单位是短语(NP/VP/PP/Clause),不是单个 token
2. **Expand phrases only** — Phase 1 的"加形容词"操作对象是 NP,不是 NOUN token
3. **Maintain an Expansion Tree** — 父子关系的扩展树
4. **Maintain Parent-Child relationships** — 每次扩展产生子节点,挂到父短语下
5. **Maintain Modifier Scope Rules** — 修饰语的管辖域(形容词管哪个名词,副词管哪个动词)
6. **Maintain Feature Slots** — 特征槽(person/number/gender/tense/case)
7. **Maintain Tense State** — 句子的时态状态机,扩展动词时必须保持一致
8. **Maintain Expansion Depth Limits** — 防止无限嵌套(规范严禁项 #7)
9. **Validate every expansion before rendering** — 渲染前必验证
10. **Grammar correctness relies on Rule Engine + Validator, not LLM** — LLM 只做教学解释

**目标工具链 pipeline(长期)**:
```
spaCy → Benepar → Grammar Engine → Validator → LanguageTool → UI
```
- `spaCy`:依存分析(已有)
- `Benepar`:Berkeley 成分句法分析,产出 NP/VP/PP/Clause 嵌套树(原则 #1/#2 的基础)
- `Grammar Engine`:维护 Expansion Tree + Node Graph + Feature Slots + Tense State
- `Validator`:5 项规则校验(主谓一致/时态一致/从句完整/非谓语/关系代词)
- `LanguageTool`:外部全句语法兜底校验(Java 服务)

**M3a 的位置**:M3a 是 Phase 1(word-level)的**只读骨架**。原则 #1/#2 要求 phrase-level 数据模型——**M3a 现在就采用 phrase-level 数据模型**(用 spaCy 的 `noun_chunks` + `dep_` 拼短语边界作过渡),但**暂不装 Benepar / LanguageTool**(见 §2.1)。

### 2.1 模块边界

```
backend/grammar_engine/
├── expansion_rules.py       # 规则库:短语类型 → 可扩展项
├── expansion_templates.py   # 模板:L1 模板实例(形容词/副词/数词词表)
├── expansion_validator.py   # 验证器:5 项规则(主谓一致有实现,其他占位)
├── expansion_engine.py      # 主入口:spaCy → 短语识别 → orchestrate 上面三个
├── phrase_segmenter.py      # [新增] 短语识别:spaCy noun_chunks + dep_ 拼 NP/VP/PP 边界
└── models.py                # (扩展) phrase-level Pydantic 模型
```

**模块依赖**:`engine → phrase_segmenter + rules + templates + validator → spaCy(nlp_loader)`。

**Benepar / LanguageTool 的引入计划(不在 M3a,写入路线图)**:
- **M3b(Phase 2 短语扩展)**:装 Benepar(`pip install benepar` + 下载 `benepar_en` 模型),`phrase_segmenter.py` 从"spaCy 拼接"升级为"Benepar 成分树"。M3a 的 `phrase_segmenter` 接口保持不变,只换实现——这是为平滑升级预留的接缝。
- **M3c(Phase 3 从句扩展)**:装 LanguageTool(本地 Java 服务 + `language-tool-python` 包装),作为 Validator 的第 6 道外部校验。Validator 接口不变,加一个 `validate_with_languagetool` 可选步骤。

### 2.2 短语识别 (`phrase_segmenter.py`) [新增]

**职责**:把句子切成短语节点(NP/VP/PP/Clause),每个短语带特征槽 + **Parent-Child 挂载关系**。**这是原则 #1/#2/#6 的代码化**——扩展单位是短语,不是 token;且为原则 #3/#4/#5 的后续(Expansion Tree/父子/修饰域)预留数据结构。

**设计目标**:M3a 保证**数据模型稳定**,为 M3b(Benepar)/ M3c(LanguageTool)预留接缝,**不追求句法分析精度**。

```python
PhraseType = Literal["NP", "VP", "PP", "ADJP", "ADVP", "CLAUSE", "OTHER"]

@dataclass
class PhraseNode:
    id: str                     # "p0" / "p1" ...
    type: PhraseType            # "NP" / "VP" / "PP" ...
    text: str                   # "the dogs" / "has been working" / "in the park"
    head_token_text: str        # 中心词:"dogs" / "working" / "park"
    head_pos: str               # 中心词 POS:"NOUN" / "VERB" / "NOUN"
    syntactic_role: str         # "subject" / "predicate" / "object" / "adverbial" / "other"
    span: tuple[int, int]       # 字符位置
    # 特征槽(Feature Slots,原则 #6)—— M3a 仅 NP/VP 填充
    features: dict              # NP: {"number": "plural", "person": 3}
                                # VP: {"tense": "present_perfect_progressive", "modal": None,
                                #       "aux_chain": ["has", "been"], "aspect": "progressive"}
    # Parent-Child 挂载(调整 1,为原则 #3/#4/#5 预留)——M3a 建立内部挂载,右栏不显示
    parent_id: Optional[str]    # None = 顶层;否则指向父短语 id
    children_ids: list[str]     # 子短语 id 列表(M3a 多为空,PP 挂 NP/VP 时填)
    is_expandable: bool         # 该短语是否有 L1 可扩展项
    candidates: list            # 仅 is_expandable=True 时非空

def segment(doc) -> list[PhraseNode]:
    """M3a 短语识别(过渡实现,无 Benepar)。

    返回扁平 list[PhraseNode],但每个节点内部已具备 parent_id/children_ids,
    可重建树结构(调整 1:即使 M3a 不显示关系树,也必须建立内部挂载)。

    流程:
    1. **NP**:doc.noun_chunks → NP(text/span/head/number/person 特征)
    2. **VP 完整时态链**(调整 2):从每个 main verb(VERB pos)向前回溯,
       吞掉连续的 auxiliaries(has/be/do)+ modal(would/can/must...)+
       main verb + particles(up/off/out...,带 prt dep_)→ 合成一个 VP span。
       - `has been working` → 一个 VP(features.tense=present_perfect_progressive)
       - `would like` → 一个 VP(features.modal="would")
       - `to help` → **不纳入 VP**,留给 M3b 的 infinitive phrase
    3. **PP**:介词(IN pos,pobj 关系)引导的 chunk → PP。
       挂载规则(调整 1 简化版):
       - PP 紧跟 NP(右侧相邻)→ parent_id = 该 NP
       - PP 紧跟 VP(右侧相邻)→ parent_id = 该 VP
       - 否则 PP 顶层漂浮(parent_id=None)
       例:`likes the dog in the park` → NP(dog) ← PP(in the park);
       即 PP 挂到 dog 而非漂浮,保留 `[the dog in the park]` 教学结构。
    4. 其余 token(冠词已被 noun_chunks 吞入 NP / 连词 / 标点)不单独成节点。

    M3b 升级:函数体改用 Benepar 成分树,parent_id/children_ids 直接来自
    Benepar 的嵌套结构,无需改数据模型。
    """
```

**关键决策**:
- **数据模型稳定优先于精度**(调整精神):M3a 的 `PhraseNode` 字段集(parent_id/children_ids/features/tense 链)设计为 M3b/M3c 不需扩展��能承载 Benepar 和 LanguageTool 的输出。M3b 只换 `segment()` 函数体。
- **VP 必须完整吞时态链**(调整 2):`has been working` 不可切成 `working`。VP.features 含 `aux_chain`/`modal`/`aspect`/`tense`,Validator 主谓一致和后续时态扩展都依赖它。`to help` 暂不纳入(留给 M3b infinitive phrase)。
- **PP 挂载消除漂浮**(调整 1):`in the park` 必须挂到 `the dog`(宾语 NP)而非顶层漂浮,否则修饰关系丢失、Expansion Tree 无处挂载、后续 relative clause/PP/participle 扩展失锚。M3a 用简化规则(PP 跟 NP 挂 NP,跟 VP 挂 VP),M3b 用 Benepar 精确挂载。
- **右栏不显示 Parent-Child 关系**(M3a):内部挂载是为数据完整性,右栏 M3a 仍是"短语结构图"(扁平短语序列,见 §4.2)。挂载关系等到 M3a+1 提交闭环或 M3b 才可视化。
- **特征槽是原则 #6 的体现**——NP 带 number/person,VP 带 tense/modal/aux_chain。M3a Validator 主谓一致读 `NP.features["number"]` 和 `VP` 的时态,不重新分析。
- **接口隔离,M3b 可换实现**:`segment(doc)` 返回契约固定,M3b 装 Benepar 后只换函数体。

### 2.3 规则库 (`expansion_rules.py`)

**职责**:给定一个**短语的类型 + 中心词 POS**,返回可扩展项列表。**注意:查询键从"token POS"改为"短语类型"**(原则 #1/#2 的直接后果)。

```python
ExpansionKind = Literal[
    # Level 1: 词级(作用于短语的特征槽)
    "adjective",          # → NP 前置形容词(NP.features 加 adj 修饰)
    "adverb",             # → VP/ADJP 前置副词
    "number",             # → NP 前置数词
    "degree_adverb",      # → ADJP/ADVP 前置程度副词
    # Level 2: 短语级
    "prepositional_phrase",
    "participle_phrase",
    "infinitive_phrase",
    # Level 3: 从句级
    "relative_clause",
    "adverbial_clause",
    "noun_clause",
]

# 规则来源(键是 PhraseType,不是 token POS)
NP_RULES:  list[ExpansionKind] = ["adjective", "number", "prepositional_phrase",
                                   "participle_phrase", "relative_clause"]
VP_RULES:  list[ExpansionKind] = ["adverb", "adverbial_clause"]
ADJP_RULES: list[ExpansionKind] = ["degree_adverb", "infinitive_complement"]
ADVP_RULES: list[ExpansionKind] = ["degree_adverb"]

# 查询(纯函数)
def get_rules_for_phrase(phrase_type: PhraseType, head_pos: str) -> list[ExpansionKind]: ...
def get_kind_metadata(kind: ExpansionKind) -> dict: ...  # label_cn / level / available
```

**关键决策**:
- **查询键是短语类型**——`NP_RULES` 不是 `NOUN_RULES`。给 NP 加形容词,不是给 NOUN token 加。这从根上贯彻原则 #1/#2。
- **M3a 只实现 L1 规则查询**(NP→adjective/number,VP→adverb,ADJP→degree_adverb)。L2/L3 在数据中预声明但 `available=False`,前端显示"未开放"。
- **`head_pos` 作为次要键**:同为 NP,"the dogs"(head NOUN)可加形容词,"the running dogs"(head 也是 NOUN,但有分词修饰)依然可加——head_pos 用于区分细类,M3a 暂不深入。

### 2.4 模板库 (`expansion_templates.py`)

**职责**:为每个 ExpansionKind 提供填充实例。**规范第 12 节「模板优先」**——禁止 AI 从零生成。

```python
@dataclass(frozen=True)
class Template:
    kind: ExpansionKind
    template_id: str
    surface: str               # "cute" / "three" / "really"
    pos_tag: str               # "ADJ" / "NUM" / "ADV"
    semantic_class: str        # "appearance" / "cardinal" / "degree"
    example_anchor: str        # 模板预览锚:"dogs"(NP)/ "like"(VP)

# L1 模板集(20 个,用户确认"完全够")
L1_TEMPLATES: dict[ExpansionKind, list[Template]] = {
    "adjective": [  # 7 个,锚=NP 中心词如 dogs
        Template("adjective", "tpl_adj_cute", "cute", "ADJ", "appearance", "dogs"),
        Template("adjective", "tpl_adj_black", "black", "ADJ", "color", "dogs"),
        Template("adjective", "tpl_adj_small", "small", "ADJ", "size", "dogs"),
        Template("adjective", "tpl_adj_big", "big", "ADJ", "size", "dogs"),
        Template("adjective", "tpl_adj_friendly", "friendly", "ADJ", "temperament", "dogs"),
        Template("adjective", "tpl_adj_noisy", "noisy", "ADJ", "behavior", "dogs"),
        Template("adjective", "tpl_adj_loyal", "loyal", "ADJ", "temperament", "dogs"),
    ],
    "adverb": [  # 6 个,锚=VP 中心词如 like/runs
        Template("adverb", "tpl_adv_really", "really", "ADV", "degree", "like"),
        Template("adverb", "tpl_adv_always", "always", "ADV", "frequency", "like"),
        Template("adverb", "tpl_adv_never", "never", "ADV", "frequency", "like"),
        Template("adverb", "tpl_adv_quickly", "quickly", "ADV", "manner", "runs"),
        Template("adverb", "tpl_adv_slowly", "slowly", "ADV", "manner", "runs"),
        Template("adverb", "tpl_adv_carefully", "carefully", "ADV", "manner", "drives"),
    ],
    "number": [  # 4 个,锚=NP
        Template("number", "tpl_num_two", "two", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_three", "three", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_five", "five", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_many", "many", "DET", "quantifier", "dogs"),
    ],
    "degree_adverb": [  # 3 个,锚=ADJP 中心词如 cute
        Template("degree_adverb", "tpl_adv_very", "very", "ADV", "intensifier", "cute"),
        Template("degree_adverb", "tpl_adv_extremely", "extremely", "ADV", "intensifier", "cute"),
        Template("degree_adverb", "tpl_adv_quite", "quite", "ADV", "moderator", "cute"),
    ],
    # L2/L3 预声明无模板
    "prepositional_phrase": [], "participle_phrase": [], "infinitive_phrase": [],
    "relative_clause": [], "adverbial_clause": [], "noun_clause": [],
}

def get_templates_for_kind(kind: ExpansionKind) -> list[Template]: ...
def get_template_by_id(template_id: str) -> Template | None: ...
```

**关键决策**:
- **模板的 `example_anchor` 现在锚到短语中心词**(dogs/like/cute),与 §2.2 的 PhraseNode.head_token_text 对齐。预览拼成 `"cute dogs"`(给 NP 加形容词)、`"really like"`(给 VP 加副词)。
- **adj/number 严格分桶**(原 spec 决策保留):`three` 只在 number 集,不在 adjective 集。

### 2.5 Validator (`expansion_validator.py`)

**职责**:渲染前验证语法正确性。**规范第 6 节 5 项**;M3a 实现主谓一致(有实现+测试),其他 4 项签名齐+返回 PASS(为 M3b/c 预留)。**注意:主谓一致现在直接读短语特征槽,不重新分析**。

```python
@dataclass
class ValidationReport:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    auto_corrections: list[dict]  # [{"from": "like", "to": "likes", "reason": "主谓一致"}]

def validate(sentence: str, doc, phrases: list[PhraseNode]) -> ValidationReport:
    """5 项检查统一入口。M3a: 第 1 项实现,2-5 占位。phrases 是 §2.2 的输出。"""
    reports = [
        validate_subject_verb_agreement(sentence, doc, phrases),  # M3a 实现
        validate_tense_consistency(sentence, doc, phrases),       # M3b 占位
        validate_clause_completeness(sentence, doc, phrases),     # M3c 占位
        validate_non_finite_legality(sentence, doc, phrases),     # M3c 占位
        validate_relative_pronoun_match(sentence, doc, phrases),  # M3c 占位
    ]
    return merge_reports(reports)

def validate_subject_verb_agreement(sentence, doc, phrases) -> ValidationReport:
    """M3a 唯一实现。读短语特征槽(原则 #6):
    - 找 subject NP( syntactic_role=="subject")和 predicate VP
    - 若 VP.features["tense"]=="simple_present"
      且 NP.features["number"]=="singular" 且 person==3
      且 VP 中心词未带 -s 词尾
    → auto-correction {from: VP.head, to: VP.head+"s"}
    比 token 级判定更稳:不依赖 dep_ 找主语(M2 教训),直接读 NP 的 syntactic_role。
    """

def validate_tense_consistency(sentence, doc, phrases) -> ValidationReport:
    return ValidationReport(True, [], [], [])  # M3b 占位
def validate_clause_completeness(sentence, doc, phrases) -> ValidationReport:
    return ValidationReport(True, [], [], [])  # M3c 占位
def validate_non_finite_legality(sentence, doc, phrases) -> ValidationReport:
    return ValidationReport(True, [], [], [])  # M3c 占位
def validate_relative_pronoun_match(sentence, doc, phrases) -> ValidationReport:
    return ValidationReport(True, [], [], [])  # M3c 占位
```

**关键决策**:
- **Validator 现在接收 `phrases`**——直接读特征槽,不重新做句法分析。这是 phrase-level 模型的红利:主谓一致检查从"在 token 序列里找主语谓语"变成"读 subject NP 和 predicate VP 的特征"。
- **M3a 不接 UI 提交闭环**——Validator 只被单测调用,不在 IPC 路径(原决策保留)。
- **Auto-correction 是教学点**(原决策保留)。

### 2.6 主入口 (`expansion_engine.py`)

**职责**:spaCy → phrase_segmenter → orchestrate rules/templates → 产出**短语节点 + 候选菜单**。

```python
def analyze(sentence: str) -> dict:
    """M3a 唯一对外函数。流程:
    1. nlp(sentence) → doc
    2. phrase_segmenter.segment(doc) → list[PhraseNode](含特征槽,§2.2)
    3. 对每个短语调 rules.get_rules_for_phrase(node.type, node.head_pos):
       - 命中 → is_expandable=True,填 candidates
       - 不命中 → is_expandable=False,candidates=[]
    4. 对命中的 kind 调 templates.get_templates_for_kind(kind) → 模板预览
    5. 返回 {sentence, phrases, warnings}
    """
```

**关键决策**:
- **响应字段从 `nodes` 改为 `phrases`**——Pydantic 模型同步改名(§2.7)。
- **spaCy 不可用降级**:返回 `warnings=["spaCy model unavailable"]` + 空 phrases(原决策保留)。

### 2.7 Pydantic 模型(`models.py` 追加)

```python
class PhraseTypeInfo(BaseModel):
    type: str                   # "NP" / "VP" / ...
    label_cn: str               # "名词短语" / "动词短语"

class ExpansionKindInfo(BaseModel):
    kind: str
    label_cn: str
    level: int
    available: bool

class ExpansionTemplateInfo(BaseModel):
    template_id: str
    surface: str
    preview: str                # "cute dogs"
    semantic_class: str

class ExpansionCandidate(BaseModel):
    kind: str
    kind_label_cn: str
    level: int
    available: bool
    templates: list[ExpansionTemplateInfo]

class PhraseNodeInfo(BaseModel):
    id: str
    type: str                   # "NP" / "VP" / "PP" ...
    text: str                   # "the dogs" / "has been working"
    head_token_text: str        # "dogs"
    head_pos: str
    syntactic_role: str
    span: tuple[int, int]
    features: dict              # 特征槽(NP: number/person;VP: tense/modal/aux_chain/aspect)
    parent_id: Optional[str]    # 调整 1:Parent-Child 挂载,None=顶层
    children_ids: list[str]     # 调整 1:子短语 id 列表
    is_expandable: bool
    candidates: list[ExpansionCandidate]

class ExpansionAnalyzeResponse(BaseModel):
    sentence: str
    phrases: list[PhraseNodeInfo]   # 注意:phrases 不是 nodes
    warnings: list[str] = []
```

---

## 3. API 端点(`app.py` 追加)

```python
@app.post("/api/expansion/analyze", response_model=ExpansionAnalyzeResponse)
async def analyze_expansion(request: AnalyzeRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    from grammar_engine.expansion_engine import analyze as expansion_analyze
    result = expansion_analyze(request.sentence)
    return ExpansionAnalyzeResponse(**result)
```

**M3a 不实现**:`/api/expansion/apply`(提交扩展)、`/api/expansion/validate`(独立验证端点)。这两个留给 M3a+1。

---

## 4. 前端实现

### 4.1 IPC 链路(沿用 M2 模式)

- `src/main/ipc/index.ts`:加 `analyze-sentence-expansion` handler,fetch `POST /api/expansion/analyze`,模板与 M2 的 `analyze-sentence-anatomy` 一字不差——**复制粘贴可以,后面要重构时再说**(spec 末尾"已知问题"会记录)。
- `src/preload/index.ts`:加 `analyzeExpansion: (s) => ipcRenderer.invoke('analyze-sentence-expansion', s)`,类型同步扩展 `ElectronAPI`。
- `src/renderer/types/index.ts`:在 `SentenceAnalysis` 上加 `expansion: { backend: ExpansionAnalyzeResponse }` 字段(参考 M2 的 `anatomy: { backend }` 模式,见 `appState.ts:118`)。
- `src/renderer/state/appState.ts`:加 `analyzeExpansion(sentence)` action,模式同 `analyzeAnatomy`(`appState.ts:87-125`),合并到 currentAnalysis。

### 4.2 三栏布局(`ExpandScene.tsx` 重写)

按规范第 5 节推荐布局:
```
┌──────────┬──────────────┬──────────┐
│ 扩展类型库│  句子画布    │ 短语结构图│
│ (占位)   │  + [+] 菜单  │ (静态)   │
└──────────┴──────────────┴──────────┘
```

- **左栏 `<ExtensionLibrary>`**:占位组件,显示"L1 已开放:adj/adv/num/degree"列表 + "L2 短语扩展:未开放"灰态。这一栏 M3a 仅展示,点击无反应(M3a+1 才接左侧面板的拖入式扩展)。
- **中栏 `<SentenceCanvas>`**:核心组件,渲染 Engine 给的 `phrases` 列表。每个短语是一张卡片:
  - 卡片显示短语 `text`(如 `the dogs`)+ 类型角标(NP/VP/PP)+ 特征槽缩写(3sg/pl/simple_present)
  - **`is_expandable=True`**:卡片描边高亮(蓝边 + 右上角绿点 ●),可点
  - **`is_expandable=False`**:卡片灰显(opacity-50),不可点——对比即教学
  - 可扩展卡片右上角 [+] 按钮
  - 点 [+] 弹 `<ExtensionMenu>` 浮层,列出 candidates(templates 网格)
  - **M3a 不做选词提交**:浮层上的"应用"按钮 disabled + tooltip "提交功能 M3a+1 开放"
- **右栏 `<ExpansionTree>`**:对当前句子,展示短语结构与扩展可能。**静态、只读、不依赖学生操作**——直接渲染 Engine 输出的 phrases+candidates。

  > **命名(调整 3)**:M3a 的显示名称是 **「短语结构图」(Phrase Structure Preview)**,**不叫**「成分句法树」。理由:M3a 尚未引入 Benepar,当前结构只是 spaCy 的 phrase grouping,不是真正的 Constituency Parse Tree。过度承诺会让用户误以为已完成成分句法分析、结果应与语言学教材一致。**M3b 引入 Benepar 后,再升级命名为「成分句法树」(Constituency Tree)。** 组件文件名 `ExpansionTree.tsx` 不变(承载内容随阶段演进),仅 UI 标题文案在 M3b 改。

  示例(M3a 短语结构图,扁平短语序列 + 每短语下的扩展候选):
  ```
  I like dogs.
        │
     ┌──┼───────┐
   NP(I)  VP(like)   NP(dogs)
   1sg    simple_    3pl
   (灰)   present   (高亮)
   (高亮)  (高亮)    │
          │       ┌───┬───────┐
       adverb   adj  number  relcl
     really/  cute/ two/   (L3未开放)
     always   black three
  ```
  - **根节点**:整句文本(`I like dogs.`)
  - **二层**:句中的**短语节点**(NP/VP/PP),按 spaCy 输出顺序排列。可扩展的高亮(NP/VP 蓝)、不可扩展的灰显(PP)。
    - 例:`I like dogs.` 的二层是 `NP(I)` / `VP(like)` / `NP(dogs)`
  - **三层**:每个可扩展短语下,按 candidate kind 分支;L2/L3 kind 标"未开放"灰态;L1 kind 下列前 2-3 个模板 surface 作叶子
  - **特征槽展示**:每个短语节点旁显示其 `features` 缩写(如 NP 旁标 `1sg`/`3pl`,VP 旁标 `simple_present`)——这是原则 #6 Feature Slots 的可视化,让学生看到"扩展时必须保持一致的特征"
  - **M3a 不显示 Parent-Child 嵌套**:虽然 phrase_segmenter 内部已建立 PP→NP 等挂载(§2.2 调整 1),但右栏 M3a 仍是扁平短语序列。嵌套关系等到 M3b(Benepar)或 M3a+1(提交闭环)才可视化。
  - **交互**:点树上的 kind 叶子 → 高亮中栏对应短语的 [+](M3a 仅视觉联动)
  - **数据来源**:与中栏画布**同一份** `phrases`,不重复请求

### 4.3 状态机

```
空态 ──[用户切到 expand 场景且有 sentence]──> loading
loading ──[API 成功]──> loaded(phrases)
loading ──[API 失败]──> error
loaded ──[用户点 [+] ]──> loaded + menuOpenFor=phraseId
menuOpenFor ──[点 X 或外部]──> loaded
```

**M3a 不做**:`applyExtension` action / undo 栈 / 提交后重画。`AnatomyScene.tsx:103-118` 的 undo/reset 模式**不在 M3a 范围**。

### 4.4 不在 M3a 做的 UI 决策

- **不做新增成分的连线修饰关系**——右栏短语结构图是"短语结构 + 扩展可能性"的静态展示,**不是**"已加修饰成分的关系连线"(原则 #5 Modifier Scope Rules 的动态维护)。后者(M3a+1 提交闭环)才需要追踪学生提交的扩展并更新修饰域。
- **不维护动态 Expansion Tree(原则 #3/#4)**——M3a 是只读,没有扩展动作,不产生父子扩展关系。原则 #3/#4 的完整实现要等 M3a+1 提交闭环。M3a 的右栏是**短语结构图**(句子本身的 NP/VP/PP 结构,扁平展示),**不是**扩展历史树,也**不是**成分句法树(M3b 才升级)。
- **不高亮"新增"成分**——M3a 没有"新增"概念(没有提交)。画布上的高亮只表示"该短语可扩展",不表示"刚被加进来"。
- **不做撤销/重做 / Depth 限制**(原则 #8)——M3a 没有"修改"概念,也没有嵌套深度问题。

---

## 5. 测试策略

### 5.1 后端单测 (`backend/tests/test_expansion_engine.py`)

**必须覆盖**(至少 11 项,编号含调整 1/2 新增的 VP 时态链与 PP 挂载):
1. **规则库完整性**:所有 L1 ExpansionKind 都在 `get_rules_for_phrase` 输出里(`NP`→含 `adjective`/`number`;`VP`→含 `adverb`;`ADJP`→含 `degree_adverb`)
2. **短语识别 - 基础**:`segment(doc("I like dogs."))` 返回 3 个短语:`NP(I)`(head=I, syntactic_role=subject, features={1sg})/ `VP(like)`(head=like, predicate, features={simple_present, modal=None})/ `NP(dogs)`(head=dogs, object, features={3pl})
3. **VP 完整时态链**(调整 2):
   - `segment(doc("He has been working hard."))` → VP.text 含 "has been working"(aux_chain=[has,been]),tense 含 perfect_progressive,**不是** 单独 "working"
   - `segment(doc("She would like to help."))` → VP.text=="would like"(modal="would"),`to help` 不在 VP 内(留 M3b infinitive phrase)
4. **PP 挂载**(调整 1):`segment(doc("likes the dog in the park"))` → PP(`in the park`)的 parent_id 指向 NP(`the dog`),**不是** None 漂浮;该 NP 的 children_ids 含该 PP
3. **模板填充**:`get_templates_for_kind("adjective")` 返回 7 个;每个 Template 的 `surface + example_anchor` 拼出的 preview 是合理短语
4. **Engine 入口**:`analyze("I like dogs.")` 返回:
   - 3 个 phrases(`NP(I)` / `VP(like)` / `NP(dogs)`)
   - `NP(dogs)` 的 `is_expandable=True`,2 个 candidates(`adjective` / `number`),各带模板
   - `VP(like)` 的 `is_expandable=True`,1 个 candidate(`adverb`)
   - `NP(I)` 的 `is_expandable=False`(代词作 NP,L1 不扩展),candidates=[]
5. **Validator 主谓一致**(读短语特征槽):
   - `He like dogs.` → invalid,`auto_corrections` 含 `{from:"like", to:"likes"}`(读到 subject NP `He` features={3sg},predicate VP `like` 无 -s)
   - `I like dogs.` → valid(subject NP `I` features={1sg},不触发)
   - `They like dogs.` → valid(NP `They` features={3pl},不触发)
   - `She has been running.` → valid(VP tense 非 simple_present,不触发)
6. **Validator 占位接口齐全**:`validate_tense_consistency` / `validate_clause_completeness` / `validate_non_finite_legality` / `validate_relative_pronoun_match` 四函数可调用且返回 `is_valid=True`(M3b/c 填实现)
7. **严禁项回归**:`analyze("I beautiful like dogs.")` → 短语识别不应把 `beautiful` 当作 VP 的合法扩展(规范严禁项 #1:"动词前添加形容词")。M3a 该句的 VP 是 `like`,`beautiful` 应被识别为游离 ADJ 或 ADJP,不进入 VP 的 candidate。
8. **spaCy 不可用**:mock nlp_loader 失败 → Engine 返回 `warnings=["spaCy model unavailable"]` + 空 phrases,不抛异常
9. **L2/L3 渐进**:`get_kind_metadata("relative_clause")` 返回 `level=3, available=False`

**不覆盖**:
- 端到端 HTTP(`app.py` 路由层面太薄,主路径靠手动 curl)
- Validator 的主谓一致以外 4 项的**实现**(规范明文要求但 M3a 范围外,仅测占位接口可调用)

### 5.2 手工验证(M3a 完成标准)

1. `pytest backend/tests/test_expansion_engine.py` 全过
2. `curl -X POST http://127.0.0.1:18765/api/expansion/analyze -d '{"sentence":"I like dogs."}' -H 'Content-Type: application/json'` 返回的 JSON 含 3 个 phrases,`NP(dogs)` 的 candidates 有 `adjective` 和 `number` 两种
3. 启动 Electron,默认句 `I usually get up at seven every morning.`,切到「句扩展」场景,看到:
   - 三栏布局(左:扩展类型库占位 / 中:句子画布 / 右:扩展可能树)
   - 中栏画布上多个节点卡片:**可扩展的高亮(蓝边+绿点),不可扩展的灰显**
   - 至少一个节点有 [+] 按钮;点 [+] 弹浮层,显示 adj 模板(`cute` / `black` / `small` 等)
   - 右栏树状结构:根=整句,二层=各 token,三层=可扩展 token 下的 kind 分支 + 模板叶子
   - 点右栏树的 kind 叶子 → 中栏对应节点 [+] 高亮(视觉联动)
4. 关闭 dev server 时端到端不会崩(已经由 M0/M1/M2 验证,这里只确认 expansion 路径不破)

---

## 6. 文件清单

### 新增(后端)
- `backend/grammar_engine/expansion_rules.py` — 规则库(短语类型→可扩展项)
- `backend/grammar_engine/expansion_templates.py` — L1 模板集(20 个)
- `backend/grammar_engine/expansion_validator.py` — Validator(主谓一致有实现,其他 4 项占位)
- `backend/grammar_engine/phrase_segmenter.py` — [新] 短语识别(spaCy noun_chunks+dep_ 拼 NP/VP/PP,M3b 换 Benepar)
- `backend/grammar_engine/expansion_engine.py` — 主入口
- `backend/tests/test_expansion_engine.py` — 单元测试(9 项)

### 新增(前端)
- `src/renderer/components/expand/ExpandScene.tsx` — 重写,三栏编排
- `src/renderer/components/expand/ExtensionLibrary.tsx` — 左栏占位
- `src/renderer/components/expand/SentenceCanvas.tsx` — 中栏画布 + 节点卡片(可扩展高亮/不可扩展灰显)
- `src/renderer/components/expand/ExtensionMenu.tsx` — [+] 弹菜单(只读,应用按钮 disabled)
- `src/renderer/components/expand/ExpansionTree.tsx` — 右栏短语结构图(M3a 标题"短语结构图",渲染 phrases+candidates 的扁平结构)

### 修改
- `backend/grammar_engine/models.py` — 追加 `Expansion*` Pydantic
- `backend/app.py` — 追加 `/api/expansion/analyze`
- `src/main/ipc/index.ts` — `analyze-sentence-expansion` handler
- `src/preload/index.ts` — `analyzeExpansion` 暴露
- `src/renderer/state/appState.ts` — `analyzeExpansion` action
- `src/renderer/types/index.ts` — `Expansion*` 类型 + `SentenceAnalysis.expansion`
- `src/renderer/App.tsx` — expand 场景自动拉取 expansion 数据(`analyze-anatomy` 模式对称)
- `docs/PROGRESS.md` — M3a 阶段记录
- `docs/DEVLOG.md` — M3a 决策与坑点

### 已知问题(spec 末尾留待后续解决)
1. **`ipc/index.ts` 三段 handler 一字不差**:`analyze-sentence` / `analyze-sentence-anatomy` / `analyze-sentence-expansion` 复制粘贴。可抽出 `forwardToBackend(path)` 工具,M3 整体结束后再重构。
2. **`appState.ts` 三个 analyze action 模板一致**:`analyzeSentence` / `analyzeAnatomy` / `analyzeExpansion` 都是 setLoading / fetch / 合并到 currentAnalysis。同样可抽 hook。
3. **句剖析和句扩展都基于 spaCy**,后续 spaCy 升级要两边同步。

---

## 7. 实施顺序(给 plan / implementation skill 用)

按 TDD 顺序:
1. 写 `expansion_rules.py` + 测试(规则库最纯,先稳)
2. 写 `expansion_templates.py` + 测试
3. 写 `expansion_validator.py` + 测试(主谓一致 4 case)
4. 写 `expansion_engine.py` + 测试(端到端 4 case)
5. 写 `app.py` 端点 + curl 验证
6. 写前端:`types` → `preload` → `ipc` → `state` → `App` → `ExpandScene` + 三栏 + 画布 + 菜单
7. 启 Electron,人工跑验证清单第 3 步
8. 写 PROGRESS / DEVLOG,提交

---

## 8. Spec Self-Review

> 按 SKILL.md checklist 第 7 项:placeholder / 矛盾 / 歧义 / 范围

- [x] **没有 placeholder**:所有 Pydantic 字段、Template 实例、kind 列表都列了具体值
- [x] **没有矛盾**:Engine 输出 schema(§2.5)和 Pydantic 模型(§2.6)对齐;UI 状态(§4.3)和组件边界(§4.2)对齐
- [x] **没有歧义**:
  - "扩展单位是短语不是 token"已定义(§2.2)— PhraseNode 是 NP/VP/PP
  - "M3a 不做"已显式枚举(§1.1)— 不会让人误以为 M3a 包含写路径
  - "模板预览"已定义(§2.4)— `surface + " " + example_anchor`(锚是短语中心词)
  - "右栏命名"(调整 3):M3a 叫「短语结构图」,**不叫**「成分句法树」(M3b 升级)
- [x] **范围清晰**:§1.1 「做 / 不做」二段式,§1.2 解释为什么这样切,§6 给出确切文件清单

---

## 9. 用户已确认(2026-06-16)

> 4 条修正 + 1 条新增,全部已落入本 spec:

1. ✅ **范围**:严格只读(保持原 spec,M3a 不做提交闭环)
2. ✅ **模板规模**:20 个(adj 7 / adv 6 / num 4 / degree 3)——用户确认"完全够"
3. ✅ **画布节点**:改为**全部 token 显示**(后端给所有 token,前端过滤标点),可扩展节点高亮(蓝边+绿点),不可扩展灰显——原 spec 是"只显示可扩展 token",已改
4. ✅ **Validator**:只实现主谓一致(有实现+测试),其他 4 项**接口全部预留**(函数签名齐、返回 PASS 占位,供 M3b/c 接入)——原 spec 措辞"占位"易误解,已明确为"签名齐+返回 PASS"
5. ✅ **新增 Expansion Tree(静态扩展可能树)**:右栏从"教学区占位"改为**静态扩展可能树**——渲染 Engine 输出的 phrases+candidates 的树状结构,与中栏画布同源数据,只读、不依赖学生操作

> **2026-06-16 二次整合(Chief Architect 建议)**:spec 从 token 级升级为 **phrase 级**(原则 #1/#2)。上方第 3/5 条的"token"措辞已被 §2/§4.2 的 phrase-level 设计取代,以此整合版为准。

> **2026-06-16 三次整合(三条架构调整)**:数据模型稳定优先于分析精度,为 M3b/M3c 预留接缝:
> - **调整 1(已落 §2.2)**:`PhraseNode` 加 `parent_id`/`children_ids`,segment() 内部建立 PP→NP/VP 挂载(消除漂浮)。M3a 不显示嵌套,但数据具备树能力。
> - **调整 2(已落 §2.2)**:VP 必须吞完整时态链(aux+modal+main+particle)。`has been working` 一个 VP,`would like` 一个 VP,`to help` 留 M3b。features 含 aux_chain/modal/aspect/tense。
> - **调整 3(已落 §4.2)**:右栏 M3a 命名「短语结构图」,**不叫**「成分句法树」(M3b 引入 Benepar 后升级)。组件文件名不变,仅 UI 标题文案 M3b 改。

## 10. Grammar Engine 长期路线图(Chief Architect 视角)

> 用户 2026-06-16 设计建议的 5-Phase roadmap,M3a 是 Phase 1 的只读起点。
> **设计精神(三次整合)**:M3a 目标是验证 Grammar Engine 的数据模型稳定性,不是实现最终句法分析器。优先保证 PhraseNode 可扩展、Parent-Child 可挂载、VP 特征完整——保证 M3b 接 Benepar / M3c 接 LanguageTool 时无需重构数据结构。

| Phase | 内容 | M3a 关系 | Benepar/LT |
|---|---|---|---|
| **Phase 1** | Word-level(NP 加形容词/数词,VP 加副词) | **M3a = 只读骨架**(phrase-level 数据模型 + 规则 + 模板 + Validator 主谓一致) | 不装 |
| Phase 1 写路径 | 提交扩展闭环 + 新增高亮 + 连线 | **M3a+1** | 不装 |
| **Phase 2** | Phrase-level(PP / participle / infinitive phrase) | M3b | **装 Benepar**,`phrase_segmenter` 换实现 |
| **Phase 3** | Clause-level(relative / adverbial / noun clause)+ 关系代词匹配 | M3c | **接 LanguageTool** 作第 6 道校验 |
| Phase 4 | Sentence restructuring(句式重构) | M4+ | — |
| Phase 5 | Grammar knowledge graph(语法知识图谱) | M5+ | — |

**原则落地检查表**(M3a 已落 vs 待落):

| 原则 | M3a 状态 | 落点 |
|---|---|---|
| #1 Never expand tokens | ✅ 数据模型是 phrase | §2.2 PhraseNode |
| #2 Expand phrases only | ✅ 规则键是 PhraseType | §2.3 NP_RULES/VP_RULES |
| #3 Expansion Tree | 🟡 静态成分树(M3a+1 动态化) | §4.2 右栏 |
| #4 Parent-Child | ❌ M3a+1(提交才产生父子) | — |
| #5 Modifier Scope | ❌ M3a+1(提交才维护域) | — |
| #6 Feature Slots | ✅ NP/VP 带 features | §2.2 features 字段 |
| #7 Tense State | 🟡 VP.features["tense"](M3a 只读) | §2.2 |
| #8 Depth Limits | ❌ M3a+1(无嵌套扩展) | — |
| #9 Validate before render | 🟡 Validator 写好但 M3a 只读不调用 | §2.5 |
| #10 Rule Engine not LLM | ✅ M3a 无 AI | — |

**接缝预留**:`phrase_segmenter.segment(doc)` 返回契约固定,M3b 装 Benepar 只换函数体;`validate(...)` 接收 phrases,M3c 加 `validate_with_languagetool` 可选步骤——都不破坏 M3a 的接口。
