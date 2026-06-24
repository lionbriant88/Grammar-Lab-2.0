"""Explain 结果缓存 — TTLCache 实现。

Cache key 不含 provider/model(跨 provider 复用)。
"""
import asyncio
from cachetools import TTLCache

from .explain_service import ExplainResult  # 避免循环:service 也引用 cache


class ExplainCache:
    def __init__(self, ttl: int = 86400, maxsize: int = 500):
        self._store: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str):
        async with self._lock:
            return self._store.get(key)

    async def set(self, key: str, result) -> None:
        async with self._lock:
            self._store[key] = result
