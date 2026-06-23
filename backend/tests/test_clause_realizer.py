"""测试 clause_realizer.py (M3c2)"""
import pytest
from grammar_engine.clause_realizer import (
    RealizationContext,
    ClauseRealizer,
    RelativeClauseRealizer,
    AdverbialClauseRealizer,
    NounClauseRealizer,
    get_realizer,
)
from grammar_engine.template_base import ClauseTemplate, Slot
from grammar_engine.phrase_segmenter import PhraseNode


# ===================== RealizationContext Tests =====================

def test_realization_context_creation():
    """RealizationContext 正常创建"""
    phrase = PhraseNode(
        id="p1",
        type="NP",
        text="the dog",
        head_token_text="dog",
        head_pos="NOUN",
        syntactic_role="subject",
        span=(0, 7),
        features={},
        parent_id=None,
        children_ids=[],
        is_expandable=True,
        candidates=[]
    )

    context = RealizationContext(
        original_sentence="The dog runs.",
        doc=None,  # Mock
        phrases=[phrase],
        target_phrase_id="p1"
    )

    assert context.original_sentence == "The dog runs."
    assert len(context.phrases) == 1
    assert context.target_phrase_id == "p1"


def test_get_phrase_by_id():
    """get_phrase_by_id 正确查找短语"""
    p1 = PhraseNode(
        id="p1", type="NP", text="dog", head_token_text="dog",
        head_pos="NOUN", syntactic_role="subject", span=(0, 3),
        features={}, parent_id=None, children_ids=[],
        is_expandable=True, candidates=[]
    )
    p2 = PhraseNode(
        id="p2", type="VP", text="runs", head_token_text="runs",
        head_pos="VERB", syntactic_role="predicate", span=(4, 8),
        features={}, parent_id=None, children_ids=[],
        is_expandable=False, candidates=[]
    )

    context = RealizationContext(
        original_sentence="dog runs",
        doc=None,
        phrases=[p1, p2],
        target_phrase_id="p1"
    )

    assert context.get_phrase_by_id("p1") == p1
    assert context.get_phrase_by_id("p2") == p2
    assert context.get_phrase_by_id("p999") is None


def test_get_target_phrase():
    """get_target_phrase 返回目标短语"""
    p1 = PhraseNode(
        id="p1", type="NP", text="dog", head_token_text="dog",
        head_pos="NOUN", syntactic_role="subject", span=(0, 3),
        features={}, parent_id=None, children_ids=[],
        is_expandable=True, candidates=[]
    )

    context = RealizationContext(
        original_sentence="dog runs",
        doc=None,
        phrases=[p1],
        target_phrase_id="p1"
    )

    assert context.get_target_phrase() == p1


# ===================== ClauseRealizer Tests =====================

def test_replace_slots():
    """_replace_slots 正确替换槽位"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB> <ADV>",
        slots=[
            Slot(name="verb", type="VP", required=True),
            Slot(name="adv", type="ADV", required=False, default="quickly"),
        ]
    )

    realizer = RelativeClauseRealizer()
    result = realizer._replace_slots(template, {"verb": "runs", "adv": "fast"})

    assert result == "who runs fast"


def test_replace_slots_with_default():
    """_replace_slots 使用默认值"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB> <ADV>",
        slots=[
            Slot(name="verb", type="VP", required=True),
            Slot(name="adv", type="ADV", required=False, default="quickly"),
        ]
    )

    realizer = RelativeClauseRealizer()
    result = realizer._replace_slots(template, {"verb": "runs"})

    assert result == "who runs quickly"


def test_validate_constraints_empty():
    """_validate_constraints 返回空列表（M3c2 占位）"""
    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB>"
    )

    context = RealizationContext(
        original_sentence="test",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    realizer = RelativeClauseRealizer()
    errors = realizer._validate_constraints(template, context)

    assert errors == []


# ===================== RelativeClauseRealizer Tests =====================

def test_relative_clause_realize():
    """RelativeClauseRealizer.realize 正确实现（M3c3: 需要先行词）"""
    from grammar_engine.phrase_segmenter import PhraseNode

    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)],
        constraints={"antecedent_type": "any"}  # M3c3: 添加约束（any = 不限制）
    )

    # M3c3: 提供有效的先行词
    antecedent = PhraseNode(
        id="p1", type="NP", text="the dog",
        head_token_text="dog", head_pos="NOUN",
        syntactic_role="subject", span=(0, 2),
        features={"head_lemma": "dog"}
    )

    context = RealizationContext(
        original_sentence="The dog runs.",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    realizer = RelativeClauseRealizer()
    result = realizer.realize(template, {"verb": "runs fast"}, context)

    assert result == "who runs fast"


def test_relative_clause_realize_missing_required_slot():
    """RelativeClauseRealizer.realize 缺少必填槽位时抛出异常"""
    from grammar_engine.phrase_segmenter import PhraseNode

    template = ClauseTemplate(
        template_id="tpl_test",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)],
        constraints={"antecedent_type": "any"}  # M3c3: 添加约束
    )

    # M3c3: 提供先行词
    antecedent = PhraseNode(
        id="p1", type="NP", text="test",
        head_token_text="test", head_pos="NOUN",
        syntactic_role="subject", span=(0, 1),
        features={"head_lemma": "test"}
    )

    context = RealizationContext(
        original_sentence="test",
        doc=None,
        phrases=[antecedent],
        target_phrase_id="p1"
    )

    realizer = RelativeClauseRealizer()

    with pytest.raises(ValueError, match="Invalid slot values"):
        realizer.realize(template, {}, context)


# ===================== AdverbialClauseRealizer Tests =====================

def test_adverbial_clause_realize():
    """AdverbialClauseRealizer.realize 正确实现"""
    template = ClauseTemplate(
        template_id="tpl_adv_because",
        clause_type="adverbial",
        surface="because <CLAUSE>",
        slots=[Slot(name="clause", type="CLAUSE", required=True)]
    )

    context = RealizationContext(
        original_sentence="test",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    realizer = AdverbialClauseRealizer()
    result = realizer.realize(template, {"clause": "he is tired"}, context)

    assert result == "because he is tired"


# ===================== NounClauseRealizer Tests =====================

def test_noun_clause_realize():
    """NounClauseRealizer.realize 正确实现"""
    template = ClauseTemplate(
        template_id="tpl_noun_that",
        clause_type="noun",
        surface="that <CLAUSE>",
        slots=[Slot(name="clause", type="CLAUSE", required=True)]
    )

    context = RealizationContext(
        original_sentence="test",
        doc=None,
        phrases=[],
        target_phrase_id="p1"
    )

    realizer = NounClauseRealizer()
    result = realizer.realize(template, {"clause": "he is smart"}, context)

    assert result == "that he is smart"


# ===================== Factory Function Tests =====================

def test_get_realizer_relative():
    """get_realizer 返回 RelativeClauseRealizer"""
    realizer = get_realizer("relative")
    assert isinstance(realizer, RelativeClauseRealizer)


def test_get_realizer_adverbial():
    """get_realizer 返回 AdverbialClauseRealizer"""
    realizer = get_realizer("adverbial")
    assert isinstance(realizer, AdverbialClauseRealizer)


def test_get_realizer_noun():
    """get_realizer 返回 NounClauseRealizer"""
    realizer = get_realizer("noun")
    assert isinstance(realizer, NounClauseRealizer)


def test_get_realizer_unknown_type():
    """get_realizer 未知类型时抛出异常"""
    with pytest.raises(ValueError, match="Unknown clause type"):
        get_realizer("invalid_type")
