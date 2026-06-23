"""M3c3 定语从句测试"""
import pytest
from grammar_engine.clause_templates import (
    RELATIVE_CLAUSE_TEMPLATES,
    get_available_clause_templates,
    get_template_by_id,
)
from grammar_engine.clause_realizer import RelativeClauseRealizer, RealizationContext
from grammar_engine.phrase_segmenter import PhraseNode
from grammar_engine.expansion_rules import get_available_rules_for_phrase


# ===================== 模板定义测试 =====================

def test_relative_clause_templates_count():
    """M3c3: 定语从句模板数量 >= 10"""
    assert len(RELATIVE_CLAUSE_TEMPLATES) >= 10, f"Expected >= 10 templates, got {len(RELATIVE_CLAUSE_TEMPLATES)}"


def test_all_relative_templates_available():
    """M3c3: 所有定语从句模板已开放"""
    for t in RELATIVE_CLAUSE_TEMPLATES:
        assert t.available is True, f"{t.template_id} should be available=True"


def test_get_available_includes_relative():
    """M3c3: get_available_clause_templates 包含定语从句"""
    available = get_available_clause_templates()
    relative_count = sum(1 for t in available if t.clause_type == "relative")
    assert relative_count >= 10, f"Expected >= 10 available relative templates, got {relative_count}"


def test_relative_template_structure():
    """验证定语从句模板结构完整"""
    for t in RELATIVE_CLAUSE_TEMPLATES:
        assert t.template_id.startswith("tpl_rel_"), f"Invalid template_id: {t.template_id}"
        assert t.clause_type == "relative"
        assert len(t.slots) > 0, f"{t.template_id} has no slots"
        assert "antecedent_type" in t.constraints, f"{t.template_id} missing antecedent_type constraint"


def test_subject_relative_templates():
    """验证主语关系从句模板（who/which/that + VP）"""
    subj_templates = [t for t in RELATIVE_CLAUSE_TEMPLATES if t.constraints.get("clause_function") == "subject"]
    assert len(subj_templates) >= 3, "Should have at least 3 subject relative templates"

    # 验证 who
    who_subj = get_template_by_id("tpl_rel_who_subj")
    assert who_subj is not None
    assert who_subj.constraints["antecedent_type"] == "person"
    assert len(who_subj.slots) == 1
    assert who_subj.slots[0].type == "VP"


def test_object_relative_templates():
    """验证宾语关系从句模板（who/which/that + NP + VP）"""
    obj_templates = [t for t in RELATIVE_CLAUSE_TEMPLATES if t.constraints.get("clause_function") == "object"]
    assert len(obj_templates) >= 4, "Should have at least 4 object relative templates"


def test_possessive_relative_template():
    """验证所有格关系从句模板（whose）"""
    whose = get_template_by_id("tpl_rel_whose")
    assert whose is not None
    assert whose.constraints.get("clause_function") == "possessive"
    assert len(whose.slots) == 2  # noun + verb


def test_adverbial_relative_templates():
    """验证关系副词从句模板（where/when）"""
    where = get_template_by_id("tpl_rel_where")
    when = get_template_by_id("tpl_rel_when")

    assert where is not None
    assert where.constraints["antecedent_type"] == "place"

    assert when is not None
    assert when.constraints["antecedent_type"] == "time"


# ===================== Realizer 测试 =====================

