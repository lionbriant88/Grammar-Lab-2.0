"""扩展引擎 (Expansion Engine) — M3a 主入口

spaCy → phrase_segmenter → orchestrate rules / templates → 产出短语节点 + 候选菜单。

spec §2.6:`analyze(sentence)` 是 M3a 唯一对外函数。流程:
  1. nlp(sentence) → doc
  2. phrase_segmenter.segment(doc) → list[PhraseNode](含特征槽)
  3. 对每个短语调 rules.get_rules_for_phrase(node.type, node.head_pos):
     - 命中(且 available=True)→ is_expandable=True,填 candidates(模板预览)
     - 不命中 → is_expandable=False,candidates=[]
  4. 返回 {sentence, phrases, warnings}

spaCy 不可用时降级:返回 warnings + 空 phrases,不抛异常(spec §2.6 原决策)。
"""
from __future__ import annotations

from typing import Any, Dict, List

from .nlp_loader import nlp_loader
from .phrase_segmenter import segment
from . import expansion_rules as rules
from . import expansion_templates as templates


def analyze(sentence: str) -> Dict[str, Any]:
    """M3a 唯一对外函数。返回 {sentence, phrases, warnings}。

    phrases: list[PhraseNode],每个带 is_expandable / candidates(模板预览)。
    """
    sentence_clean = (sentence or "").strip()
    if not sentence_clean:
        return {"sentence": "", "phrases": [], "warnings": ["空句子"]}

    warnings: List[str] = []

    # spaCy 降级
    try:
        nlp = nlp_loader.get()
    except Exception as e:  # noqa: BLE001
        return {
            "sentence": sentence_clean,
            "phrases": [],
            "warnings": [f"spaCy model unavailable: {e}"],
        }

    try:
        doc = nlp(sentence_clean)
    except Exception as e:  # noqa: BLE001
        return {
            "sentence": sentence_clean,
            "phrases": [],
            "warnings": [f"spaCy model unavailable: {e}"],
        }

    if len(doc) == 0:
        return {"sentence": sentence_clean, "phrases": [], "warnings": ["空句子"]}

    # 1. 短语识别
    phrases = segment(doc)

    # 2. 为每个短语填 candidates(仅 available=True 的 kind,带模板预览)
    for node in phrases:
        available_kinds = rules.get_available_rules_for_phrase(node.type, node.head_pos)
        if not available_kinds:
            node.is_expandable = False
            node.candidates = []
            continue
        # NP 中心词是代词(I/you/he...)时,L1 不扩展(不能说 "cute I" / "two I")
        if node.type == "NP" and node.head_pos == "PRON":
            node.is_expandable = False
            node.candidates = []
            continue
        node.is_expandable = True
        node.candidates = _build_candidates(node, available_kinds)

    return {
        "sentence": sentence_clean,
        "phrases": phrases,
        "warnings": warnings,
    }


def _build_candidates(node: Any, kinds: List[str]) -> List[Dict[str, Any]]:
    """为一个短语构造候选菜单:每个 kind 一组,带模板预览。"""
    candidates: List[Dict[str, Any]] = []
    for kind in kinds:
        meta = rules.get_kind_metadata(kind)  # type: ignore[arg-type]
        tpls = templates.get_templates_for_kind(kind)  # type: ignore[arg-type]
        # 模板预览用该短语的实际中心词替换锚(让 "cute dogs" 而非 "cute <锚>")
        head = node.head_token_text or ""
        template_infos = []
        for tpl in tpls:
            preview = _compose_preview(tpl, head)
            template_infos.append({
                "template_id": tpl.template_id,
                "surface": tpl.surface,
                "preview": preview,
                "semantic_class": tpl.semantic_class,
            })
        candidates.append({
            "kind": kind,
            "kind_label_cn": meta.get("label_cn", kind),
            "level": meta.get("level", 0),
            "available": meta.get("available", False),
            "templates": template_infos,
        })
    return candidates


def _compose_preview(tpl: Any, head: str) -> str:
    """模板预览:用短语实际中心词替换 example_anchor。"""
    if tpl.kind in ("adverb",):
        return f"{tpl.surface} {head}" if head else tpl.surface
    return f"{tpl.surface} {head}" if head else tpl.surface


__all__ = ["analyze"]
