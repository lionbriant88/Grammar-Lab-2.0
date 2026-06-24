"""M4-M7 共享推理入口。

降级策略由调用方决定(gateway 不 swallow exception),保持 M5/M6 灵活性。
"""
import logging

logger = logging.getLogger(__name__)


class InferenceError(Exception):
    """Provider 调用失败时抛出。"""
    pass


class InferenceGateway:
    """唯一推理入口。ExplainService / RewriteService / ChatService 复用。"""

    def __init__(self, provider):
        self.provider = provider

    async def complete(self, system: str, user: str) -> str:
        try:
            return await self.provider.generate(system, user)
        except Exception as e:
            logger.warning(f"[Inference] Provider {self.provider.name} failed: {e}")
            raise InferenceError(str(e)) from e

    async def health(self) -> dict:
        return await self.provider.health_check()