def test_relative_realizer_who_subject():
    """who + VP (主语从句)"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_who_subj")

    slot_values = {"verb": "lives here"}

    # Mock context (先行词是人)
    antecedent = PhraseNode(
        id="p1", type="NP", text="the man",
        head_token_text="man", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "man"}
    )
    context = RealizationContext(
        original_sentence="The man is my teacher.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "who lives here"


def test_relative_realizer_which_subject():
    """which + VP (物)"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_which_subj")

    slot_values = {"verb": "is red"}

    # Mock context (先行词是物)
    antecedent = PhraseNode(
        id="p1", type="NP", text="the book",
        head_token_text="book", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "book"}
    )
    context = RealizationContext(
        original_sentence="The book is interesting.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "which is red"


def test_relative_realizer_that_universal():
    """that + VP (通用，无约束)"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_that_subj")

    slot_values = {"verb": "runs fast"}

    # Mock context (先行词是物)
    antecedent = PhraseNode(
        id="p1", type="NP", text="the dog",
        head_token_text="dog", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "dog"}
    )
    context = RealizationContext(
        original_sentence="The dog is cute.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "that runs fast"


def test_relative_realizer_antecedent_mismatch():
    """约束验证失败：who 用于非人先行词"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_who_subj")  # 需要 person

    slot_values = {"verb": "is red"}

    # Mock context (先行词是物)
    antecedent = PhraseNode(
        id="p1", type="NP", text="the book",
        head_token_text="book", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "book"}
    )
    context = RealizationContext(
        original_sentence="The book is interesting.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    # 应该抛出 ValueError（约束不匹配）
    with pytest.raises(ValueError, match="Antecedent type mismatch"):
        realizer.realize(template, slot_values, context)


def test_relative_realizer_which_for_person_fails():
    """约束验证失败：which 用于人"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_which_subj")  # 需要 thing

    slot_values = {"verb": "teaches math"}

    # Mock context (先行词是人)
    antecedent = PhraseNode(
        id="p1", type="NP", text="the teacher",
        head_token_text="teacher", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "teacher"}
    )
    context = RealizationContext(
        original_sentence="The teacher is kind.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    with pytest.raises(ValueError, match="Antecedent type mismatch"):
        realizer.realize(template, slot_values, context)


def test_relative_realizer_object_clause():
    """宾语从句：who + NP + VP"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_who_obj")

    slot_values = {"subject": "I", "verb": "met"}

    antecedent = PhraseNode(
        id="p1", type="NP", text="the man",
        head_token_text="man", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "man"}
    )
    context = RealizationContext(
        original_sentence="The man is a doctor.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "who I met"


def test_relative_realizer_whose():
    """所有格从句：whose + NP + VP"""
    realizer = RelativeClauseRealizer()
    template = get_template_by_id("tpl_rel_whose")

    slot_values = {"noun": "car", "verb": "is red"}

    antecedent = PhraseNode(
        id="p1", type="NP", text="the man",
        head_token_text="man", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "man"}
    )
    context = RealizationContext(
        original_sentence="The man lives here.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "whose car is red"


# ===================== 先行词类型识别测试 =====================

def test_antecedent_type_detection_person():
    """先行词类型识别：person"""
    realizer = RelativeClauseRealizer()

    test_cases = [
        ("teacher", "NOUN", "teacher"),
        ("man", "NOUN", "man"),
        ("student", "NOUN", "student"),
        ("he", "PRON", "he"),
        ("she", "PRON", "she"),
    ]

    for head_text, head_pos, head_lemma in test_cases:
        phrase = PhraseNode(
            id="p1", type="NP", text=f"the {head_text}",
            head_token_text=head_text, head_pos=head_pos,
            syntactic_role="subject", span=(0, 2),
            features={"head_lemma": head_lemma}
        )
        assert realizer._get_antecedent_type(phrase) == "person", f"Failed for {head_text}"


def test_antecedent_type_detection_thing():
    """先行词类型识别：thing"""
    realizer = RelativeClauseRealizer()

    test_cases = ["book", "car", "dog", "table", "computer"]

    for head_lemma in test_cases:
        phrase = PhraseNode(
            id="p1", type="NP", text=f"the {head_lemma}",
            head_token_text=head_lemma, head_pos="NOUN",
            syntactic_role="subject", span=(0, 2),
            features={"head_lemma": head_lemma}
        )
        assert realizer._get_antecedent_type(phrase) == "thing", f"Failed for {head_lemma}"


def test_antecedent_type_detection_place():
    """先行词类型识别：place"""
    realizer = RelativeClauseRealizer()

    test_cases = ["city", "school", "park", "home", "place", "building"]

    for head_lemma in test_cases:
        phrase = PhraseNode(
            id="p1", type="NP", text=f"the {head_lemma}",
            head_token_text=head_lemma, head_pos="NOUN",
            syntactic_role="subject", span=(0, 2),
            features={"head_lemma": head_lemma}
        )
        assert realizer._get_antecedent_type(phrase) == "place", f"Failed for {head_lemma}"


def test_antecedent_type_detection_time():
    """先行词类型识别：time"""
    realizer = RelativeClauseRealizer()

    test_cases = ["day", "year", "time", "moment", "morning", "week"]

    for head_lemma in test_cases:
        phrase = PhraseNode(
            id="p1", type="NP", text=f"the {head_lemma}",
            head_token_text=head_lemma, head_pos="NOUN",
            syntactic_role="subject", span=(0, 2),
            features={"head_lemma": head_lemma}
        )
        assert realizer._get_antecedent_type(phrase) == "time", f"Failed for {head_lemma}"


def test_antecedent_type_detection_reason():
    """先行词类型识别：reason"""
    realizer = RelativeClauseRealizer()

    phrase = PhraseNode(
        id="p1", type="NP", text="the reason",
        head_token_text="reason", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "reason"}
    )
    assert realizer._get_antecedent_type(phrase) == "reason"


# ===================== expansion_rules 集成测试 =====================

def test_expansion_rules_relative_clause_available():
    """expansion_rules: relative_clause 已开放"""
    from grammar_engine.expansion_rules import KIND_METADATA

    assert KIND_METADATA["relative_clause"]["available"] is True
    assert KIND_METADATA["relative_clause"]["level"] == 3
    assert KIND_METADATA["relative_clause"]["label_cn"] == "定语从句"


def test_get_available_rules_includes_relative_clause():
    """NP 的可用规则包含 relative_clause"""
    available = get_available_rules_for_phrase("NP")
    assert "relative_clause" in available, f"Expected relative_clause in {available}"


# ===================== expansion_engine 集成测试 =====================

def test_expansion_engine_returns_relative_clause_candidates():
    """expansion_engine.analyze() 返回定语从句候选"""
    from grammar_engine.expansion_engine import analyze

    result = analyze("The man likes dogs.")

    # 找到 "man" 的 NP
    man_phrase = next((p for p in result["phrases"] if "man" in p.text), None)
    assert man_phrase is not None, "Should find 'man' phrase"
    assert man_phrase.is_expandable, "man phrase should be expandable"

    # 检查是否有 relative_clause 候选
    relative_cands = [c for c in man_phrase.candidates if c["kind"] == "relative_clause"]
    assert len(relative_cands) > 0, "Should have relative_clause candidates"
    assert relative_cands[0]["available"] is True, "relative_clause should be available"
    assert len(relative_cands[0]["templates"]) >= 10, f"Should have >= 10 templates, got {len(relative_cands[0]['templates'])}"


def test_expansion_templates_get_relative_clause_templates():
    """expansion_templates.get_templates_for_kind 返回定语从句模板"""
    from grammar_engine.expansion_templates import get_templates_for_kind

    templates = get_templates_for_kind("relative_clause")
    assert len(templates) >= 10, f"Expected >= 10 templates, got {len(templates)}"

    # 验证返回的是 ClauseTemplate 实例
    for t in templates:
        assert hasattr(t, "clause_type")
        assert t.clause_type == "relative"
        assert hasattr(t, "slots")
        assert hasattr(t, "constraints")
