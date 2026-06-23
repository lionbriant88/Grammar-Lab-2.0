"""扩展引擎 (Expansion Engine) — M3a 主入口

spaCy → phrase_segmenter → orchestrate rules / templates → 产出短语节点 + 候选菜单。

spec §2.6:`analyze(sentence)` 是 M3a 唯一对外函数。流程:
  1. nlp(sentence) → doc
  2. phrase_segmenter.segment(doc) → list[PhraseNode](含特征槽)
  3. 对每个短语调 rules.get_rules_for_phrase(node.type, node.head_pos):
     - 命中(且 available=True)→ is_expandable=True,填 candidates(模板预览)
     - 不命中 → is_expandable=False,candidates=[]
  4. 返回 {sentence, phrases, warnings}

M3c2 更新: 支持 ClauseTemplate（但 available=False，M3c3-5 才开放）

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


def apply_template(phrase: Any, template: Any, sentence: str) -> str:
    """M3a+1:套模板到目标短语,返回新句。

    M3c2 更新: 添加 ClauseTemplate 支持（占位，M3c3-5 完善）

    形容词:插到 NP head 之前,所有已有 adj 之后。
    """
    # M3c2: 检测 ClauseTemplate（通过 hasattr 判断是否有 clause_type 属性）
    if hasattr(template, 'clause_type'):
        # ClauseTemplate - M3c2 占位，M3c3-5 实现
        # 目前所有 ClauseTemplate available=False，前端不会调用到这里
        # M3c3: 实现定语从句拼装
        # M3c4: 实现状语从句拼装
        # M3c5: 实现名词性从句拼装
        return sentence  # M3c2 占位：不做任何改变

    if template.kind == "adjective":
        # 找 head 在原句中的字符位置
        head = phrase.head_token_text
        head_idx = sentence.find(head)
        if head_idx < 0:
            return sentence  # 找不到 head,不变
        # 找到 head 之前第一个空格(head 前就是头一个词的开头)
        before = sentence[:head_idx].rstrip()
        after_start = head_idx
        # 已有的 adj 之前是 determiner(若有)和 head
        # 简化:在 head 之前的最后空白处插入 adj
        new_sentence = before + " " + template.surface + " " + sentence[after_start:].lstrip()
        return new_sentence

    if template.kind == "number":
        head = phrase.head_token_text
        head_idx = sentence.find(head)
        if head_idx < 0:
            return sentence
        # 检测 head 前紧邻的 a/an(前一个 token 是 a/an)
        # 简化:看 head_idx 之前的字符,如果是 " a " 或 " an "(带空格)就替换
        before = sentence[:head_idx].rstrip()
        tokens_before = before.split()
        new_tokens = []
        replaced = False
        for tok in tokens_before:
            if not replaced and tok.lower() in ("a", "an"):
                # 跳过 a/an,被 number 替代
                replaced = True
                continue
            new_tokens.append(tok)

        # 如果替换了 a/an,将名词复数化
        plural_head = head
        if replaced:
            # 简单复数化规则：通常加 s
            plural_head = head + "s"

        new_tokens.append(template.surface)
        noun_form = plural_head if replaced else head
        new_sentence = " ".join(new_tokens) + " " + noun_form + sentence[head_idx + len(head):]
        return new_sentence

    if template.kind == "adverb":
        # 找 VP 的主词(head)位置,副词插到 modal 之后、main verb 之前
        head = phrase.head_token_text
        # 简化:在原句里找 main head 之前最近的空白
        # 若有 modal 词(would/can/must...),插到 modal 之后
        modal = phrase.features.get("modal")
        if modal:
            modal_idx = sentence.find(modal)
            insert_pos = modal_idx + len(modal)
        else:
            # 没 modal,直接找 head 前
            head_idx = sentence.find(head)
            if head_idx < 0:
                return sentence
            insert_pos = head_idx
        new_sentence = sentence[:insert_pos].rstrip() + " " + template.surface + " " + sentence[insert_pos:].lstrip()
        return new_sentence

    if template.kind == "degree_adverb":
        head = phrase.head_token_text
        head_idx = sentence.find(head)
        if head_idx < 0:
            return sentence
        before = sentence[:head_idx].rstrip()
        new_sentence = before + " " + template.surface + " " + sentence[head_idx:].lstrip()
        return new_sentence

    return sentence


def apply(sentence: str, phrase_id: str, template_id: str) -> Dict[str, Any]:
    """M3a+1 写路径主入口(spec §2.2 流水线):
    1. spaCy → doc, segment(doc) → base_phrases
    2. 查 phrase_id → 目标 PhraseNode  + 查 template_id → Template
    3. 拼装: apply_template → new_sentence
    4. 重跑 analyze(new_sentence) → new_phrases
    5. 调 Validator(5 项)
    6. 包装 ValidationReport(4 级 severity)
    7. 返回 {sentence, phrases, warnings, validation}

    边界:phrase_id / template_id 找不到 → warnings + phrases=原 base_phrases,不抛异常。
    """
    from . import expansion_templates as templates
    from . import expansion_validator as validator
    from .nlp_loader import nlp_loader

    sentence_clean = (sentence or "").strip()
    if not sentence_clean:
        return {
            "sentence": sentence_clean,
            "phrases": [],
            "warnings": ["空句子"],
            "validation": {"severity": "PASS", "is_valid": True, "errors": [], "warnings": [], "infos": [], "auto_corrections": []},
        }

    warnings: List[str] = []

    # 1. spaCy → base_phrases
    try:
        nlp = nlp_loader.get()
        doc = nlp(sentence_clean)
    except Exception as e:  # noqa: BLE001
        return {
            "sentence": sentence_clean,
            "phrases": [],
            "warnings": [f"spaCy model unavailable: {e}"],
            "validation": {"severity": "PASS", "is_valid": True, "errors": [], "warnings": [], "infos": [], "auto_corrections": []},
        }

    base_phrases = segment(doc)
    base_phrases.sort(key=lambda n: n.span[0])

    # 2. 查 phrase_id + template_id
    target_phrase = next((p for p in base_phrases if p.id == phrase_id), None)
    target_template = templates.get_template_by_id(template_id)

    if target_phrase is None:
        warnings.append(f"phrase_id '{phrase_id}' not found")
        # 返回原 base_phrases(转 dict)+ validation 空
        phrases_dicts = [_phrase_to_dict(p) for p in base_phrases]
        return {
            "sentence": sentence_clean,
            "phrases": phrases_dicts,
            "warnings": warnings,
            "validation": {"severity": "PASS", "is_valid": True, "errors": [], "warnings": [], "infos": [], "auto_corrections": []},
        }
    if target_template is None:
        warnings.append(f"template_id '{template_id}' not found")
        phrases_dicts = [_phrase_to_dict(p) for p in base_phrases]
        return {
            "sentence": sentence_clean,
            "phrases": phrases_dicts,
            "warnings": warnings,
            "validation": {"severity": "PASS", "is_valid": True, "errors": [], "warnings": [], "infos": [], "auto_corrections": []},
        }

    # 3. 拼装新句
    new_sentence = apply_template(target_phrase, target_template, sentence_clean)
    if new_sentence == sentence_clean:
        # 拼装失败(kind 不支持等)
        warnings.append(f"apply_template failed for kind={target_template.kind}")
        phrases_dicts = [_phrase_to_dict(p) for p in base_phrases]
        return {
            "sentence": sentence_clean,
            "phrases": phrases_dicts,
            "warnings": warnings,
            "validation": {"severity": "PASS", "is_valid": True, "errors": [], "warnings": [], "infos": [], "auto_corrections": []},
        }

    # 4. 重跑 analyze
    analyze_result = analyze(new_sentence)
    new_phrases = analyze_result["phrases"]
    new_warnings = analyze_result.get("warnings", [])
    warnings.extend(new_warnings)

    # 5. Validator
    new_doc = nlp(new_sentence)
    validation_rep = validator.validate(new_sentence, new_doc, new_phrases)
    validation_dict = {
        "severity": validation_rep.severity,
        "is_valid": validation_rep.is_valid,
        "errors": validation_rep.errors,
        "warnings": validation_rep.warnings,
        "infos": validation_rep.infos,
        "auto_corrections": validation_rep.auto_corrections,
    }

    # 6. phrases 转 dict
    phrases_dicts = [_phrase_to_dict(p) for p in new_phrases]

    return {
        "sentence": new_sentence,
        "phrases": phrases_dicts,
        "warnings": warnings,
        "validation": validation_dict,
    }


def _phrase_to_dict(p: Any) -> Dict[str, Any]:
    """把 PhraseNode dataclass 转 dict(供 Pydantic PhraseNodeInfo 消费)。

    注:candidates 在 analyze() 时已填 dict 列表,这里直接透传。
    """
    return {
        "id": p.id,
        "type": p.type,
        "text": p.text,
        "head_token_text": p.head_token_text,
        "head_pos": p.head_pos,
        "syntactic_role": p.syntactic_role,
        "span": list(p.span),
        "features": p.features,
        "parent_id": p.parent_id,
        "children_ids": list(p.children_ids),
        "is_expandable": p.is_expandable,
        "candidates": p.candidates,
    }


__all__ = ["analyze", "apply_template", "apply", "_phrase_to_dict"]
