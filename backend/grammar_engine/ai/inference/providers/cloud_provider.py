"""Cloud Provider — OpenAI / Anthropic 统一封装。

读 env:
  AI_CLOUD_PROVIDER=openai|anthropic  (默认 openai)
  AI_CLOUD_MODEL=gpt-4o-mini|claude-haiku-4-5-20251001
  AI_CLOUD_API_KEY=sk-...

用 openai SDK(Anthropic 走 openai 兼容模式,M5 再加原生 SDK)。
"""
import os
import time
import httpx

from .provider_base import AIProvider


class CloudProvider(AIProvider):
    def __init__(self):
        api_key = os.environ.get("AI_CLOUD_API_KEY")
        if not api_key:
            raise ValueError("AI_CLOUD_API_KEY env var required for CloudProvider")

        self.name = os.environ.get("AI_CLOUD_PROVIDER", "openai")
        self.model_id = os.environ.get("AI_CLOUD_MODEL", "gpt-4o-mini")
        self.api_key = api_key
        self.timeout = 30.0

    async def generate(self, system: str, user: str) -> str:
        """调 OpenAI 兼容 chat/completions 端点。"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.3,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def health_check(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
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
