"""硬编码 fallback 解释库。

AI 不可用时使用。M4a 覆盖主要 case,M4b 视情况扩充。
"""
from .explain_service import ExplainResult, ExplainSource


def _make(
    title: str, summary: str, why: str, example: str,
    mistakes: list, tips: list,
) -> ExplainResult:
    return ExplainResult(
        title=title, summary=summary, why=why, example=example,
        common_mistakes=mistakes, tips=tips,
        source=ExplainSource.FALLBACK,
        provider="fallback", model="builtin",
        prompt_version="M4a_v1", cached=False,
    )


FALLBACK_LIBRARY: dict = {
    # Timeline
    ("timeline", "tense"): _make(
        title="时态解释(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="时态由规则引擎根据动词形态和时间状语综合判断。请结合时间状语(already, yesterday, tomorrow 等)和动词形态(do/doing/done)理解。",
        example="I have lived here for 5 years. (现在完成时:have + 过去分词,持续到现在的状态)",
        mistakes=["把现在完成时和一般过去时混淆(现在完成时强调与现在的联系)"],
        tips=["先看时间状语,再看动词是否完成或持续"],
    ),

    # Anatomy
    ("anatomy", "phrase"): _make(
        title="短语角色(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="短语角色由规则引擎基于 spaCy 依存关系标注(主/谓/宾/状/从)。颜色对应:蓝=主语,绿=谓语,紫=宾语,琥珀=状语,粉=从句。",
        example="When I arrived, he was reading. → When I arrived 是状语从句(琥珀),修饰主句时间。",
        mistakes=["把定语(关系从句)和状语(时间/原因/让步)混淆——看它修饰名词还是动词"],
        tips=["找动词:它前面的主语、后面的宾语、旁边的时间/地点状语"],
    ),

    # Expansion
    ("expansion", "template"): _make(
        title="扩展模板(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="模板由规则引擎基于短语类型和句法约束推荐。形容词前置、副词后置、定从紧跟先行词——这些是英语的常见语序。",
        example="dog → cute dog (形容词扩展); ran → ran quickly (副词扩展)",
        mistakes=["形容词放错位置(cute dog vs dog cute)"],
        tips=["英语修饰习惯:形容词在名词前,副词在动词后或句首"],
    ),

    # Expansion — Validation
    ("expansion", "validation_warning"): _make(
        title="语法问题(规则库)",
        summary="AI 暂不可用,显示规则库解释。",
        why="校验引擎(规则 + LanguageTool)检测到潜在语法问题:主谓一致、时态一致、分句完整、非谓语合法性、关系代词匹配等。",
        example="He go to school. → 应为 He goes(主谓一致,三单加 s)。",
        mistakes=["忽略主谓一致(He go 错为 He goes)"],
        tips=["先核对主语(单复数),再核对谓语(时态/数)"],
    ),
}


FALLBACK_GENERIC = _make(
    title="解释",
    summary="AI 暂不可用,显示通用解释。",
    why="Grammar Lab 的规则引擎已给出分析结果。请结合界面上的色带、标签和提示理解句子结构。",
    example="(无) 请在主界面查看结构化分析。",
    mistakes=[],
    tips=["遇到复杂句时,先找主语和谓语,再看修饰成分"],
)


def fallback_for(scene: str, node_type: str) -> ExplainResult:
    """查表,未命中返回 generic。"""
    return FALLBACK_LIBRARY.get((scene, node_type), FALLBACK_GENERIC)
