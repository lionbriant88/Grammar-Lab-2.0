"""M4 — InferenceGateway 单测。"""
import pytest
from grammar_engine.ai.inference.inference_gateway import InferenceGateway, InferenceError
from grammar_engine.ai.inference.providers.null_provider import NullProvider
from grammar_engine.ai.inference.provider_factory import get_provider
from grammar_engine.ai.inference.providers.cloud_provider import CloudProvider


@pytest.mark.asyncio
async def test_gateway_complete_returns_provider_output():
    """complete() 透传 provider 输出。"""
    class FakeProvider(NullProvider):
        async def generate(self, system, user):
            return f"S:{system}|U:{user}"

    gw = InferenceGateway(FakeProvider())
    out = await gw.complete("sys", "user")
    assert out == "S:sys|U:user"


@pytest.mark.asyncio
async def test_gateway_complete_raises_inference_error_on_failure():
    """provider 抛异常时,gateway 转 InferenceError。"""
    class BrokenProvider(NullProvider):
        async def generate(self, system, user):
            raise RuntimeError("boom")

    gw = InferenceGateway(BrokenProvider())
    with pytest.raises(InferenceError, match="boom"):
        await gw.complete("sys", "user")


@pytest.mark.asyncio
async def test_gateway_health_returns_provider_health():
    """health() 透传 provider.health_check()。"""
    gw = InferenceGateway(NullProvider())
    h = await gw.health()
    assert h["ok"] is False


@pytest.mark.asyncio
async def test_factory_returns_null_when_no_provider(monkeypatch):
    """无 cloud key + ollama 不可用 → NullProvider。"""
    monkeypatch.delenv("AI_CLOUD_API_KEY", raising=False)

    async def mock_unavailable(self):
        return False

    monkeypatch.setattr(
        "grammar_engine.ai.inference.provider_factory.OllamaProvider.is_available",
        mock_unavailable,
    )
    p = await get_provider()
    assert isinstance(p, NullProvider)


@pytest.mark.asyncio
async def test_factory_returns_cloud_when_key_set(monkeypatch):
    """有 AI_CLOUD_API_KEY → CloudProvider(优先于 ollama)。"""
    monkeypatch.setenv("AI_CLOUD_API_KEY", "sk-test")
    monkeypatch.setenv("AI_CLOUD_PROVIDER", "openai")
    p = await get_provider()
    assert isinstance(p, CloudProvider)
    assert p.name == "openai"
