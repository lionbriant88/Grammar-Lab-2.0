"""Prompt snapshot 测试 — 防止 prompt 漂移。

改 prompt 时必须:
1. 改 prompt_templates.py
2. 更新 snapshots/ 对应文件
3. bump snapshot.PROMPT_VERSION
4. 测试失败 → 确认改动有意 → 更新 snapshot
"""
from pathlib import Path
from grammar_engine.ai.explain.prompt_templates import (
    BASE_PROMPT, SCENE_PROMPTS, NODE_PROMPTS,
)
from grammar_engine.ai.explain.snapshot import PROMPT_VERSION


SNAP_DIR = Path(__file__).parent / "snapshots"


def _check(name, content):
    expected = (SNAP_DIR / name).read_text(encoding="utf-8").rstrip("\n")
    actual = content.rstrip("\n")
    assert actual == expected, f"{name} drifted. If intentional, update snapshot and bump PROMPT_VERSION."


def test_base_prompt_snapshot():
    _check("base_prompt_v1.txt", BASE_PROMPT)


def test_scene_snapshots():
    for scene in ("timeline", "anatomy", "expansion"):
        _check(f"scene_{scene}_v1.txt", SCENE_PROMPTS[scene])


def test_node_snapshots():
    for nt in ("tense", "phrase", "template", "validation_warning"):
        _check(f"node_{nt}_v1.txt", NODE_PROMPTS[nt])


def test_prompt_version_present():
    assert PROMPT_VERSION, "PROMPT_VERSION must be set"
