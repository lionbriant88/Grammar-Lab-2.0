"""M4 — /api/explain 端点 in-process 集成测。

Unlike backend/tests/integration/test_m4_api.py (which hits a live server
and skips if the service is not running), this file exercises the FastAPI
app in-process via fastapi.testclient.TestClient. The whole M4 contract
(never-200, source field, degraded flag, cache hit, fallback path) is
covered here, so CI gets deterministic coverage without a live backend.

The pattern is the same one used in
backend/tests/test_expansion_engine.py:507 (test_endpoint_apply_via_testclient).
"""

import pytest
from fastapi.testclient import TestClient

from app import app
import app as app_module
from grammar_engine.ai.explain.models import ExplainSource


@pytest.fixture
def client():
    """TestClient that triggers FastAPI's lifespan (so model loads, etc.).

    Lifespan may fail to load the spaCy model in some CI environments
    (no en_core_web_sm) — that's fine: the M4 endpoints have their own
    fallback path when the model or the AI provider is not available.
    """
    with TestClient(app) as c:
        yield c


def _payload(scene: str = "timeline", node_id: str = "n1") -> dict:
    return {
        "scene": scene,
        "input_sentence": "I have lived here.",
        "selected_node_id": node_id,
        "node_type": "tense",
        "selected_node": {"text": "have lived"},
        "engine_result_summary": {"verb_count": 1},
    }


def test_full_flow_health_then_explain_happy_path(client):
    """Health endpoint returns 200 + valid shape; explain returns 200 with
    a non-empty result title regardless of whether AI is available."""
    # 1. Health
    h = client.get("/api/explain/health")
    assert h.status_code == 200
    health = h.json()
    assert "provider" in health
    assert "available" in health
    assert isinstance(health["available"], bool)

    # 2. Explain — Iron Rule: always 200, ok=True, result present.
    r = client.post("/api/explain", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "result" in data
    assert data["result"]["title"]  # non-empty
    assert data["result"]["source"] in {s.value for s in ExplainSource}


def test_explain_cache_hit_on_identical_input(client, monkeypatch):
    """Two identical /api/explain calls — the second must report cached=true.

    Validates that the cache key is stable across calls and that
    ExplainCache.hit() sets result.cached. The gateway is monkey-patched
    to return a deterministic AI result so the cache is always populated,
    regardless of whether a real AI API key is available.
    """
    service = app_module.explain_service
    if service is None:
        pytest.skip("explain_service not initialized in this env")

    # JSON that parse_response(ExplainResponseModel) accepts.
    FAKE_LLM_OUTPUT = (
        '{"title":"Present Perfect Tense","summary":"Action with past relevance.",'
        '"why":"connect past and present","example":"I have lived here.",'
        '"common_mistakes":[],"tips":[]}'
    )

    async def _fake_complete(system: str, user: str) -> str:
        return FAKE_LLM_OUTPUT

    monkeypatch.setattr(service.gateway, "complete", _fake_complete)

    payload = _payload(node_id="cache-test-node")
    r1 = client.post("/api/explain", json=payload)
    assert r1.status_code == 200
    first = r1.json()["result"]
    assert first["cached"] is False
    assert first["source"] == ExplainSource.AI.value

    r2 = client.post("/api/explain", json=payload)
    assert r2.status_code == 200
    second = r2.json()["result"]
    assert second["cached"] is True, (
        f"second call should be served from cache; got cached={second['cached']}, "
        f"source={second['source']}"
    )
    assert second["source"] == ExplainSource.CACHE.value
    assert second["title"] == first["title"]


def test_explain_fallback_when_service_down(client, monkeypatch):
    """With explain_service forced to None, the endpoint must still 200
    and serve a fallback result. Iron Rule 1: never 5xx."""
    monkeypatch.setattr(app_module, "explain_service", None)
    r = client.post("/api/explain", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["degraded"] is True
    assert data["result"]["source"] == ExplainSource.FALLBACK.value
    # Fallback title is scene-specific (timeline → 解释), must be non-empty.
    assert data["result"]["title"]


def test_explain_degraded_on_provider_exception(client, monkeypatch):
    """If the live provider throws, the endpoint must catch, fall back,
    and still return 200 with degraded=true. Iron Rule 1 + ErrorHandling."""
    service = app_module.explain_service
    if service is None:
        pytest.skip("explain_service not initialized in this env")

    async def _explode(ctx):
        raise RuntimeError("simulated provider outage")

    monkeypatch.setattr(service, "explain", _explode)

    r = client.post("/api/explain", json=_payload(node_id="provider-boom"))
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["degraded"] is True
    assert data["result"]["source"] == ExplainSource.FALLBACK.value
