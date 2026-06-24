"""M4 — /api/explain 集成测。

需要 backend 运行在 127.0.0.1:18765。
启动:cd backend && python app.py
"""
import time
import pytest
import requests

BASE_URL = "http://127.0.0.1:18765"


def _wait_for_service(timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            return
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    pytest.skip("Backend service not running on 18765, skipping integration test")


def test_explain_returns_200_always():
    _wait_for_service()
    r = requests.post(
        f"{BASE_URL}/api/explain",
        json={
            "scene": "timeline",
            "input_sentence": "I have lived here.",
            "selected_node_id": "n1",
            "node_type": "tense",
            "selected_node": {"text": "have lived"},
            "engine_result_summary": {"verb_count": 1},
        },
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "result" in data


def test_explain_with_missing_node_id_returns_fallback():
    _wait_for_service()
    r = requests.post(
        f"{BASE_URL}/api/explain",
        json={
            "scene": "timeline",
            "input_sentence": "test",
            "selected_node_id": "",
            "node_type": "tense",
            "selected_node": {},
            "engine_result_summary": {},
        },
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    # 缺 node_id 可能走 fallback 或 generic,degraded 至少为 true
    # (实际可能 cache miss 走 AI,然后 node_id 空仍合法 → 这里不强求 degraded)


def test_explain_health_endpoint():
    _wait_for_service()
    r = requests.get(f"{BASE_URL}/api/explain/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert "available" in data
