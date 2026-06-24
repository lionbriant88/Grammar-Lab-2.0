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
