# M3b — Sentence Expansion Phase 2: Benepar + Phrase-level扩展

> 设计稿日期: 2026-06-23
> 状态: 待确认
> 前置: M3a + M3a+1 已完成(commit 042d340)
> 关联: `2026-06-16-sentence-expansion-m3a-design.md` §10 路线图

---

## 1. 背景与目标

M3a+M3a+1 已交付 **Level 1 词级扩展的完整闭环**(形容词/副词/数词)+ 提交/撤销/历史 UI。M3b 是 **Phase 2 短语级扩展**，引入 Berkeley Neural Parser (Benepar) 提升句法分析精度，并支持 PP/participle/infinitive phrase 扩展。

### 1.1 M3b 核心任务

✅ **做**:
1. **安装 Benepar** - `pip install benepar` + 下载 `benepar_en3` 模型
2. **升级 `phrase_segmenter.py`** - 从 spaCy noun_chunks 简化版切换到 Benepar 成分树精确版
3. **L2 规则和模板** - 添加 PP / participle phrase / infinitive phrase 的扩展规则和模板
4. **Validator tense_consistency 实现** - 检查多个 VP 的时态一致性
5. **前端右栏升级** - 标题从「短语结构图」改为「成分句法树」(组件文件名不变)
6. **单元测试** - phrase_segmenter 的 Benepar 路径 + L2 规则/模板/apply + tense_consistency

❌ **不做**(留给 M3c):
- Level 3 从句扩展(relative/adverbial/noun clause)
- LanguageTool 集成
- Validator 其他 3 项(clause_completeness / non_finite / relative_pronoun)

### 1.2 为什么 Benepar

M3a 的 spaCy 简化版存在两个系统性问题：
1. **PP 挂载不精确** - "简化规则(PP 跟 NP 挂 NP)" 无法处理复杂嵌套，如 `the dog [in the park [near the river]]` 两层 PP 嵌套
2. **短语边界模糊** - spaCy `noun_chunks` 对某些结构(如带分词修饰的 NP)边界不准

Benepar 是成分句法分析器，直接产出 `(NP (DT the) (NN dog))` 嵌套树，天然解决上述问题。且 Benepar 输出与 M3a 的 `PhraseNode` 数据模型完全兼容——证明了 M3a "数据模型稳定优先于精度" 的设计决策正确。

---

## 2. Benepar 集成

### 2.1 安装与模型

```bash
pip install benepar
python -c "import benepar; benepar.download('benepar_en3')"
```

- `benepar==0.2.0`(最新稳定版)
- `benepar_en3` 模型(基于 PTB 训练，准确率 95.5% F1)

### 2.2 phrase_segmenter.py 重写策略

**保持接口契约不变**:
```python
def segment(doc) -> List[PhraseNode]:
    """M3b Benepar 实现。接口与 M3a 完全相同，只换函数体。"""
```

**新流程**(Benepar 成分树 → PhraseNode 列表):
1. `benepar.Parser.parse(doc.sents)` → 成分树(nltk.Tree 对象)
2. DFS 遍历树，对每个非终结符节点:
   - `(NP ...)` → `PhraseNode(type="NP", ...)`
   - `(VP ...)` → `PhraseNode(type="VP", ...)`
   - `(PP ...)` → `PhraseNode(type="PP", ...)`
   - `(S ...)` / `(SBAR ...)` → `PhraseNode(type="CLAUSE", ...)`
3. Parent-Child 挂载直接来自树结构(不需要 M3a 的"相邻性猜测")
4. 特征槽填充:
   - NP: 从 head token 的 spaCy morph 读 number/person
   - VP: 从 Benepar 的 VP 子树提取 aux_chain/modal/tense/aspect
5. 返回扁平 `List[PhraseNode]`(保持与 M3a 的 IPC 兼容)

**关键决策**:
- **M3a 的简化规则完全废弃** - PP 挂载、VP 时态链回溯都由 Benepar 树结构替代
- **`to help` 现在纳入 VP** - Benepar 会给 `(VP (TO to) (VP (VB help)))` 嵌套结构，M3b 识别为 infinitive VP
- **ADJP / ADVP 现在支持** - M3a 未实现，M3b 从 Benepar 的 `(ADJP ...)` / `(ADVP ...)` 直接映射
- **Clause 识别升级** - `(SBAR (WHNP ...) (S ...))` → relative clause; `(SBAR (IN because) (S ...))` → adverbial clause

