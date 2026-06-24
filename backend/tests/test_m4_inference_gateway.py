"""M4 — InferenceGateway 单测。"""
import pytest
from grammar_engine.ai.inference.inference_gateway import InferenceGateway, InferenceError
from grammar_engine.ai.inference.providers.null_provider import NullProvider


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
