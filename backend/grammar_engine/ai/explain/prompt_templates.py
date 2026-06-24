"""Prompt 三层结构:BASE + SCENE + NODE。

修改 prompt 时:
1. 改这里
2. 更新 tests/prompts/snapshots/ 对应文件
3. bump snapshot.py 的 PROMPT_VERSION
"""
from pathlib import Path

from .snapshot import PROMPT_VERSION


def _load_snapshot(name: str) -> str:
    """从 tests/prompts/snapshots 加载(运行时也走这里,保证一致)。"""
    snap_dir = Path(__file__).parent.parent.parent.parent / "tests" / "prompts" / "snapshots"
    return (snap_dir / name).read_text(encoding="utf-8").rstrip("\n")


BASE_PROMPT = _load_snapshot("base_prompt_v1.txt")

SCENE_PROMPTS: dict[str, str] = {
    "timeline":  _load_snapshot("scene_timeline_v1.txt"),
    "anatomy":   _load_snapshot("scene_anatomy_v1.txt"),
    "expansion": _load_snapshot("scene_expansion_v1.txt"),
}

NODE_PROMPTS: dict[str, str] = {
    "tense":              _load_snapshot("node_tense_v1.txt"),
    "phrase":             _load_snapshot("node_phrase_v1.txt"),
    "template":           _load_snapshot("node_template_v1.txt"),
    "validation_warning": _load_snapshot("node_validation_warning_v1.txt"),
}


def build_system(scene: str, node_type: str) -> str:
    """三层拼接: BASE + SCENE + NODE。"""
    if scene not in SCENE_PROMPTS:
        raise ValueError(f"Unknown scene: {scene}")
    if node_type not in NODE_PROMPTS:
        raise ValueError(f"Unknown node_type: {node_type}")
    return f"{BASE_PROMPT}\n{SCENE_PROMPTS[scene]}\n{NODE_PROMPTS[node_type]}"


# User 模板 — 占位符是 selected_node / engine_result_summary
USER_TEMPLATE = """原句: {input_sentence}
选中节点 ID: {selected_node_id}
节点类型: {node_type}
节点信息: {selected_node}
引擎摘要: {engine_result_summary}
学生水平: {student_level}
请生成教学解释。"""