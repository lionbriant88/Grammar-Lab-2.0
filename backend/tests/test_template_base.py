"""测试 template_base.py (M3c2)"""
import pytest
from grammar_engine.template_base import Slot, TemplateBase, ClauseTemplate


# ===================== Slot Tests =====================

def test_slot_creation():
    """Slot 正常创建"""
    slot = Slot(name="verb", type="VP", required=True)
    assert slot.name == "verb"
    assert slot.type == "VP"
    assert slot.required is True
    assert slot.default is None


def test_slot_with_default():
    """可选 Slot 带默认值"""
    slot = Slot(name="adverb", type="ADV", required=False, default="quickly")
    assert slot.required is False
    assert slot.default == "quickly"


def test_slot_empty_name_raises():
    """Slot name 不能为空"""
    with pytest.raises(ValueError, match="name cannot be empty"):
        Slot(name="", type="VP", required=True)


def test_slot_empty_type_raises():
    """Slot type 不能为空"""
    with pytest.raises(ValueError, match="type cannot be empty"):
        Slot(name="verb", type="", required=True)


def test_slot_optional_without_default_raises():
    """可选 Slot 必须有默认值"""
    with pytest.raises(ValueError, match="must have a default value"):
        Slot(name="adverb", type="ADV", required=False)


# ===================== ClauseTemplate Tests =====================

def test_clause_template_creation():
    """ClauseTemplate 正常创建"""
    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)],
        available=False
    )

    assert template.template_id == "tpl_rel_who_verb"
    assert template.clause_type == "relative"
    assert template.surface == "who <VERB>"
    assert len(template.slots) == 1
    assert template.available is False


def test_clause_template_invalid_type_raises():
    """clause_type 必须是 relative/adverbial/noun"""
    with pytest.raises(ValueError, match="Invalid clause_type"):
        ClauseTemplate(
            template_id="tpl_invalid",
            clause_type="invalid_type",  # type: ignore
            surface="test"
        )


def test_clause_template_empty_template_id_raises():
    """template_id 不能为空"""
    with pytest.raises(ValueError, match="template_id cannot be empty"):
        ClauseTemplate(
            template_id="",
            clause_type="relative",
            surface="who <VERB>"
        )


def test_clause_template_empty_surface_raises():
    """surface 不能为空"""
    with pytest.raises(ValueError, match="surface cannot be empty"):
        ClauseTemplate(
            template_id="tpl_test",
            clause_type="relative",
            surface=""
        )


def test_clause_template_duplicate_slot_names_raises():
    """槽位名称必须唯一"""
    with pytest.raises(ValueError, match="Slot names must be unique"):
        ClauseTemplate(
            template_id="tpl_test",
            clause_type="relative",
            surface="test",
            slots=[
                Slot(name="verb", type="VP", required=True),
                Slot(name="verb", type="VP", required=True),  # 重复
            ]
        )


def test_get_required_slots():
    """获取必填槽位"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB> <ADV>",
        slots=[
            Slot(name="verb", type="VP", required=True),
            Slot(name="adv", type="ADV", required=False, default="quickly"),
        ]
    )

    required = template.get_required_slots()
    assert len(required) == 1
    assert required[0].name == "verb"


def test_get_optional_slots():
    """获取可选槽位"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB> <ADV>",
        slots=[
            Slot(name="verb", type="VP", required=True),
            Slot(name="adv", type="ADV", required=False, default="quickly"),
        ]
    )

    optional = template.get_optional_slots()
    assert len(optional) == 1
    assert optional[0].name == "adv"


def test_validate_slot_values_success():
    """槽位值验证通过"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)]
    )

    errors = template.validate_slot_values({"verb": "runs"})
    assert errors == []


def test_validate_slot_values_missing_required():
    """槽位值验证失败（缺少必填）"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)]
    )

    errors = template.validate_slot_values({})
    assert len(errors) == 1
    assert "verb" in errors[0]
    assert "missing" in errors[0].lower()


def test_get_preview_returns_surface():
    """M3c2: get_preview 返回 surface（简化版）"""
    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>"
    )

    preview = template.get_preview()
    assert preview == "who <VERB>"


def test_clause_template_with_constraints():
    """ClauseTemplate 带约束条件"""
    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        constraints={"antecedent_type": "person"}
    )

    assert template.constraints["antecedent_type"] == "person"


def test_clause_template_with_semantic_class():
    """ClauseTemplate 带语义类别"""
    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        semantic_class="person"
    )

    assert template.semantic_class == "person"
