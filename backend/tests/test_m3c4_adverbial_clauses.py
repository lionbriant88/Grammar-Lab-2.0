"""M3c4 状语从句测试"""
import pytest
from grammar_engine.clause_templates import (
    ADVERBIAL_CLAUSE_TEMPLATES,
    get_available_clause_templates,
    get_template_by_id,
)
from grammar_engine.clause_realizer import AdverbialClauseRealizer, RealizationContext
from grammar_engine.phrase_segmenter import PhraseNode
from grammar_engine.expansion_rules import get_available_rules_for_phrase


# ===================== 模板定义测试 =====================

def test_adverbial_templates_count():
    """M3c4: 状语从句模板数量 >= 12"""
    assert len(ADVERBIAL_CLAUSE_TEMPLATES) >= 12, f"Expected >= 12 templates, got {len(ADVERBIAL_CLAUSE_TEMPLATES)}"


def test_all_adverbial_templates_available():
    """M3c4: 所有状语从句模板已开放"""
    for t in ADVERBIAL_CLAUSE_TEMPLATES:
        assert t.available is True, f"{t.template_id} should be available=True"


def test_get_available_includes_adverbial():
    """M3c4: get_available_clause_templates 包含状语从句"""
    available = get_available_clause_templates()
    adverbial_count = sum(1 for t in available if t.clause_type == "adverbial")
    assert adverbial_count >= 12, f"Expected >= 12 available adverbial templates, got {adverbial_count}"


def test_adverbial_template_structure():
    """验证状语从句模板结构完整"""
    for t in ADVERBIAL_CLAUSE_TEMPLATES:
        assert t.template_id.startswith("tpl_adv_"), f"Invalid template_id: {t.template_id}"
        assert t.clause_type == "adverbial"
        assert len(t.slots) == 2, f"{t.template_id} should have 2 slots (subject + verb)"
        assert t.slots[0].name == "subject"
        assert t.slots[0].type == "NP"
        assert t.slots[1].name == "verb"
        assert t.slots[1].type == "VP"


def test_reason_adverbial_templates():
    """验证原因状语从句模板（because/since）"""
    because = get_template_by_id("tpl_adv_because")
    since = get_template_by_id("tpl_adv_since")

    assert because is not None
    assert because.semantic_class == "reason"
    assert because.surface == "because <SUBJECT> <VERB>"

    assert since is not None
    assert since.semantic_class == "reason"
    assert since.surface == "since <SUBJECT> <VERB>"


def test_time_adverbial_templates():
    """验证时间状语从句模板（when/while/after/before）"""
    when = get_template_by_id("tpl_adv_when")
    while_t = get_template_by_id("tpl_adv_while")
    after = get_template_by_id("tpl_adv_after")
    before = get_template_by_id("tpl_adv_before")

    assert when is not None
    assert when.semantic_class == "time"

    assert while_t is not None
    assert while_t.semantic_class == "time"

    assert after is not None
    assert after.semantic_class == "time"

    assert before is not None
    assert before.semantic_class == "time"


def test_condition_adverbial_templates():
    """验证条件状语从句模板（if/unless/as_long_as）"""
    if_t = get_template_by_id("tpl_adv_if")
    unless = get_template_by_id("tpl_adv_unless")
    as_long_as = get_template_by_id("tpl_adv_as_long_as")

    assert if_t is not None
    assert if_t.semantic_class == "condition"
    assert if_t.surface == "if <SUBJECT> <VERB>"

    assert unless is not None
    assert unless.semantic_class == "condition"

    assert as_long_as is not None
    assert as_long_as.semantic_class == "condition"
    assert as_long_as.surface == "as long as <SUBJECT> <VERB>"


def test_concession_adverbial_templates():
    """验证让步状语从句模板（although/though/even_though）"""
    although = get_template_by_id("tpl_adv_although")
    though = get_template_by_id("tpl_adv_though")
    even_though = get_template_by_id("tpl_adv_even_though")

    assert although is not None
    assert although.semantic_class == "concession"
    assert although.surface == "although <SUBJECT> <VERB>"

    assert though is not None
    assert though.semantic_class == "concession"

    assert even_though is not None
    assert even_though.semantic_class == "concession"
    assert even_though.surface == "even though <SUBJECT> <VERB>"


# ===================== Realizer 测试 =====================

def test_adverbial_realizer_simple():
    """AdverbialClauseRealizer 简单槽位替换"""
    realizer = AdverbialClauseRealizer()
    template = get_template_by_id("tpl_adv_because")

    slot_values = {
        "subject": "it",
        "verb": "is raining"
    }

    # Mock context
    context = RealizationContext(
        original_sentence="I like this book.",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "because it is raining"


def test_adverbial_realizer_when_clause():
    """when 从句"""
    realizer = AdverbialClauseRealizer()
    template = get_template_by_id("tpl_adv_when")

    slot_values = {
        "subject": "she",
        "verb": "arrives"
    }

    context = RealizationContext(
        original_sentence="Call me.",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "when she arrives"


# ===================== 规则集成测试 =====================

def test_vp_expansion_rules_include_adverbial():
    """VP 扩展规则包含状语从句"""
    vp_rules = get_available_rules_for_phrase("VP")
    assert "adverbial_clause" in vp_rules, "VP rules should include adverbial_clause"
