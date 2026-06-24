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

    # L1 已开放 kind 数量正确（M3c4: VP 包含 adverb + adverbial_clause）
    np_avail = rules.get_available_rules_for_phrase("NP")
    assert set(np_avail) == {"adjective", "number", "relative_clause"}
    vp_avail = rules.get_available_rules_for_phrase("VP")
    assert set(vp_avail) == {"adverb", "adverbial_clause"}


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
    # M3c4: VP 的 candidates 包含 adverb + adverbial_clause
    assert set(c["kind"] for c in pred.candidates) == {"adverb", "adverbial_clause"}

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
    """He like dogs. → severity=WARNING(auto_corrections 含 like→likes),is_valid=True(非阻断)。"""
    rep = _validate("He like dogs.")
    assert rep.severity == "WARNING"
    assert rep.is_valid is True  # M3a+1:WARNING 非 ERROR → True(非阻断)
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
    """get_kind_metadata('relative_clause') → level=3, available=True (M3c3)。"""
    meta = rules.get_kind_metadata("relative_clause")
    assert meta["level"] == 3
    assert meta["available"] is True  # M3c3: 定语从句已开放

    meta2 = rules.get_kind_metadata("prepositional_phrase")
    assert meta2["level"] == 2
    assert meta2["available"] is False

    # L1 应 available=True
    assert rules.get_kind_metadata("adjective")["available"] is True


# ----------------------------- M3a+1.1 apply_template -----------------------------

def test_apply_template_adjective_to_np():
    """apply_template 给 NP 套形容词 — 插到 head 之前。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("I like the dogs.")
    phrases = segment(doc)
    np_dogs = next(p for p in phrases if p.type == "NP" and "dogs" in p.text)
    tpl = get_template_by_id("tpl_adj_cute")

    new_sentence = apply_template(np_dogs, tpl, "I like the dogs.")
    assert new_sentence == "I like the cute dogs."


def test_apply_template_number_replaces_a():
    """apply_template 给 NP 套 number — 替换 a/an 限定词。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("I saw a dog.")
    phrases = segment(doc)
    np_dog = next(p for p in phrases if p.type == "NP" and "dog" in p.text)
    tpl = get_template_by_id("tpl_num_two")

    new_sentence = apply_template(np_dog, tpl, "I saw a dog.")
    assert new_sentence == "I saw two dogs."


def test_apply_template_number_no_determiner():
    """apply_template 给 NP 套 number — 没有 a/an 时只插在 head 前。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("I like the dogs.")
    phrases = segment(doc)
    np_dogs = next(p for p in phrases if p.type == "NP" and "dogs" in p.text)
    tpl = get_template_by_id("tpl_num_two")

    new_sentence = apply_template(np_dogs, tpl, "I like the dogs.")
    assert new_sentence == "I like the two dogs."


def test_apply_template_adverb_simple_vp():
    """apply_template 给简单 VP 套副词 — 插到 main verb 前。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("He likes dogs.")
    phrases = segment(doc)
    vp = next(p for p in phrases if p.type == "VP")
    tpl = get_template_by_id("tpl_adv_really")

    new_sentence = apply_template(vp, tpl, "He likes dogs.")
    assert new_sentence == "He really likes dogs."


def test_apply_template_adverb_after_modal():
    """apply_template 给带 modal 的 VP 套副词 — 插到 modal 后、main verb 前。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("She would like it.")
    phrases = segment(doc)
    vp_like = next(p for p in phrases if p.type == "VP" and p.head_token_text == "like")
    tpl = get_template_by_id("tpl_adv_really")

    new_sentence = apply_template(vp_like, tpl, "She would like it.")
    assert new_sentence == "She would really like it."


def test_apply_template_degree_adverb_to_adjp():
    """apply_template 给 ADJP 套 degree_adverb — 插到 head 前。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.expansion_templates import get_template_by_id
    from grammar_engine.phrase_segmenter import segment
    from grammar_engine.nlp_loader import nlp_loader

    doc = nlp_loader.get()("The dog is cute.")
    phrases = segment(doc)
    # M3a 暂未实现 ADJP 短语识别,可能识别为 ADJP=None
    # 若识别不出 ADJP,改测其他方式
    # 此测试先跳过,任务 5 再补 — 但若 ADJP 已识别则通过
    adjp = next((p for p in phrases if p.type == "ADJP"), None)
    if adjp is None:
        pytest.skip("M3a ADJP 识别未实现,任务 5 边界测试暂跳过")
    tpl = get_template_by_id("tpl_dadv_very")
    new_sentence = apply_template(adjp, tpl, "The dog is cute.")
    assert new_sentence == "The dog is very cute."


def test_apply_template_degree_adverb_unit():
    """unit 测试:apply_template 对 degree_adverb kind 的拼接(模拟 head 文本)。"""
    from grammar_engine.expansion_engine import apply_template
    from grammar_engine.phrase_segmenter import PhraseNode
    from grammar_engine.expansion_templates import Template

    # 模拟 ADJP 节点
    fake_phrase = PhraseNode(
        id="fake", type="ADJP", text="cute", head_token_text="cute",
        head_pos="ADJ", syntactic_role="other", span=(0, 4),
    )
    tpl = Template("degree_adverb", "tpl_dadv_very", "very", "ADV", "intensifier", "cute")

    new_sentence = apply_template(fake_phrase, tpl, "The dog is cute.")
    assert new_sentence == "The dog is very cute."


