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
    # ========== Subject Relative Clauses (主语关系从句) ==========
    # 先行词作从句主语，关系词代替主语

    # 1. who + VP (先行词是人)
    ClauseTemplate(
        template_id="tpl_rel_who_subj",
        clause_type="relative",
        surface="who <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "person",
            "clause_function": "subject"
        },
        semantic_class="person",
        available=True  # M3c3 开放
    ),

    # 2. which + VP (先行词是物)
    ClauseTemplate(
        template_id="tpl_rel_which_subj",
        clause_type="relative",
        surface="which <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "thing",
            "clause_function": "subject"
        },
        semantic_class="thing",
        available=True  # M3c3 开放
    ),

    # 3. that + VP (通用，人或物)
    ClauseTemplate(
        template_id="tpl_rel_that_subj",
        clause_type="relative",
        surface="that <VERB>",
        slots=[
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "any",
            "clause_function": "subject"
        },
        semantic_class="general",
        available=True  # M3c3 开放
    ),

    # ========== Object Relative Clauses (宾语关系从句) ==========
    # 先行词作从句宾语，关系词后需要主语+动词

    # 4. who + NP + VP (人，口语)
    ClauseTemplate(
        template_id="tpl_rel_who_obj",
        clause_type="relative",
        surface="who <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "person",
            "clause_function": "object"
        },
        semantic_class="person",
        available=True  # M3c3 开放
    ),

    # 5. whom + NP + VP (人，正式)
    ClauseTemplate(
        template_id="tpl_rel_whom_obj",
        clause_type="relative",
        surface="whom <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "person",
            "clause_function": "object",
            "formality": "formal"
        },
        semantic_class="person",
        available=True  # M3c3 开放
    ),

    # 6. which + NP + VP (物)
    ClauseTemplate(
        template_id="tpl_rel_which_obj",
        clause_type="relative",
        surface="which <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "thing",
            "clause_function": "object"
        },
        semantic_class="thing",
        available=True  # M3c3 开放
    ),

    # 7. that + NP + VP (通用)
    ClauseTemplate(
        template_id="tpl_rel_that_obj",
        clause_type="relative",
        surface="that <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "any",
            "clause_function": "object"
        },
        semantic_class="general",
        available=True  # M3c3 开放
    ),

    # ========== Possessive Relative Clauses (所有格关系从句) ==========

    # 8. whose + NP + VP
    ClauseTemplate(
        template_id="tpl_rel_whose",
        clause_type="relative",
        surface="whose <NOUN> <VERB>",
        slots=[
            Slot(name="noun", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "any",  # whose 可用于人或物
            "clause_function": "possessive"
        },
        semantic_class="possessive",
        available=True  # M3c3 开放
    ),

    # ========== Adverbial Relative Clauses (关系副词从句) ==========

    # 9. where + clause (地点)
    ClauseTemplate(
        template_id="tpl_rel_where",
        clause_type="relative",
        surface="where <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "place",
            "clause_function": "adverbial"
        },
        semantic_class="place",
        available=True  # M3c3 开放
    ),

    # 10. when + clause (时间)
    ClauseTemplate(
        template_id="tpl_rel_when",
        clause_type="relative",
        surface="when <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "antecedent_type": "time",
            "clause_function": "adverbial"
        },
        semantic_class="time",
        available=True  # M3c3 开放
    ),
]


# ----------------------------- 状语从句模板 (Adverbial Clauses) -----------------------------

ADVERBIAL_CLAUSE_TEMPLATES: List[ClauseTemplate] = [
    # ========== Reason/Cause Adverbial Clauses (原因状语从句) ==========

    # 1. because + clause
    ClauseTemplate(
        template_id="tpl_adv_because",
        clause_type="adverbial",
        surface="because <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "end",  # 通常在句末
        },
        semantic_class="reason",
        available=True  # M3c4 开放
    ),

    # 2. since + clause (原因，较正式)
    ClauseTemplate(
        template_id="tpl_adv_since",
        clause_type="adverbial",
        surface="since <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="reason",
        available=True  # M3c4 开放
    ),

    # ========== Time Adverbial Clauses (时间状语从句) ==========

    # 3. when + clause
    ClauseTemplate(
        template_id="tpl_adv_when",
        clause_type="adverbial",
        surface="when <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="time",
        available=True  # M3c4 开放
    ),

    # 4. while + clause
    ClauseTemplate(
        template_id="tpl_adv_while",
        clause_type="adverbial",
        surface="while <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="time",
        available=True  # M3c4 开放
    ),

    # 5. after + clause
    ClauseTemplate(
        template_id="tpl_adv_after",
        clause_type="adverbial",
        surface="after <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="time",
        available=True  # M3c4 开放
    ),

    # 6. before + clause
    ClauseTemplate(
        template_id="tpl_adv_before",
        clause_type="adverbial",
        surface="before <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="time",
        available=True  # M3c4 开放
    ),

    # ========== Condition Adverbial Clauses (条件状语从句) ==========

    # 7. if + clause
    ClauseTemplate(
        template_id="tpl_adv_if",
        clause_type="adverbial",
        surface="if <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="condition",
        available=True  # M3c4 开放
    ),

    # 8. unless + clause (除非)
    ClauseTemplate(
        template_id="tpl_adv_unless",
        clause_type="adverbial",
        surface="unless <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="condition",
        available=True  # M3c4 开放
    ),

    # 9. as long as + clause
    ClauseTemplate(
        template_id="tpl_adv_as_long_as",
        clause_type="adverbial",
        surface="as long as <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "end",
        },
        semantic_class="condition",
        available=True  # M3c4 开放
    ),

    # ========== Concession Adverbial Clauses (让步状语从句) ==========

    # 10. although + clause
    ClauseTemplate(
        template_id="tpl_adv_although",
        clause_type="adverbial",
        surface="although <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="concession",
        available=True  # M3c4 开放
    ),

    # 11. though + clause (口语)
    ClauseTemplate(
        template_id="tpl_adv_though",
        clause_type="adverbial",
        surface="though <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="concession",
        available=True  # M3c4 开放
    ),

    # 12. even though + clause (强调)
    ClauseTemplate(
        template_id="tpl_adv_even_though",
        clause_type="adverbial",
        surface="even though <SUBJECT> <VERB>",
        slots=[
            Slot(name="subject", type="NP", required=True),
            Slot(name="verb", type="VP", required=True)
        ],
        constraints={
            "position": "flexible",
        },
        semantic_class="concession",
        available=True  # M3c4 开放
    ),
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
