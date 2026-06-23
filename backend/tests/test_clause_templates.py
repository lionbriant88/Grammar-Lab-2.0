"""测试 clause_templates.py (M3c2 -> M3c3 更新)"""
import pytest
from grammar_engine.clause_templates import (
    RELATIVE_CLAUSE_TEMPLATES,
    ADVERBIAL_CLAUSE_TEMPLATES,
    NOUN_CLAUSE_TEMPLATES,
    ALL_CLAUSE_TEMPLATES,
    get_clause_templates_by_type,
    get_available_clause_templates,
    get_template_by_id,
)


# ===================== 定语从句模板测试 =====================

def test_relative_clause_templates_count():
    """定语从句模板数量（M3c3: 10个）"""
    assert len(RELATIVE_CLAUSE_TEMPLATES) >= 10


def test_relative_clause_who_template():
    """who + verb 模板"""
    template = RELATIVE_CLAUSE_TEMPLATES[0]

    assert template.template_id == "tpl_rel_who_subj"
    assert template.clause_type == "relative"
    assert template.surface == "who <VERB>"
    assert len(template.slots) == 1
    assert template.slots[0].name == "verb"
    assert template.slots[0].type == "VP"
    assert template.constraints["antecedent_type"] == "person"
    assert template.semantic_class == "person"
    assert template.available is True  # M3c3 开放


def test_relative_clause_which_template():
    """which + verb 模板"""
    template = RELATIVE_CLAUSE_TEMPLATES[1]

    assert template.template_id == "tpl_rel_which_subj"
    assert template.clause_type == "relative"
    assert template.surface == "which <VERB>"
    assert template.constraints["antecedent_type"] == "thing"
    assert template.semantic_class == "thing"
    assert template.available is True  # M3c3 开放


# ===================== 状语从句模板测试 =====================

def test_adverbial_clause_templates_count():
    """状语从句模板数量（M3c2: 2个占位）"""
    assert len(ADVERBIAL_CLAUSE_TEMPLATES) == 2


def test_adverbial_clause_because_template():
    """because + clause 模板"""
    template = ADVERBIAL_CLAUSE_TEMPLATES[0]

    assert template.template_id == "tpl_adv_because"
    assert template.clause_type == "adverbial"
    assert template.surface == "because <CLAUSE>"
    assert len(template.slots) == 1
    assert template.slots[0].name == "clause"
    assert template.slots[0].type == "CLAUSE"
    assert template.constraints["position"] == "end"
    assert template.semantic_class == "reason"
    assert template.available is False


def test_adverbial_clause_when_template():
    """when + clause 模板"""
    template = ADVERBIAL_CLAUSE_TEMPLATES[1]

    assert template.template_id == "tpl_adv_when"
    assert template.clause_type == "adverbial"
    assert template.surface == "when <CLAUSE>"
    assert template.constraints["position"] == "flexible"
    assert template.semantic_class == "time"
    assert template.available is False


# ===================== 名词性从句模板测试 =====================

def test_noun_clause_templates_count():
    """名词性从句模板数量（M3c2: 2个占位）"""
    assert len(NOUN_CLAUSE_TEMPLATES) == 2


def test_noun_clause_that_template():
    """that + clause 模板"""
    template = NOUN_CLAUSE_TEMPLATES[0]

    assert template.template_id == "tpl_noun_that"
    assert template.clause_type == "noun"
    assert template.surface == "that <CLAUSE>"
    assert len(template.slots) == 1
    assert template.slots[0].name == "clause"
    assert template.constraints["function"] == "object"
    assert template.semantic_class == "statement"
    assert template.available is False


def test_noun_clause_whether_template():
    """whether + clause 模板"""
    template = NOUN_CLAUSE_TEMPLATES[1]

    assert template.template_id == "tpl_noun_whether"
    assert template.clause_type == "noun"
    assert template.surface == "whether <CLAUSE>"
    assert template.constraints["function"] == "object"
    assert template.semantic_class == "question"
    assert template.available is False


# ===================== 统一接口测试 =====================

def test_all_clause_templates_count():
    """ALL_CLAUSE_TEMPLATES 包含所有模板（M3c3: 14个）"""
    assert len(ALL_CLAUSE_TEMPLATES) == 14  # M3c3: 10 relative + 2 adverbial + 2 noun


def test_all_clause_templates_unique_ids():
    """所有模板 ID 唯一"""
    template_ids = [t.template_id for t in ALL_CLAUSE_TEMPLATES]
    assert len(template_ids) == len(set(template_ids))


def test_get_clause_templates_by_type_relative():
    """get_clause_templates_by_type 返回定语从句模板"""
    templates = get_clause_templates_by_type("relative")
    assert templates == RELATIVE_CLAUSE_TEMPLATES


def test_get_clause_templates_by_type_adverbial():
    """get_clause_templates_by_type 返回状语从句模板"""
    templates = get_clause_templates_by_type("adverbial")
    assert templates == ADVERBIAL_CLAUSE_TEMPLATES


def test_get_clause_templates_by_type_noun():
    """get_clause_templates_by_type 返回名词性从句模板"""
    templates = get_clause_templates_by_type("noun")
    assert templates == NOUN_CLAUSE_TEMPLATES


def test_get_clause_templates_by_type_invalid():
    """get_clause_templates_by_type 未知类型抛出异常"""
    with pytest.raises(ValueError, match="Unknown clause type"):
        get_clause_templates_by_type("invalid_type")


def test_get_available_clause_templates_empty():
    """M3c3: get_available_clause_templates 返回定语从句10个"""
    available = get_available_clause_templates()
    assert len(available) == 10  # M3c3: 定语从句已开放


def test_get_template_by_id_found():
    """get_template_by_id 找到模板（M3c3: 使用新ID）"""
    template = get_template_by_id("tpl_rel_who_subj")

    assert template is not None
    assert template.template_id == "tpl_rel_who_subj"


def test_get_template_by_id_not_found():
    """get_template_by_id 未找到返回 None"""
    template = get_template_by_id("tpl_nonexistent")

    assert template is None


# ===================== 模板一致性测试 =====================

def test_all_templates_have_unique_ids():
    """所有模板 ID 唯一"""
    ids = [t.template_id for t in ALL_CLAUSE_TEMPLATES]
    assert len(ids) == len(set(ids)), "Duplicate template IDs found"


def test_all_templates_have_valid_clause_type():
    """所有模板的 clause_type 有效"""
    valid_types = {"relative", "adverbial", "noun"}
    for template in ALL_CLAUSE_TEMPLATES:
        assert template.clause_type in valid_types


def test_all_templates_have_surface():
    """所有模板都有 surface"""
    for template in ALL_CLAUSE_TEMPLATES:
        assert template.surface
        assert len(template.surface) > 0


def test_all_templates_m3c2_not_available():
    """M3c3: 定语从句已开放，状语/名词性从句仍为 False"""
    for template in ALL_CLAUSE_TEMPLATES:
        if template.clause_type == "relative":
            assert template.available is True, f"{template.template_id} should be available in M3c3"
        else:
            assert template.available is False, f"{template.template_id} should not be available yet (M3c4/M3c5)"
