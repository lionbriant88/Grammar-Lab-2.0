"""M4 — ExplainService 单测。"""
import pytest
from pydantic import ValidationError
from grammar_engine.ai.explain.explain_service import (
    ExplainResponseModel,
    parse_response,
    ParseFail,
    AIExplainService,
    ExplainContext,
    _make_cache_key,
)
from grammar_engine.ai.explain.models import ExplainSource
from grammar_engine.ai.explain.explain_cache import ExplainCache
from grammar_engine.ai.inference.inference_gateway import InferenceGateway
from grammar_engine.ai.inference.providers.null_provider import NullProvider


def test_parse_valid_json():
    raw = '{"title":"t","summary":"s","why":"w","example":"e","common_mistakes":["m"],"tips":["t"]}'
    r = parse_response(raw)
    assert r.title == "t"
    assert r.common_mistakes == ["m"]


def test_parse_missing_fields_uses_defaults():
    raw = '{"title":"only title"}'
    r = parse_response(raw)
    assert r.title == "only title"
    assert r.summary == ""
    assert r.common_mistakes == []


def test_parse_invalid_json_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("not json at all")


def test_parse_non_object_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("[]")


def _ctx(scene="timeline", node_type="tense", sentence="I have lived here."):
    return ExplainContext(
        scene=scene,
        input_sentence=sentence,
        selected_node_id="n1",
        node_type=node_type,
        selected_node={"text": "have lived", "tense": "present_perfect"},
        engine_result_summary={"verb_count": 1},
        language="zh",
        student_level="intermediate",
    )


@pytest.mark.asyncio
async def test_explain_uses_fallback_when_provider_returns_empty():
    """NullProvider 返回空 → 走 fallback。"""
    gw = InferenceGateway(NullProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK
    assert r.title  # 非空


@pytest.mark.asyncio
async def test_explain_uses_fallback_on_gateway_error():
    """Gateway 抛 InferenceError → 走 fallback。"""
    from grammar_engine.ai.inference.inference_gateway import InferenceGateway

    class BrokenProvider(NullProvider):
        async def generate(self, system, user):
            raise RuntimeError("boom")

    gw = InferenceGateway(BrokenProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK


@pytest.mark.asyncio
async def test_explain_returns_ai_result_on_valid_response():
    """LLM 返回合法 JSON → source=AI。"""

    class FakeProvider(NullProvider):
        async def generate(self, system, user):
            return '{"title":"ai title","summary":"s","why":"w","example":"e","common_mistakes":["m"],"tips":["t"]}'

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(FakeProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.AI
    assert r.title == "ai title"
    assert r.provider == "null"  # FakeProvider 用 NullProvider 的 name


@pytest.mark.asyncio
async def test_explain_uses_cache_on_second_call():
    """第二次同样 ctx → 命中 cache, source=CACHE, 不调 provider。"""
    call_count = {"n": 0}

    class CountingProvider(NullProvider):
        async def generate(self, system, user):
            call_count["n"] += 1
            return '{"title":"x","summary":"","why":"","example":"","common_mistakes":[],"tips":[]}'

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(CountingProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r1 = await svc.explain(_ctx())
    r2 = await svc.explain(_ctx())
    assert r1.source == ExplainSource.AI
    assert r2.source == ExplainSource.CACHE
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_explain_uses_fallback_on_parse_failure():
    """LLM 返回非 JSON → 走 fallback。"""

    class GarbageProvider(NullProvider):
        async def generate(self, system, user):
            return "this is not json at all {"

    from grammar_engine.ai.inference.inference_gateway import InferenceGateway
    gw = InferenceGateway(GarbageProvider())
    svc = AIExplainService(gateway=gw, cache=ExplainCache())
    r = await svc.explain(_ctx())
    assert r.source == ExplainSource.FALLBACK


def test_cache_key_excludes_provider_model():
    """cache key 不含 provider/model。"""
    from grammar_engine.ai.explain.explain_service import _make_cache_key
    c1 = _ctx(sentence="hello")
    c2 = _ctx(sentence="hello")
    k1 = _make_cache_key(c1)
    k2 = _make_cache_key(c2)
    assert k1 == k2


def test_cache_key_changes_with_sentence():
    c1 = _ctx(sentence="hello")
    c2 = _ctx(sentence="world")
    assert _make_cache_key(c1) != _make_cache_key(c2)
