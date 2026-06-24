"""M4 — Provider 单测。"""
import pytest
from grammar_engine.ai.inference.providers.provider_base import AIProvider
from grammar_engine.ai.inference.providers.null_provider import NullProvider


def test_ai_provider_cannot_instantiate_directly():
    """AIProvider 是抽象类,不能直接实例化。"""
    with pytest.raises(TypeError):
        AIProvider()


def test_subclass_must_implement_generate():
    """子类必须实现 generate()。"""
    class IncompleteProvider(AIProvider):
        name = "incomplete"
        model_id = "x"

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_subclass_must_implement_health_check():
    """子类必须实现 health_check()。"""
    class IncompleteProvider(AIProvider):
        name = "incomplete"
        model_id = "x"

        async def generate(self, system, user):
            return ""

    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.asyncio
async def test_null_provider_generate_returns_empty():
    p = NullProvider()
    out = await p.generate("sys", "user")
    assert out == ""


@pytest.mark.asyncio
async def test_null_provider_health_check_returns_not_ok():
    p = NullProvider()
    h = await p.health_check()
    assert h["ok"] is False
    assert "error" in h


def test_null_provider_name_and_model():
    p = NullProvider()
    assert p.name == "null"
    assert p.model_id == "builtin"


from unittest.mock import patch, AsyncMock
from grammar_engine.ai.inference.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_generate_calls_api(monkeypatch):
    """generate() 调用 POST /api/generate,正确解析 response。"""
    p = OllamaProvider(base_url="http://fake", model="llama3.1:8b")

    fake_response = AsyncMock()
    fake_response.status_code = 200
    fake_response.json = lambda: {"response": "AI says..."}
    fake_response.raise_for_status = lambda: None

    class FakeAsyncClient:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def post(self, url, **kw): return fake_response

    monkeypatch.setattr(
        "grammar_engine.ai.inference.providers.ollama_provider.httpx.AsyncClient",
        FakeAsyncClient,
    )

    out = await p.generate("sys", "user")
    assert out == "AI says..."


@pytest.mark.asyncio
async def test_ollama_is_available_returns_false_on_connection_error():
    """连接失败时 is_available() 返回 False。"""
    p = OllamaProvider(base_url="http://127.0.0.1:1", model="llama3.1:8b")  # 端口 1 一定失败
    ok = await p.is_available()
    assert ok is False


import os
from grammar_engine.ai.inference.providers.cloud_provider import CloudProvider


def test_cloud_provider_requires_api_key(monkeypatch):
    """没设 AI_CLOUD_API_KEY 时 init 失败。"""
    monkeypatch.delenv("AI_CLOUD_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AI_CLOUD_API_KEY"):
        CloudProvider()


def test_cloud_provider_reads_env(monkeypatch):
    """env 配置正确时,init 成功。"""
    monkeypatch.setenv("AI_CLOUD_API_KEY", "sk-test")
    monkeypatch.setenv("AI_CLOUD_PROVIDER", "openai")
    monkeypatch.setenv("AI_CLOUD_MODEL", "gpt-4o-mini")
    p = CloudProvider()
    assert p.name == "openai"
    assert p.model_id == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_cloud_provider_health_check_without_key():
    """无 key 时 health_check 报告 not ok。"""
    os.environ.pop("AI_CLOUD_API_KEY", None)
    p = CloudProvider.__new__(CloudProvider)  # bypass __init__
    p.name = "openai"
    p.model_id = "gpt-4o-mini"
    h = await p.health_check()
    assert h["ok"] is False