# ----------------------------- M3a+1.5 Validator severity -----------------------------

def test_validator_severity_warning():
    """触发主谓一致后 severity == WARNING(非阻断)。"""
    rep = _validate("He like dogs.")
    assert rep.severity == "WARNING"
    assert rep.is_valid is True  # 兼容旧字段:WARNING 非 ERROR → True
    assert len(rep.auto_corrections) >= 1


def test_validator_severity_pass_default():
    """无问题时 severity == PASS or INFO（M3c1: LanguageTool 不可用时为 INFO）。"""
    rep = _validate("I like dogs.")
    assert rep.severity in ["PASS", "INFO"]  # M3c1: LanguageTool unavailable → INFO
    assert rep.is_valid is True


def test_validator_severity_infos_field():
    """ValidationReport 有 infos 字段(可空或含 LanguageTool 不可用提示)。"""
    rep = _validate("I like dogs.")
    assert hasattr(rep, "infos")
    # M3c1: LanguageTool 不可用时会有 INFO 消息，这是正常的降级行为
    assert isinstance(rep.infos, list)


# ----------------------------- M3a+1.6 Pydantic 模型 -----------------------------

def test_apply_request_validation():
    """ApplyRequest 必填字段校验。"""
    from grammar_engine.models import ApplyRequest
    from pydantic import ValidationError

    # 缺字段
    try:
        ApplyRequest()
        assert False, "应抛 ValidationError"
    except ValidationError:
        pass

    # 完整字段
    req = ApplyRequest(sentence="I like dogs.", phrase_id="p2", template_id="tpl_adj_cute", mode="offline")
    assert req.sentence == "I like dogs."
    assert req.phrase_id == "p2"


def test_apply_response_shape():
    """ExpansionApplyResponse 响应 schema。"""
    from grammar_engine.models import ExpansionApplyResponse, ValidationReport

    resp = ExpansionApplyResponse(
        sentence="I like cute dogs.",
        phrases=[],
        warnings=[],
        validation=ValidationReport(severity="PASS", is_valid=True),
    )
    assert resp.sentence == "I like cute dogs."
    assert resp.validation.severity == "PASS"


# ----------------------------- M3a+1.7 apply() 顶层入口 -----------------------------

def test_apply_full_pipeline_adjective():
    """apply() 完整流水线:输入句 + phrase_id + template_id,返回完整响应。"""
    from grammar_engine.expansion_engine import apply

    # Note: phrase_id "p1" is NP(dogs) (noun_chunks assigns p0/p1, then VPs get p2+)
    result = apply("I like dogs.", "p1", "tpl_adj_cute")
    assert result["sentence"] == "I like cute dogs."
    assert "phrases" in result
    assert len(result["phrases"]) >= 3  # 至少 NP(I), VP(like), NP(cute dogs)
    # 验证 NP(cute dogs) 包含 cute (phrases are dicts)
    np_with_cute = next(
        (p for p in result["phrases"] if p["type"] == "NP" and "cute" in p["text"]),
        None,
    )
    assert np_with_cute is not None, f"重识别后应有 NP(cute dogs),got {[p['text'] for p in result['phrases']]}"
    assert "warnings" in result
    assert "validation" in result
    assert result["validation"]["severity"] in ("PASS", "INFO", "WARNING", "ERROR")


def test_apply_phrase_id_not_found():
    """apply() 找不到 phrase_id → 200 等价 + warnings + phrases 不变。"""
    from grammar_engine.expansion_engine import apply

    result = apply("I like dogs.", "p99", "tpl_adj_cute")
    assert any("phrase_id" in w for w in result["warnings"])
    # phrases 应为原句 phrases(因为拼装失败)
    assert len(result["phrases"]) >= 1


def test_apply_template_id_not_found():
    """apply() 找不到 template_id → warnings + phrases 不变。"""
    from grammar_engine.expansion_engine import apply

    # Note: phrase_id "p1" is NP(dogs)
    result = apply("I like dogs.", "p1", "tpl_adj_nonexistent")
    assert any("template_id" in w for w in result["warnings"])
    assert len(result["phrases"]) >= 1


# ----------------------------- M3a+1.8 端点集成测试 -----------------------------

def test_endpoint_apply_via_testclient():
    """FastAPI TestClient 测 /api/expansion/apply 端点。"""
    from fastapi.testclient import TestClient
    from app import app

    # Note: phrase_id "p1" is NP(dogs) (noun_chunks assigns p0/p1, then VPs get p2+)
    with TestClient(app) as client:
        response = client.post(
            "/api/expansion/apply",
            json={"sentence": "I like dogs.", "phrase_id": "p1", "template_id": "tpl_adj_cute", "mode": "offline"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentence"] == "I like cute dogs."
        assert "phrases" in data
        assert "validation" in data
        assert data["validation"]["severity"] in ("PASS", "INFO", "WARNING", "ERROR")
