"""Provider 选择逻辑。

优先级:cloud (有 API key) > ollama (运行中) > null。
启动时调一次,后续由 lifespan 缓存。
"""
import os
import logging

from .providers.provider_base import AIProvider
from .providers.ollama_provider import OllamaProvider
from .providers.cloud_provider import CloudProvider
from .providers.null_provider import NullProvider

logger = logging.getLogger(__name__)


async def get_provider(base_url: str = "http://127.0.0.1:11434",
                       default_model: str = "llama3.1:8b") -> AIProvider:
    # 1. Cloud(优先)
    if os.environ.get("AI_CLOUD_API_KEY"):
        try:
            p = CloudProvider()
            logger.info(f"[Provider] Selected cloud: {p.name}/{p.model_id}")
            return p
        except ValueError as e:
            logger.warning(f"[Provider] Cloud init failed: {e}")

    # 2. Ollama
    ollama = OllamaProvider(base_url=base_url, model=default_model)
    if await ollama.is_available():
        logger.info(f"[Provider] Selected ollama: {ollama.model_id}")
        return ollama

    # 3. Fallback
    logger.info("[Provider] No provider available, using NullProvider")
    return NullProvider()
