# -*- coding: utf-8 -*-
"""M4 — Prompt 三层结构 + Snapshot。"""
from pathlib import Path
from grammar_engine.ai.explain.prompt_templates import (
    PROMPT_VERSION,
    BASE_PROMPT,
    SCENE_PROMPTS,
    NODE_PROMPTS,
    build_system,
)


def test_prompt_version_is_set():
    assert PROMPT_VERSION.startswith("M4")


def test_base_prompt_contains_no_reparse_constraint():
    assert "严禁自己重新解析句子" in BASE_PROMPT or "不要重新解析" in BASE_PROMPT
    assert "严禁修改引擎结果" in BASE_PROMPT or "不要修改引擎" in BASE_PROMPT


def test_base_prompt_requires_json_output():
    assert "JSON" in BASE_PROMPT
    for field in ("title", "summary", "why", "example", "common_mistakes", "tips"):
        assert field in BASE_PROMPT


def test_all_scenes_have_prompts():
    for scene in ("timeline", "anatomy", "expansion"):
        assert scene in SCENE_PROMPTS
        assert SCENE_PROMPTS[scene]


def test_all_node_types_have_prompts():
    for nt in ("tense", "phrase", "template", "validation_warning"):
        assert nt in NODE_PROMPTS
        assert NODE_PROMPTS[nt]


def test_build_system_combines_three_layers():
    s = build_system("timeline", "tense")
    assert BASE_PROMPT in s
    assert SCENE_PROMPTS["timeline"] in s
    assert NODE_PROMPTS["tense"] in s


def test_snapshot_files_match_constants():
    snap_dir = Path(__file__).parent / "prompts" / "snapshots"
    assert (snap_dir / "base_prompt_v1.txt").read_text(encoding="utf-8") == BASE_PROMPT
    for scene in ("timeline", "anatomy", "expansion"):
        path = snap_dir / f"scene_{scene}_v1.txt"
        assert path.read_text(encoding="utf-8") == SCENE_PROMPTS[scene]
    for nt in ("tense", "phrase", "template", "validation_warning"):
        path = snap_dir / f"node_{nt}_v1.txt"
        assert path.read_text(encoding="utf-8") == NODE_PROMPTS[nt]
