"""M3a 句扩展引擎单元测试(11 项)。

覆盖 spec §5.1:
  1.  规则库完整性
  2.  短语识别 - 基础(I like dogs. → 3 短语 + 特征槽)
  3.  VP 完整时态链(调整 2):has been working / would like / to help 不在 VP
  4.  PP 挂载(调整 1):in the park → parent_id=NP(the dog)
  5.  模板填充
  6.  Engine 入口(I like dogs. → NP(dogs) 可扩展 + 候选;NP(I) 不可扩展)
  7.  Validator 主谓一致(4 case)
  8.  Validator 占位接口齐全(4 函数可调 + 返回 PASS)
  9.  严禁项回归(I beautiful like dogs. → VP 候选不含 adjective)
  10. spaCy 不可用降级
  11. L2/L3 元数据(level/available)
"""
import pytest

from grammar_engine.nlp_loader import nlp_loader
from grammar_engine import expansion_rules as rules
from grammar_engine import expansion_templates as templates
from grammar_engine import expansion_validator as validator
from grammar_engine import expansion_engine as engine
from grammar_engine.phrase_segmenter import segment


# 共享 nlp 实例(session 级)
_nlp = None


def nlp():
    global _nlp
    if _nlp is None:
        _nlp = nlp_loader.get()
    return _nlp


# ----------------------------- 1. 规则库完整性 -----------------------------

def test_rule_completeness():
    """所有 L1 ExpansionKind 都应在 get_rules_for_phrase 输出里。"""
    np_rules = rules.get_rules_for_phrase("NP")
    assert "adjective" in np_rules
    assert "number" in np_rules

    vp_rules = rules.get_rules_for_phrase("VP")
    assert "adverb" in vp_rules

    adjp_rules = rules.get_rules_for_phrase("ADJP")
    assert "degree_adverb" in adjp_rules

    # L1 已开放 kind 数量正确
    np_avail = rules.get_available_rules_for_phrase("NP")
    assert set(np_avail) == {"adjective", "number"}
    vp_avail = rules.get_available_rules_for_phrase("VP")
    assert vp_avail == ["adverb"]


# ----------------------------- 2. 短语识别 - 基础 -----------------------------

def test_segment_basic():
    """segment(I like dogs.) → 3 个短语 + 特征槽正确。"""
    phrases = segment(nlp()("I like dogs."))
    by_role = {p.syntactic_role: p for p in phrases}

    # 3 个短语:subject NP / predicate VP / object NP
    assert len(phrases) == 3
    subj = by_role["subject"]
    pred = by_role["predicate"]
    obj = by_role["object"]

    assert subj.type == "NP" and subj.head_token_text == "I"
    assert subj.features["number"] == "singular"
    assert subj.features["person"] == 1

    assert pred.type == "VP" and pred.head_token_text == "like"
    assert pred.features["tense"] == "simple_present"
    assert pred.features["modal"] is None

    assert obj.type == "NP" and obj.head_token_text == "dogs"
    assert obj.features["number"] == "plural"
    assert obj.features["person"] == 3


# ----------------------------- 3. VP 完整时态链(调整 2) -----------------------------

def test_vp_tense_chain_perfect_progressive():
    """has been working → 一个 VP,aux_chain=[has,been],tense=present_perfect_progressive。"""
    phrases = segment(nlp()("He has been working hard."))
    vps = [p for p in phrases if p.type == "VP"]
    assert len(vps) == 1
    vp = vps[0]
    assert "has" in vp.text and "been" in vp.text and "working" in vp.text
    assert vp.features["aux_chain"] == ["has", "been"]
    assert vp.features["tense"] == "present_perfect_progressive"


def test_vp_tense_chain_modal():
    """would like → 一个 VP,modal='would';to help 不在 VP 内。"""
    phrases = segment(nlp()("She would like to help."))
    vps = [p for p in phrases if p.type == "VP"]
    assert len(vps) >= 1
    # 找到以 like 为中心词的 VP
    like_vp = next((v for v in vps if v.head_token_text == "like"), None)
    assert like_vp is not None
    assert like_vp.features["modal"] == "would"
    # to help 不应在 VP 文本里(xcomp,留 M3b)
    assert "help" not in like_vp.text


# ----------------------------- 4. PP 挂载(调整 1) -----------------------------

def test_pp_attachment():
    """in the park 的 parent_id 指向 NP(the dog),非 None 漂浮。"""
    phrases = segment(nlp()("likes the dog in the park"))
    pps = [p for p in phrases if p.type == "PP"]
    assert len(pps) >= 1
    pp = pps[0]
    assert "in the park" in pp.text
    assert pp.parent_id is not None, "PP 应挂载到 NP,不能顶层漂浮"

    # parent_id 指向的应是 NP(the dog)
    parent = next((p for p in phrases if p.id == pp.parent_id), None)
    assert parent is not None
    assert parent.type == "NP"
    assert "dog" in parent.text
    # 父 NP 的 children_ids 含该 PP
    assert pp.id in parent.children_ids


# ----------------------------- 5. 模板填充 -----------------------------

