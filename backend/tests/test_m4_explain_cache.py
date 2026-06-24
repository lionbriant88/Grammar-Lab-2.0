"""M4 — ExplainCache 单测。"""
import asyncio
import time
import pytest
from grammar_engine.ai.explain.explain_cache import ExplainCache


def _make_result():
    from grammar_engine.ai.explain.explain_service import ExplainResult, ExplainSource
    return ExplainResult(
        title="t", summary="s", why="w", example="e",
        common_mistakes=[], tips=[], source=ExplainSource.AI,
        provider="ollama", model="llama3.1:8b", prompt_version="M4a_v1",
        cached=False,
    )


@pytest.mark.asyncio
async def test_cache_set_and_get():
    c = ExplainCache()
    r = _make_result()
    await c.set("k1", r)
    got = await c.get("k1")
    assert got is not None
    assert got.title == "t"


@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    c = ExplainCache()
    assert await c.get("nope") is None


@pytest.mark.asyncio
async def test_cache_respects_ttl(monkeypatch):
    c = ExplainCache(ttl=1, maxsize=10)
    await c.set("k", _make_result())
    assert await c.get("k") is not None
    time.sleep(1.1)
    assert await c.get("k") is None


@pytest.mark.asyncio
async def test_cache_evicts_oldest_when_full():
    c = ExplainCache(ttl=86400, maxsize=2)
    await c.set("a", _make_result())
    await c.set("b", _make_result())
    await c.set("c", _make_result())  # 触发淘汰
    assert await c.get("a") is None
    assert await c.get("b") is not None
    assert await c.get("c") is not None
