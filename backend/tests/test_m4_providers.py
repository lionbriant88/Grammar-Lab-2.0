"""M4 — Provider 单测。"""
import pytest
from grammar_engine.ai.inference.providers.provider_base import AIProvider


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
