"""M3c5 名词性从句测试"""
import pytest
from grammar_engine.clause_templates import (
    NOUN_CLAUSE_TEMPLATES,
    get_available_clause_templates,
    get_template_by_id,
)
from grammar_engine.clause_realizer import NounClauseRealizer, RealizationContext
from grammar_engine.expansion_rules import get_available_rules_for_phrase


# ===================== 模板定义测试 =====================

def test_noun_templates_count():
    """M3c5: 名词性从句模板数量 >= 10"""
    assert len(NOUN_CLAUSE_TEMPLATES) >= 10, f"Expected >= 10 templates, got {len(NOUN_CLAUSE_TEMPLATES)}"


def test_all_noun_templates_available():
    """M3c5: 所有名词性从句模板已开放"""
    for t in NOUN_CLAUSE_TEMPLATES:
        assert t.available is True, f"{t.template_id} should be available=True"


def test_get_available_includes_noun():
    """M3c5: get_available_clause_templates 包含名词性从句"""
    available = get_available_clause_templates()
    noun_count = sum(1 for t in available if t.clause_type == "noun")
    assert noun_count >= 10, f"Expected >= 10 available noun templates, got {noun_count}"


def test_noun_template_structure():
    """验证名词性从句模板结构完整"""
    for t in NOUN_CLAUSE_TEMPLATES:
        assert t.template_id.startswith("tpl_noun_"), f"Invalid template_id: {t.template_id}"
        assert t.clause_type == "noun"
        assert len(t.slots) > 0, f"{t.template_id} should have slots"
        # who 只有 1 个 verb 槽位，其他都有 2 个（subject + verb）
        if t.template_id == "tpl_noun_who":
            assert len(t.slots) == 1
            assert t.slots[0].name == "verb"
        else:
            assert len(t.slots) == 2
            assert t.slots[0].name == "subject"
            assert t.slots[1].name == "verb"


def test_object_clause_templates():
    """验证宾语从句模板（that/whether/if/what）"""
    that = get_template_by_id("tpl_noun_that")
    whether = get_template_by_id("tpl_noun_whether")
    if_t = get_template_by_id("tpl_noun_if")
    what = get_template_by_id("tpl_noun_what")

    assert that is not None
    assert that.semantic_class == "statement"
    assert that.surface == "that <SUBJECT> <VERB>"

    assert whether is not None
    assert whether.semantic_class == "question"
    assert whether.surface == "whether <SUBJECT> <VERB>"

    assert if_t is not None
    assert if_t.semantic_class == "question"

    assert what is not None
    assert what.semantic_class == "question"


def test_wh_clause_templates():
    """验证疑问词引导从句模板（how/why/where/when/who/which）"""
    how = get_template_by_id("tpl_noun_how")
    why = get_template_by_id("tpl_noun_why")
    where = get_template_by_id("tpl_noun_where")
    when = get_template_by_id("tpl_noun_when")
    who = get_template_by_id("tpl_noun_who")
    which = get_template_by_id("tpl_noun_which")

    assert how is not None
    assert how.semantic_class == "manner"

    assert why is not None
    assert why.semantic_class == "reason"

    assert where is not None
    assert where.semantic_class == "place"

    assert when is not None
    assert when.semantic_class == "time"

    assert who is not None
    assert who.semantic_class == "person"
    assert who.surface == "who <VERB>"  # 只有 verb 槽位

    assert which is not None
    assert which.semantic_class == "choice"


# ===================== Realizer 测试 =====================

def test_noun_realizer_simple():
    """NounClauseRealizer 简单槽位替换"""
    realizer = NounClauseRealizer()
    template = get_template_by_id("tpl_noun_that")

    slot_values = {
        "subject": "he",
        "verb": "is right"
    }

    # Mock context
    context = RealizationContext(
        original_sentence="I think.",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "that he is right"


def test_noun_realizer_who_clause():
    """who 从句（只有 verb 槽位）"""
    realizer = NounClauseRealizer()
    template = get_template_by_id("tpl_noun_who")

    slot_values = {
        "verb": "did it"
    }

    context = RealizationContext(
        original_sentence="I know.",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    result = realizer.realize(template, slot_values, context)
    assert result == "who did it"


# ===================== 规则集成测试 =====================

def test_vp_expansion_rules_include_noun():
    """VP 扩展规则包含名词性从句"""
    vp_rules = get_available_rules_for_phrase("VP")
    assert "noun_clause" in vp_rules, "VP rules should include noun_clause"
