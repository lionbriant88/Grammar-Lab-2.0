"""Null Provider — 永远返回空字符串。

用于 fallback 路径:AI 不可用时,ExplainService 直接走 fallback 库,
不调用 generate()。但 Gateway 健康检查仍需正常工作。
"""
from .provider_base import AIProvider


class NullProvider(AIProvider):
    name = "null"
    model_id = "builtin"

    async def generate(self, system: str, user: str) -> str:
        """返回空字符串,调用方应走 fallback。"""
        return ""

    async def health_check(self) -> dict:
        return {"ok": False, "error": "no provider configured", "latency_ms": 0}
