"""从句模板定义 - M3c2

定义 3 类从句的模板数据（占位版本，available=False）：
- 定语从句 (RelativeClause)
- 状语从句 (AdverbialClause)
- 名词性从句 (NounClause)

M3c2: 每类 1-2 个占位模板
M3c3: 定语从句扩展到 8-12 个模板，available=True
M3c4: 状语从句扩展到 10-12 个模板，available=True
M3c5: 名词性从句扩展到 10-12 个模板，available=True
"""
from typing import List
from .template_base import ClauseTemplate, Slot


# ----------------------------- 定语从句模板 (Relative Clauses) -----------------------------

RELATIVE_CLAUSE_TEMPLATES: List[ClauseTemplate] = [
    # M3c2 占位模板 #1: who + verb
    ClauseTemplate(
        template_id="tpl_rel_who_verb",
        clause_type="relative",
        surface="who <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "person",  # 先行词必须是人
        },
        semantic_class="person",
        available=False  # M3c3 才改为 True
    ),

    # M3c2 占位模板 #2: which + verb
    ClauseTemplate(
        template_id="tpl_rel_which_verb",
        clause_type="relative",
        surface="which <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "thing",  # 先行词必须是物
        },
        semantic_class="thing",
        available=False  # M3c3 才改为 True
    ),

    # M3c3 将扩展到 8-12 个模板:
    # - that + verb
    # - where + clause
    # - when + clause
    # - whose + noun + verb
    # - whom + subject + verb
    # 等等
]


# ----------------------------- 状语从句模板 (Adverbial Clauses) -----------------------------

ADVERBIAL_CLAUSE_TEMPLATES: List[ClauseTemplate] = [
    # M3c2 占位模板 #1: because + clause
    ClauseTemplate(
        template_id="tpl_adv_because",
        clause_type="adverbial",
        surface="because <CLAUSE>",
        slots=[
            Slot(name="clause", type="CLAUSE", required=True)
        ],
        constraints={
            "position": "end",  # 因果状语从句通常在句末
        },
        semantic_class="reason",
        available=False  # M3c4 才改为 True
    ),

    # M3c2 占位模板 #2: when + clause
    ClauseTemplate(
        template_id="tpl_adv_when",
        clause_type="adverbial",
        surface="when <CLAUSE>",
        slots=[
            Slot(name="clause", type="CLAUSE", required=True)
        ],
        constraints={
            "position": "flexible",  # 时间状语从句位置灵活
        },
        semantic_class="time",
        available=False  # M3c4 才改为 True
    ),

    # M3c4 将扩展到 10-12 个模板:
    # - if + clause (条件)
    # - although + clause (让步)
    # - while + clause (时间)
    # - as soon as + clause (时间)
    # - unless + clause (条件)
    # - even though + clause (让步)
    # 等等
]


# ----------------------------- 名词性从句模板 (Noun Clauses) -----------------------------

NOUN_CLAUSE_TEMPLATES: List[ClauseTemplate] = [
    # M3c2 占位模板 #1: that + clause
    ClauseTemplate(
        template_id="tpl_noun_that",
        clause_type="noun",
        surface="that <CLAUSE>",
        slots=[
            Slot(name="clause", type="CLAUSE", required=True)
        ],
        constraints={
            "function": "object",  # 作宾语从句
        },
        semantic_class="statement",
        available=False  # M3c5 才改为 True
    ),

    # M3c2 占位模板 #2: whether + clause
    ClauseTemplate(
        template_id="tpl_noun_whether",
        clause_type="noun",
        surface="whether <CLAUSE>",
        slots=[
            Slot(name="clause", type="CLAUSE", required=True)
        ],
        constraints={
            "function": "object",  # 作宾语从句
        },
        semantic_class="question",
        available=False  # M3c5 才改为 True
    ),

    # M3c5 将扩展到 10-12 个模板:
    # - what + clause (主语/宾语)
    # - how + clause (方式)
    # - why + clause (原因)
    # - where + clause (地点)
    # - when + clause (时间)
    # - who + clause (人物)
    # 等等
]


# ----------------------------- 统一访问接口 -----------------------------

ALL_CLAUSE_TEMPLATES: List[ClauseTemplate] = (
    RELATIVE_CLAUSE_TEMPLATES
    + ADVERBIAL_CLAUSE_TEMPLATES
    + NOUN_CLAUSE_TEMPLATES
)


def get_clause_templates_by_type(clause_type: str) -> List[ClauseTemplate]:
    """根据从句类型获取模板列表。

    Args:
        clause_type: "relative", "adverbial", or "noun"

    Returns:
        对应类型的模板列表
    """
    if clause_type == "relative":
        return RELATIVE_CLAUSE_TEMPLATES
    elif clause_type == "adverbial":
        return ADVERBIAL_CLAUSE_TEMPLATES
    elif clause_type == "noun":
        return NOUN_CLAUSE_TEMPLATES
    else:
        raise ValueError(f"Unknown clause type: {clause_type}")


def get_available_clause_templates() -> List[ClauseTemplate]:
    """获取所有 available=True 的从句模板。

    M3c2: 返回空列表（所有模板 available=False）
    M3c3+: 返回已开放的模板
    """
    return [t for t in ALL_CLAUSE_TEMPLATES if t.available]


def get_template_by_id(template_id: str) -> ClauseTemplate | None:
    """根据 template_id 获取模板。

    Args:
        template_id: 模板 ID

    Returns:
        对应的模板，未找到返回 None
    """
    for template in ALL_CLAUSE_TEMPLATES:
        if template.template_id == template_id:
            return template
    return None


# ----------------------------- 导出 -----------------------------

__all__ = [
    "RELATIVE_CLAUSE_TEMPLATES",
    "ADVERBIAL_CLAUSE_TEMPLATES",
    "NOUN_CLAUSE_TEMPLATES",
    "ALL_CLAUSE_TEMPLATES",
    "get_clause_templates_by_type",
    "get_available_clause_templates",
    "get_template_by_id",
]
