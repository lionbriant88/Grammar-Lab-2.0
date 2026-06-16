"""扩展规则库 (Expansion Rules) — 短语类型 → 可扩展项

给定一个 **短语的类型 + 中心词 POS**,返回该短语能往哪些方向扩展(ExpansionKind)。

**关键决策(spec §2.3)**:查询键是 **短语类型 (PhraseType)**,不是 token 的 POS。
这是 spec §2.0 原则 #1/#2 的直接后果——"给 NP 加形容词"不是"给 NOUN token 加"。
因此规则表是 `NP_RULES` 而非 `NOUN_RULES`。

M3a 只实现 L1 规则查询(NP→adjective/number,VP→adverb,ADJP→degree_adverb)。
L2/L3 的 kind 在 `KIND_METADATA` 中预声明但 `available=False`,前端显示"未开放"。
"""
from __future__ import annotations

from typing import Dict, List, Literal

from .phrase_segmenter import PhraseType

# ----------------------------- 类型 -----------------------------

ExpansionKind = Literal[
    # Level 1: 词级(作用于短语的特征槽)
    "adjective",          # → NP 前置形容词
    "adverb",             # → VP/ADJP 前置副词
    "number",             # → NP 前置数词
    "degree_adverb",      # → ADJP/ADVP 前置程度副词
    # Level 2: 短语级
    "prepositional_phrase",
    "participle_phrase",
    "infinitive_phrase",
    # Level 3: 从句级
    "relative_clause",
    "adverbial_clause",
    "noun_clause",
]

# ----------------------------- 规则表(键是 PhraseType) -----------------------------

NP_RULES: List[ExpansionKind] = [
    "adjective",
    "number",
    "prepositional_phrase",     # L2(available=False)
    "participle_phrase",        # L2(available=False)
    "relative_clause",          # L3(available=False)
]

VP_RULES: List[ExpansionKind] = [
    "adverb",
    "adverbial_clause",         # L3(available=False)
]

ADJP_RULES: List[ExpansionKind] = [
    "degree_adverb",
    "infinitive_phrase",        # L2(available=False),形容词补语
]

ADVP_RULES: List[ExpansionKind] = [
    "degree_adverb",
]

# PhraseType → 规则表
_PHRASE_RULES: Dict[str, List[ExpansionKind]] = {
    "NP": NP_RULES,
    "VP": VP_RULES,
    "ADJP": ADJP_RULES,
    "ADVP": ADVP_RULES,
}

# L1 已开放的 kind(其余为预声明,L2/L3 available=False)
_L1_KINDS: set = {"adjective", "adverb", "number", "degree_adverb"}

# ----------------------------- kind 元数据 -----------------------------

KIND_METADATA: Dict[str, Dict[str, object]] = {
    "adjective":            {"label_cn": "形容词",   "level": 1, "available": True},
    "adverb":               {"label_cn": "副词",     "level": 1, "available": True},
    "number":               {"label_cn": "数词",     "level": 1, "available": True},
    "degree_adverb":        {"label_cn": "程度副词", "level": 1, "available": True},
    "prepositional_phrase": {"label_cn": "介词短语", "level": 2, "available": False},
    "participle_phrase":    {"label_cn": "分词短语", "level": 2, "available": False},
    "infinitive_phrase":    {"label_cn": "不定式",   "level": 2, "available": False},
    "relative_clause":      {"label_cn": "定语从句", "level": 3, "available": False},
    "adverbial_clause":     {"label_cn": "状语从句", "level": 3, "available": False},
    "noun_clause":          {"label_cn": "名词性从句", "level": 3, "available": False},
}


# ----------------------------- 查询(纯函数) -----------------------------

def get_rules_for_phrase(
    phrase_type: PhraseType, head_pos: str = ""
) -> List[ExpansionKind]:
    """返回该短语类型的所有可扩展 kind(含未开放的 L2/L3,前端按 available 过滤)。

    `head_pos` 作为次要键占位:M3a 暂不据此细分(如同为 NP,dog 与 running dog 都可加形容词)。
    """
    return list(_PHRASE_RULES.get(phrase_type, []))


def get_available_rules_for_phrase(
    phrase_type: PhraseType, head_pos: str = ""
) -> List[ExpansionKind]:
    """仅返回当前已开放(available=True)的 kind(M3a = L1)。"""
    return [
        k for k in get_rules_for_phrase(phrase_type, head_pos)
        if KIND_METADATA.get(k, {}).get("available", False)
    ]


def get_kind_metadata(kind: ExpansionKind) -> Dict[str, object]:
    """返回某个 kind 的元数据(label_cn / level / available)。"""
    meta = KIND_METADATA.get(kind)
    if meta is None:
        return {"label_cn": kind, "level": 0, "available": False}
    return dict(meta)


__all__ = [
    "ExpansionKind",
    "NP_RULES", "VP_RULES", "ADJP_RULES", "ADVP_RULES",
    "KIND_METADATA",
    "get_rules_for_phrase",
    "get_available_rules_for_phrase",
    "get_kind_metadata",
]
