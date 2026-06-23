# M3c2 实施计划：模板基础架构

> **日期:** 2026-06-23  
> **阶段:** M3c2 - Template Foundation (Internal)  
> **前置:** M3c1 完成（验证层冻结）  
> **工作量:** 2-3 天

---

## 0. 执行摘要

M3c2 建立从句扩展的模板基础架构，但**不对外开放**（available=False）。这是内部准备阶段。

### 核心任务
1. TemplateBase / WordTemplate / ClauseTemplate 抽象层
2. Slot / ClauseRealizer 基础设施
3. 3 类从句的 realizer 框架（relative/adverbial/noun）
4. 单元测试（无 E2E，因为 available=False）

### 架构原则
- **无 UI，无 available=True** - 纯后端基础设施
- **槽位驱动设计** - Slot 是从句模板的核心抽象
- **Realizer 分离** - 实现与模板定义分离
- **为 M3c3-5 铺路** - 每个阶段只需加模板，不改架构

### M3c2 完成后
- ✅ 模板架构稳定
- ✅ M3c3-5 只需定义模板数据，无需改代码
- ✅ 从句扩展的"管道"打通

---

## 1. 架构设计

### 1.1 模板类层次

```
TemplateBase (抽象)
├── WordTemplate (M3a 已有: adj/adv/number)
└── ClauseTemplate (M3c2 新增)
    ├── RelativeClauseTemplate
    ├── AdverbialClauseTemplate
    └── NounClauseTemplate
```

### 1.2 Slot 槽位系统

**定义：** Slot 是从句模板中的占位符，运行时被实际内容填充。

**示例：**
```python
# Template: "who <VERB>"
slots = [
    Slot(name="verb", type="VP", required=True)
]

# Realization: "who runs fast"
# verb slot ← "runs fast" (从原句的 VP 提取或生成)
```

### 1.3 ClauseRealizer

**职责：** 将模板 + 槽位值 → 最终从句文本

```python
class ClauseRealizer:
    def realize(
        self, 
        template: ClauseTemplate,
        slot_values: Dict[str, str],
        context: RealizationContext
    ) -> str:
        """槽位替换 + 语法调整"""
        pass
```

---

## 2. 任务分解

### Task 1: TemplateBase 抽象层
- [ ] 定义 TemplateBase 基类
- [ ] ClauseTemplate 子类
- [ ] Slot 数据结构
- [ ] 单元测试

**文件:** `backend/grammar_engine/template_base.py`

### Task 2: ClauseRealizer 基础设施
- [ ] ClauseRealizer 基类
- [ ] RealizationContext 上下文
- [ ] 槽位替换逻辑
- [ ] 单元测试

**文件:** `backend/grammar_engine/clause_realizer.py`

### Task 3: 3 类从句 Template 定义
- [ ] RelativeClauseTemplate
- [ ] AdverbialClauseTemplate  
- [ ] NounClauseTemplate
- [ ] 每类 1-2 个占位模板（available=False）
- [ ] 单元测试

**文件:** `backend/grammar_engine/clause_templates.py`

### Task 4: 集成到 expansion_engine
- [ ] expansion_engine.get_candidates() 识别从句扩展点
- [ ] 返回 ClauseTemplate candidates（available=False）
- [ ] apply_template() 调用 ClauseRealizer
- [ ] 单元测试

**文件:** `backend/grammar_engine/expansion_engine.py`

### Task 5: 文档更新
- [ ] PROGRESS.md 标记 M3c2 完成
- [ ] DEVLOG.md 添加 M3c2 章节
- [ ] 本设计文档完成

---

## 3. 数据结构设计

### 3.1 ClauseTemplate

```python
@dataclass
class ClauseTemplate:
    template_id: str
    clause_type: Literal["relative", "adverbial", "noun"]
    surface: str  # Template pattern, e.g., "who <VERB>"
    slots: List[Slot]
    constraints: Dict[str, Any]  # 语法约束
    available: bool = False  # M3c2 全部 False
    
@dataclass
class Slot:
    name: str
    type: str  # "VP", "NP", "ADJ", etc.
    required: bool
    default: Optional[str] = None
```

### 3.2 RealizationContext

```python
@dataclass
class RealizationContext:
    original_sentence: str
    doc: Any  # spaCy Doc
    phrases: List[PhraseNode]
    target_phrase_id: str
```

---

## 4. 实现示例

### 4.1 定语从句模板（占位）

```python
RELATIVE_CLAUSE_TEMPLATES = [
    ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={"antecedent_type": "person"},
        available=False  # M3c3 才改为 True
    ),
    ClauseTemplate(
        template_id="tpl_rel_which_verb",
        clause_type="relative",
        surface="which <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={"antecedent_type": "thing"},
        available=False
    ),
]
```

### 4.2 Realizer 示例

```python
class RelativeClauseRealizer(ClauseRealizer):
    def realize(self, template, slot_values, context):
        # 1. 替换槽位
        text = template.surface
        for slot in template.slots:
            text = text.replace(f"<{slot.name.upper()}>", slot_values[slot.name])
        
        # 2. 语法调整（agreement, tense, etc.）
        # TODO: M3c3 实现
        
        return text
```

---

## 5. 测试策略

### 5.1 单元测试（100% 覆盖）

**template_base_test.py:**
- ClauseTemplate 创建和验证
- Slot 数据结构

**clause_realizer_test.py:**
- 槽位替换逻辑
- RealizationContext 构建

**clause_templates_test.py:**
- 3 类从句模板定义
- constraints 验证

**expansion_engine_test.py:**
- get_candidates() 识别从句扩展点
- apply_template() 调用 realizer

### 5.2 无集成测试

M3c2 不做 E2E 测试，因为 available=False，用户无法触发。

---

## 6. 验收标准

- [ ] TemplateBase / ClauseTemplate / Slot 定义完整
- [ ] ClauseRealizer 基础逻辑实现
- [ ] 3 类从句各有 1-2 个占位模板（available=False）
- [ ] 单元测试 100% 通过
- [ ] expansion_engine 识别从句扩展点
- [ ] apply_template() 调用 realizer（但前端不可见）
- [ ] 文档更新完成

---

## 7. 风险与依赖

### 风险
- Slot 抽象过度设计 → 保持简单，M3c3 再迭代
- Realizer 语法调整复杂 → M3c2 只做替换，M3c3 再加调整

### 依赖
- ✅ M3c1 完成（验证层冻结）
- ✅ phrase_segmenter 稳定（M3b Benepar 集成完成）

---

## 8. 后续阶段

- **M3c3**: 开放定语从句（8-12 个 who/which/that 模板，available=True）
- **M3c4**: 开放状语从句（10-12 个 because/when/if 模板）
- **M3c5**: 开放名词性从句（10-12 个 that/whether/what 模板）

---

## 9. 文件清单

### 新增（后端）
- `backend/grammar_engine/template_base.py` - 模板基类
- `backend/grammar_engine/clause_realizer.py` - 实现器
- `backend/grammar_engine/clause_templates.py` - 3 类从句模板定义
- `backend/tests/test_template_base.py` - 单元测试
- `backend/tests/test_clause_realizer.py` - 单元测试
- `backend/tests/test_clause_templates.py` - 单元测试

### 修改（后端）
- `backend/grammar_engine/expansion_engine.py` - 集成 ClauseTemplate

### 文档
- `docs/superpowers/plans/2026-06-23-m3c2-template-foundation.md` - 本文档
- `docs/PROGRESS.md` - 更新进度
- `docs/DEVLOG.md` - 添加 M3c2 章节