### 2.3 后向兼容

M3a 的测试用例需保持通过(或合理调整断言):
- `segment(doc("I like dogs."))` 仍返回 3 个 phrase(NP/VP/NP)
- `segment(doc("He has been working."))` VP 仍含完整时态链
- PP 挂载的父子关系更准确(从"相邻猜测"升级为"树结构真实")

---

## 3. Level 2 扩展规则和模板

### 3.1 规则库扩展 (`expansion_rules.py`)

```python
# M3b 新增 L2 规则(available=True)
NP_RULES:  ["adjective", "number", "prepositional_phrase", "participle_phrase", "relative_clause"]
VP_RULES:  ["adverb", "adverbial_clause", "infinitive_complement"]  # infinitive_complement 新增
ADJP_RULES: ["degree_adverb", "infinitive_complement"]  # 新增 infinitive(如 "happy to see")
PP_RULES:   []  # PP 本身不扩展(它是扩展项,不是被扩展对象)

# M3b 开放的 L2 kind
"prepositional_phrase"    # NP → PP(如 "the dog" → "the dog in the park")
"participle_phrase"       # NP → participle(如 "the dog" → "the dog running fast")
"infinitive_phrase"       # NP → infinitive(如 "a book" → "a book to read")
"infinitive_complement"   # VP/ADJP → infinitive(如 "want" → "want to go" / "happy" → "happy to see")
```

**L3 仍未开放**(M3c):
- `relative_clause` / `adverbial_clause` / `noun_clause` - `available=False`

### 3.2 模板库扩展 (`expansion_templates.py`)

M3a 有 20 个 L1 模板(adj 7 + adv 6 + num 4 + degree 3)。M3b 新增 **15 个 L2 模板**:

```python
L2_TEMPLATES: dict[ExpansionKind, list[Template]] = {
    "prepositional_phrase": [  # 5 个
        Template("prepositional_phrase", "tpl_pp_in_park", "in the park", "PP", "location", "dog"),
        Template("prepositional_phrase", "tpl_pp_on_table", "on the table", "PP", "location", "book"),
        Template("prepositional_phrase", "tpl_pp_with_friends", "with friends", "PP", "accompaniment", "go"),
        Template("prepositional_phrase", "tpl_pp_at_school", "at school", "PP", "location", "study"),
        Template("prepositional_phrase", "tpl_pp_for_you", "for you", "PP", "benefactive", "buy"),
    ],
    "participle_phrase": [  # 4 个
        Template("participle_phrase", "tpl_part_running_fast", "running fast", "VBG-PHRASE", "action", "dog"),
        Template("participle_phrase", "tpl_part_playing_outside", "playing outside", "VBG-PHRASE", "action", "children"),
        Template("participle_phrase", "tpl_part_covered_snow", "covered with snow", "VBN-PHRASE", "state", "mountain"),
        Template("participle_phrase", "tpl_part_written_author", "written by the author", "VBN-PHRASE", "agent", "book"),
    ],
    "infinitive_phrase": [  # 3 个(NP 后置修饰)
        Template("infinitive_phrase", "tpl_inf_to_read", "to read", "TO-VP", "purpose", "book"),
        Template("infinitive_phrase", "tpl_inf_to_eat", "to eat", "TO-VP", "purpose", "food"),
        Template("infinitive_phrase", "tpl_inf_to_visit", "to visit", "TO-VP", "purpose", "place"),
    ],
    "infinitive_complement": [  # 3 个(VP/ADJP 补足语)
        Template("infinitive_complement", "tpl_inf_comp_to_go", "to go", "TO-VP", "goal", "want"),
        Template("infinitive_complement", "tpl_inf_comp_to_see", "to see", "TO-VP", "experience", "happy"),
        Template("infinitive_complement", "tpl_inf_comp_to_help", "to help", "TO-VP", "assistance", "try"),
    ],
}
```

**拼装规则**(apply_template 逻辑，在 `expansion_engine.py` 或新建 `template_applicator.py`):
- **PP**: 插入到 NP 末尾。`"the dog"` + `"in the park"` → `"the dog in the park"`
- **Participle**: 插入到 NP 末尾。`"the dog"` + `"running fast"` → `"the dog running fast"`
- **Infinitive (NP 后置)**: 插入到 NP 末尾。`"a book"` + `"to read"` → `"a book to read"`
- **Infinitive complement (VP/ADJP)**: 插入到 VP/ADJP 末尾。`"want"` + `"to go"` → `"want to go"` / `"happy"` + `"to see"` → `"happy to see"`

