"""Ollama 本地 Provider。

POST http://127.0.0.1:11434/api/generate
"""
import time
import httpx

from .provider_base import AIProvider


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "llama3.1:8b", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.model_id = model
        self.timeout = timeout

    async def is_available(self) -> bool:
        """GET /api/tags,3 秒超时。"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def generate(self, system: str, user: str) -> str:
        """POST /api/generate,stream=false。"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": user,
                    "system": system,
                    "stream": False,
                },
            )
            r.raise_for_status()
            return r.json().get("response", "")

    async def health_check(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                ok = r.status_code == 200
                return {
                    "ok": ok,
                    "latency_ms": int((time.time() - start) * 1000),
                    "error": None if ok else f"HTTP {r.status_code}",
                }
        except Exception as e:
            return {
                "ok": False,
                "latency_ms": int((time.time() - start) * 1000),
                "error": str(e),
            }