def test_templates():
    """get_templates_for_kind('adjective') 返回 7 个,preview 合理。"""
    adjs = templates.get_templates_for_kind("adjective")
    assert len(adjs) == 7
    for tpl in adjs:
        # surface + example_anchor 拼出合理短语(非空)
        assert tpl.surface and tpl.example_anchor
        preview = tpl.preview()
        assert tpl.surface in preview

    # 全部 L1 模板总数 = 20
    total = sum(
        len(templates.get_templates_for_kind(k))
        for k in ("adjective", "adverb", "number", "degree_adverb")
    )
    assert total == 20

    # 按 id 查
    t = templates.get_template_by_id("tpl_adj_cute")
    assert t is not None and t.surface == "cute"


# ----------------------------- 6. Engine 入口 -----------------------------

def test_engine_analyze():
    """analyze(I like dogs.) → 3 phrases;NP(dogs) 可扩展(adj+number);NP(I) 不可扩展。"""
    result = engine.analyze("I like dogs.")
    assert result["sentence"] == "I like dogs."
    assert len(result["phrases"]) == 3

    by_role = {p.syntactic_role: p for p in result["phrases"]}

    # NP(dogs) 可扩展,2 个 candidate(adj / number),各带模板
    obj = by_role["object"]
    assert obj.is_expandable is True
    cand_kinds = [c["kind"] for c in obj.candidates]
    assert "adjective" in cand_kinds and "number" in cand_kinds
    adj_cand = next(c for c in obj.candidates if c["kind"] == "adjective")
    assert len(adj_cand["templates"]) == 7
    # 预览锚到实际中心词 dogs
    assert all("dogs" in t["preview"] for t in adj_cand["templates"])

    # VP(like) 可扩展,1 个 candidate(adverb)
    pred = by_role["predicate"]
    assert pred.is_expandable is True
    assert [c["kind"] for c in pred.candidates] == ["adverb"]

    # NP(I) 代词作 NP,不可扩展
    subj = by_role["subject"]
    assert subj.is_expandable is False
    assert subj.candidates == []


# ----------------------------- 7. Validator 主谓一致(4 case) -----------------------------

def _validate(sentence):
    """helper:analyze + validate,返回 ValidationReport。"""
    from grammar_engine.nlp_loader import nlp_loader
    doc = nlp_loader.get()(sentence)
    phrases = engine.analyze(sentence)["phrases"]
    return validator.validate(sentence, doc, phrases)


def test_validator_subject_verb_agreement_invalid():
    """He like dogs. → invalid,auto_corrections 含 like→likes。"""
    rep = _validate("He like dogs.")
    assert rep.is_valid is False
    corr = next((c for c in rep.auto_corrections if c["from"] == "like"), None)
    assert corr is not None and corr["to"] == "likes"


def test_validator_subject_verb_agreement_valid_first_person():
    """I like dogs. → valid(1sg,不触发)。"""
    rep = _validate("I like dogs.")
    assert rep.is_valid is True
    assert rep.auto_corrections == []


def test_validator_subject_verb_agreement_valid_third_plural():
    """They like dogs. → valid(3pl,不触发)。"""
    rep = _validate("They like dogs.")
    assert rep.is_valid is True
    assert rep.auto_corrections == []


def test_validator_subject_verb_agreement_valid_non_present():
    """She has been running. → valid(非 simple_present,不触发)。"""
    rep = _validate("She has been running.")
    assert rep.is_valid is True
    assert rep.auto_corrections == []


# ----------------------------- 8. Validator 占位接口齐全 -----------------------------

def test_validator_placeholders_callable():
    """4 个占位函数可调用且返回 is_valid=True(M3b/c 填实现)。"""
    from grammar_engine.nlp_loader import nlp_loader
    doc = nlp_loader.get()("I like dogs.")
    phrases = engine.analyze("I like dogs.")["phrases"]

    for fn in (
        validator.validate_tense_consistency,
        validator.validate_clause_completeness,
        validator.validate_non_finite_legality,
        validator.validate_relative_pronoun_match,
    ):
        rep = fn("I like dogs.", doc, phrases)
        assert rep.is_valid is True
        assert rep.auto_corrections == []


# ----------------------------- 9. 严禁项回归 -----------------------------

def test_forbidden_adjective_before_verb():
    """I beautiful like dogs. → VP 候选不含 adjective(严禁项 #1)。"""
    result = engine.analyze("I beautiful like dogs.")
    for p in result["phrases"]:
        if p.type == "VP":
            kinds = [c["kind"] for c in p.candidates]
            assert "adjective" not in kinds, "VP 不应推荐形容词(动词前加形容词是严禁项)"


# ----------------------------- 10. spaCy 不可用降级 -----------------------------

def test_spacy_unavailable_graceful(monkeypatch):
    """mock nlp_loader 失败 → Engine 返回 warnings + 空 phrases,不抛异常。"""
    def _fail():
        raise RuntimeError("model not loaded")

    monkeypatch.setattr(engine.nlp_loader, "get", _fail)
    result = engine.analyze("I like dogs.")
    assert result["phrases"] == []
    assert any("spaCy model unavailable" in w for w in result["warnings"])


# ----------------------------- 11. L2/L3 元数据 -----------------------------

def test_kind_metadata_l2_l3():
    """get_kind_metadata('relative_clause') → level=3, available=False。"""
    meta = rules.get_kind_metadata("relative_clause")
    assert meta["level"] == 3
    assert meta["available"] is False

    meta2 = rules.get_kind_metadata("prepositional_phrase")
    assert meta2["level"] == 2
    assert meta2["available"] is False

    # L1 应 available=True
    assert rules.get_kind_metadata("adjective")["available"] is True