---

## 4. Validator tense_consistency 实现

### 4.1 规则

在 `expansion_validator.py` 的 `validate_tense_consistency()` 中实现(M3a 是占位返回 PASS)。

**检查逻辑**:
1. 找出所有 `syntactic_role == "predicate"` 的 VP
2. 如果有 2+ 个 VP，检查它们的 `features["tense"]` 是否一致
3. 允许的一致组合:
   - 全部 simple_present
   - 全部 simple_past
   - 全部 simple_future_*
   - present + present_perfect(过去动作持续到现在)
   - past + past_perfect(过去完成)
4. 不一致示例:
   - `"I go to school and worked hard."` → ERROR(present + past 混用)
   - `"She likes dogs but will adopt a cat."` → WARNING(present + future 可接受但建议统一)

**返回**:
```python
ValidationReport(
    severity="WARNING",  # 或 "ERROR"
    is_valid=False,
    errors=["时态不一致: 'go' (simple_present) 和 'worked' (simple_past)"],
    warnings=[],
    infos=[],
    auto_corrections=[]  # 时态不一致无自动修正
)
```

### 4.2 测试用例

```python
def test_validator_tense_consistency_pass():
    # 全部 simple_present → PASS
    assert validate_tense_consistency("I like dogs and eat apples.", ...).severity == "PASS"

def test_validator_tense_consistency_error():
    # present + past 混用 → ERROR
    report = validate_tense_consistency("I go to school and worked hard.", ...)
    assert report.severity == "ERROR"
    assert "时态不一致" in report.errors[0]
```

---

## 5. 前端右栏升级

在 `ExpansionTree.tsx` 中:

```tsx
// M3a 标题
<h3>短语结构图</h3>

// M3b 标题(组件文件名不变)
<h3>成分句法树 (Constituency Parse Tree)</h3>
```

在 `ExpandScene.tsx` 的右侧面板描述中同步更新。

---

## 6. 测试策略

### 6.1 后端单元测试

**新增 `test_benepar_segmenter.py`**(独立文件，与 M3a 的 `test_expansion_engine.py` 并行):
1. `test_benepar_basic_sentence()` - `"I like dogs."` → 3 个 phrase(NP/VP/NP)
2. `test_benepar_pp_attachment()` - `"the dog in the park"` → PP.parent_id 指向 NP
3. `test_benepar_nested_pp()` - `"the dog in the park near the river"` → 两层 PP 正确嵌套
4. `test_benepar_vp_infinitive()` - `"I want to help."` → VP("want") + VP("to help") 或 VP("want to help")
5. `test_benepar_participle_phrase()` - `"the dog running fast"` → NP 含 participle 修饰
6. `test_benepar_clause_identification()` - `"I know that he likes dogs."` → CLAUSE("that he likes dogs")

**扩展 `test_expansion_engine.py`**:
7. `test_apply_template_pp()` - `"the dog"` + PP 模板 → `"the dog in the park"`
8. `test_apply_template_participle()` - `"the dog"` + participle → `"the dog running fast"`
9. `test_apply_template_infinitive()` - `"a book"` + infinitive → `"a book to read"`
10. `test_validator_tense_consistency_*()` - 4 个测试(pass / error / warning / mixed)

### 6.2 手工验证

1. `pytest backend/tests/` 全过(新增 + 旧有)
2. `curl /api/expansion/analyze -d '{"sentence":"the dog in the park"}'` → PP.parent_id 正确
3. Electron 窗口:
   - 输入 `"I like the dog in the park."` → 画布显示 PP 短语卡片(M3a 没有)
   - 点击 NP("the dog") 的 [+] → 候选菜单出现 "介词短语" / "分词短语"(L2 新增)
   - 应用 PP 模板 → 句子变为 `"I like the dog in the park."`，右栏树更新
   - 右栏标题显示 **「成分句法树」**

---

## 7. 实施顺序

按 TDD + 垂直切分:

