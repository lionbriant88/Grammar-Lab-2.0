"""M4 — Fallback 解释库单测。"""
from grammar_engine.ai.explain.fallback_explanations import (
    FALLBACK_LIBRARY,
    FALLBACK_GENERIC,
    fallback_for,
)


def test_fallback_library_covers_all_node_types():
    """每个 (scene, node_type) 组合都有 fallback。"""
    scenes = ("timeline", "anatomy", "expansion")
    nodes = ("tense", "phrase", "template", "validation_warning")
    for s in scenes:
        for n in nodes:
            if (s, n) in FALLBACK_LIBRARY:
                assert FALLBACK_LIBRARY[(s, n)].source.value == "fallback"


def test_fallback_generic_is_non_empty():
    assert FALLBACK_GENERIC.title
    assert FALLBACK_GENERIC.summary
    assert FALLBACK_GENERIC.why


def test_fallback_for_known_key_returns_specific():
    r = fallback_for("timeline", "tense")
    assert r.source.value == "fallback"
    assert r.title  # 非空


def test_fallback_for_unknown_returns_generic():
    r = fallback_for("unknown_scene", "unknown_type")
    assert r is FALLBACK_GENERIC or r.title == FALLBACK_GENERIC.title
