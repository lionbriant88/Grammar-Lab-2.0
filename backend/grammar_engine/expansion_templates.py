"""扩展模板库 (Expansion Templates) — L1 词级模板实例

为每个 ExpansionKind 提供填充实例。**规范第 12 节「模板优先」**:禁止 AI 从零生成,
扩展项必须来自预设模板。

L1 模板共 20 个(adj 7 / adv 6 / num 4 / degree 3),用户确认"完全够"。
每个模板的 `example_anchor` 锚到 **短语中心词**(dogs/like/cute),与 §2.2 的
PhraseNode.head_token_text 对齐;预览拼成 "cute dogs"(给 NP 加形容词)。

M3c3: 从句模板从 clause_templates 导入。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from .expansion_rules import ExpansionKind


@dataclass(frozen=True)
class Template:
    """单个扩展模板实例。"""

    kind: ExpansionKind
    template_id: str
    surface: str               # "cute" / "three" / "really"
    pos_tag: str               # "ADJ" / "NUM" / "ADV"
    semantic_class: str        # "appearance" / "cardinal" / "degree"
    example_anchor: str        # 模板预览锚:短语中心词如 "dogs" / "like"

    def preview(self) -> str:
        """预览文本:前置修饰 + 中心词(形容词/数词/程度副词在中心词前;副词在动词前)。"""
        if self.kind in ("adverb",):
            # 副词前置到动词前:"really like"
            return f"{self.surface} {self.example_anchor}"
        # 形容词/数词/程度副词都是左修饰中心词:"cute dogs" / "two dogs" / "very cute"
        return f"{self.surface} {self.example_anchor}"


# ----------------------------- L1 模板集(20 个) -----------------------------

L1_TEMPLATES: Dict[ExpansionKind, List[Template]] = {
    "adjective": [  # 7 个,锚=NP 中心词如 dogs
        Template("adjective", "tpl_adj_cute", "cute", "ADJ", "appearance", "dogs"),
        Template("adjective", "tpl_adj_black", "black", "ADJ", "color", "dogs"),
        Template("adjective", "tpl_adj_small", "small", "ADJ", "size", "dogs"),
        Template("adjective", "tpl_adj_big", "big", "ADJ", "size", "dogs"),
        Template("adjective", "tpl_adj_friendly", "friendly", "ADJ", "temperament", "dogs"),
        Template("adjective", "tpl_adj_noisy", "noisy", "ADJ", "behavior", "dogs"),
        Template("adjective", "tpl_adj_loyal", "loyal", "ADJ", "temperament", "dogs"),
    ],
    "adverb": [  # 6 个,锚=VP 中心词如 like/runs
        Template("adverb", "tpl_adv_really", "really", "ADV", "degree", "like"),
        Template("adverb", "tpl_adv_always", "always", "ADV", "frequency", "like"),
        Template("adverb", "tpl_adv_never", "never", "ADV", "frequency", "like"),
        Template("adverb", "tpl_adv_quickly", "quickly", "ADV", "manner", "runs"),
        Template("adverb", "tpl_adv_slowly", "slowly", "ADV", "manner", "runs"),
        Template("adverb", "tpl_adv_carefully", "carefully", "ADV", "manner", "drives"),
    ],
    "number": [  # 4 个,锚=NP
        Template("number", "tpl_num_two", "two", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_three", "three", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_five", "five", "NUM", "cardinal", "dogs"),
        Template("number", "tpl_num_many", "many", "DET", "quantifier", "dogs"),
    ],
    "degree_adverb": [  # 3 个,锚=ADJP 中心词如 cute
        Template("degree_adverb", "tpl_dadv_very", "very", "ADV", "intensifier", "cute"),
        Template("degree_adverb", "tpl_dadv_extremely", "extremely", "ADV", "intensifier", "cute"),
        Template("degree_adverb", "tpl_dadv_quite", "quite", "ADV", "moderator", "cute"),
    ],
    # L2/L3 预声明无模板(M3b/M3c 填充)
    "prepositional_phrase": [],
    "participle_phrase": [],
    "infinitive_phrase": [],
    "relative_clause": [],
    "adverbial_clause": [],
    "noun_clause": [],
}


# ----------------------------- 查询 -----------------------------

def get_templates_for_kind(kind: ExpansionKind) -> List[Any]:
    """返回某 kind 的全部模板。

    L1: 返回 Template 实例
    L3: 返回 ClauseTemplate 实例（M3c3 新增）
    """
    # L3 从句模板（M3c3）
    if kind in ("relative_clause", "adverbial_clause", "noun_clause"):
        # 延迟导入避免循环依赖
        from . import clause_templates
        if kind == "relative_clause":
            return clause_templates.RELATIVE_CLAUSE_TEMPLATES
        elif kind == "adverbial_clause":
            return clause_templates.ADVERBIAL_CLAUSE_TEMPLATES
        elif kind == "noun_clause":
            return clause_templates.NOUN_CLAUSE_TEMPLATES

    # L1 词级模板
    return list(L1_TEMPLATES.get(kind, []))


def get_template_by_id(template_id: str) -> Optional[Any]:
    """按 template_id 查单个模板。

    支持 L1 词级模板和 L3 从句模板。
    """
    # L3 从句模板（M3c5 修复：apply 端点需要查询从句模板）
    from . import clause_templates
    for tpl in clause_templates.ALL_CLAUSE_TEMPLATES:
        if tpl.template_id == template_id:
            return tpl

    # L1 词级模板
    for templates in L1_TEMPLATES.values():
        for t in templates:
            if t.template_id == template_id:
                return t
    return None


__all__ = [
    "Template",
    "L1_TEMPLATES",
    "get_templates_for_kind",
    "get_template_by_id",
]