### M3b.1 后端 Benepar 集成
1. 安装 Benepar: `pip install benepar` + 下载模型
2. 重写 `phrase_segmenter.py` 的 `segment()` 函数(新函数名 `segment_benepar`)
3. 写 `test_benepar_segmenter.py`(6 测试)
4. 在 `expansion_engine.py` 中切换调用 `segment_benepar`
5. 跑 M3a 的旧测试，调整断言(PP 挂载更准确)

### M3b.2 L2 规则和模板
6. `expansion_rules.py` 添加 L2 kind(available=True)
7. `expansion_templates.py` 添加 15 个 L2 模板
8. `expansion_engine.py` 或新建 `template_applicator.py` 实现 L2 拼装规则
9. 写 `test_apply_template_pp/participle/infinitive`(3 测试)

### M3b.3 Validator tense_consistency
10. 实现 `validate_tense_consistency()` 函数体
11. 写 4 个测试(pass / error / warning / mixed)

### M3b.4 前端升级
12. `ExpansionTree.tsx` 标题改为「成分句法树」
13. `ExpandScene.tsx` 右侧面板描述同步
14. Electron 手工验证

### M3b.5 文档和提交
15. 更新 `PROGRESS.md` / `DEVLOG.md`
16. 提交: `feat(M3b): Benepar + L2 phrase-level 扩展 + tense_consistency`

---

## 8. 文件清单

### 新增
- `backend/tests/test_benepar_segmenter.py` - Benepar 专项测试

### 修改
- `backend/requirements.txt` - 添加 `benepar==0.2.0`
- `backend/grammar_engine/phrase_segmenter.py` - 重写 `segment()` 为 Benepar 实现
- `backend/grammar_engine/expansion_rules.py` - L2 规则开放
- `backend/grammar_engine/expansion_templates.py` - 15 个 L2 模板
- `backend/grammar_engine/expansion_engine.py` - L2 拼装逻辑(或新建 `template_applicator.py`)
- `backend/grammar_engine/expansion_validator.py` - 实现 `validate_tense_consistency()`
- `backend/tests/test_expansion_engine.py` - 新增 L2 apply 测试 + tense_consistency 测试
- `src/renderer/components/expand/ExpansionTree.tsx` - 标题改「成分句法树」
- `src/renderer/components/expand/ExpandScene.tsx` - 右侧描述更新
- `docs/PROGRESS.md` - M3b 标记完成
- `docs/DEVLOG.md` - M3b 决策和坑点

---

## 9. 风险和预案

### 风险 1: Benepar 模型下载失败
- **预案**: 提供离线下载链接 + 手动放置到 `~/.cache/benepar/` 的指引

### 风险 2: Benepar 解析慢(每句 200-500ms)
- **预案**: M3b 接受性能下降(教学场景单句分析可接受)；M4 引入缓存层

### 风险 3: Benepar 对口语句/语法错误句崩溃
- **预案**: try-except 包裹，失败时降级回 M3a 的 spaCy 简化版 + warning

### 风险 4: M3a 测试因 PP 挂载变准而失败
- **预案**: 合理调整断言(如 PP.parent_id 从 None 变为真实父节点 id)

---

## 10. 成功标准

- ✅ `pytest backend/tests/` 全过(新增 13 测试 + M3a 旧有 30 测试)
- ✅ `curl /api/expansion/analyze` 对复杂句(含嵌套 PP)返回正确树结构
- ✅ Electron 窗口手工验证 L2 扩展(PP/participle/infinitive)可应用
- ✅ 右栏标题显示「成分句法树」
- ✅ tsc --noEmit 零错
- ✅ npm run build 全链路通过

---

## 11. M3b 后的世界

M3b 完成后，Grammar Lab 的 Sentence Expansion 模块将支持:
- ✅ Level 1 词级扩展(形容词/副词/数词/程度副词) - M3a
- ✅ 提交/撤销/历史/50步上限 - M3a+1
- ✅ Level 2 短语级扩展(PP/participle/infinitive phrase) - M3b
- ✅ Benepar 成分句法分析(95.5% F1 精度) - M3b
- ✅ Validator 主谓一致 + 时态一致 - M3a + M3b

下一步 M3c 将添加:
- Level 3 从句级扩展(relative/adverbial/noun clause)
- LanguageTool 全句语法校验
- Validator 其他 3 项(clause_completeness / non_finite / relative_pronoun)
