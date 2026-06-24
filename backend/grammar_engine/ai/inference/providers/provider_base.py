"""Provider 抽象基类 — 所有 LLM Provider 必须实现。"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """AI Provider 接口。

    M4 只需要 generate() 和 health_check()。
    M5+ 可能加 stream()、embed() 等,在此扩展。
    """

    name: str
    model_id: str

    @abstractmethod
    async def generate(self, system: str, user: str) -> str:
        """同步返回完整文本(非流式)。

        Args:
            system: 系统提示
            user: 用户提示

        Returns:
            模型输出文本

        Raises:
            ProviderError: 任何 LLM 调用失败
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> dict:
        """健康检查。

        Returns:
            {"ok": bool, "latency_ms": int, "error"?: str}
        """
        raise NotImplementedError
