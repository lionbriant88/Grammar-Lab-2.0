"""测试 expansion_engine 与 ClauseTemplate 集成 (M3c2)"""
import pytest
from grammar_engine.expansion_engine import apply_template
from grammar_engine.template_base import ClauseTemplate, Slot
from grammar_engine.phrase_segmenter import PhraseNode


def test_apply_template_with_clause_template_placeholder():
    """M3c2: apply_template 识别 ClauseTemplate（占位返回原句）"""
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

    template = ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        slots=[Slot(name="verb", type="VP", required=True)]
    )

    sentence = "The dog runs."

    # M3c2: ClauseTemplate 占位，返回原句不变
    result = apply_template(phrase, template, sentence)

    assert result == sentence  # M3c2 占位行为


def test_apply_template_with_word_template_still_works():
    """M3c2: WordTemplate (adjective/adverb/number) 仍然正常工作"""
    from grammar_engine.expansion_templates import get_template_by_id

    phrase = PhraseNode(
        id="p1",
        type="NP",
        text="dogs",
        head_token_text="dogs",
        head_pos="NOUN",
        syntactic_role="object",
        span=(0, 4),
        features={},
        parent_id=None,
        children_ids=[],
        is_expandable=True,
        candidates=[]
    )

    template = get_template_by_id("tpl_adj_cute")

    sentence = "dogs"

    result = apply_template(phrase, template, sentence)

    # WordTemplate 正常工作
    assert "cute" in result
