"""数据模型定义 - Pydantic schemas"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class SupportedTense(str, Enum):
    """支持的时态类型"""
    SIMPLE_PRESENT = "simple_present"
    SIMPLE_PAST = "simple_past"
    SIMPLE_FUTURE_WILL = "simple_future_will"
    SIMPLE_FUTURE_GOING_TO = "simple_future_going_to"
    PAST_FUTURE_WOULD = "past_future_would"
    PAST_FUTURE_GOING_TO = "past_future_going_to"
    PRESENT_PROGRESSIVE = "present_progressive"
    PAST_PROGRESSIVE = "past_progressive"
    PRESENT_PERFECT = "present_perfect"
    PAST_PERFECT = "past_perfect"
    PRESENT_PERFECT_PROGRESSIVE = "present_perfect_progressive"


class TimeZone(str, Enum):
    """时间区域"""
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    PAST_TO_PRESENT = "past_to_present"
    PAST_FUTURE = "past_future"


class Aspect(str, Enum):
    """体"""
    SIMPLE = "simple"
    PROGRESSIVE = "progressive"
    PERFECT = "perfect"
    PERFECT_PROGRESSIVE = "perfect_progressive"


class VerbNode(BaseModel):
    """动词节点"""
    id: str
    surface: str = Field(..., description="动��原形文本")
    lemma: str = Field(..., description="动词词元")
    phrase: str = Field(..., description="完整动词短语，如 'will have been studying'")
    tense: SupportedTense
    time_zone: TimeZone
    aspect: Aspect
    subject_text: Optional[str] = None
    person: Optional[Literal[1, 2, 3]] = None
    number: Optional[Literal["singular", "plural"]] = None
    clause_text: Optional[str] = None
    span: tuple[int, int] = Field(..., description="在原句中的字符位置 [start, end)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    supported: bool = Field(default=True, description="是否支持拖拽改写")


class TimeAdverbial(BaseModel):
    """时间状语"""
    id: str
    surface: str
    semantic_type: Literal[
        "past_point", "present_point", "future_point",
        "duration", "since_start", "frequency", "reference_clause"
    ]
    time_zone: TimeZone
    span: tuple[int, int]
    confidence: float = Field(default=1.0)


class TimelineNode(BaseModel):
    """时间轴节点"""
    verb_id: str
    label: str
    x_position: float = Field(..., description="在时间轴上的归一化位置 0-1")
    visual_shape: Literal["point", "segment", "arrow", "extended_segment"]
    zone: TimeZone


class TimelineData(BaseModel):
    """时间轴数据"""
    nodes: List[TimelineNode]
    past_zone: tuple[float, float] = Field(..., description="Past 区域的 x 范围")
    present_zone: tuple[float, float] = Field(..., description="Present 区域的 x 范围")
    future_zone: tuple[float, float] = Field(..., description="Future 区域的 x 范围")


class AnalysisSummary(BaseModel):
    """分析摘要"""
    verb_count: int
    supported_verb_count: int
    primary_tense: str
    warnings: List[str] = []


class AnalyzeRequest(BaseModel):
    """分析请求"""
    sentence: str
    mode: Literal["offline", "local_ai", "cloud_ai"] = "offline"


class AnalyzeResponse(BaseModel):
    """分析响应"""
    sentence: str
    verbs: List[VerbNode]
    time_adverbials: List[TimeAdverbial]
    timeline: TimelineData
    summary: AnalysisSummary
    warnings: List[str] = []


class RewriteScope(str, Enum):
    """改写范围"""
    SINGLE_VERB = "single_verb"
    WHOLE_SENTENCE = "whole_sentence"


class ChangeItem(BaseModel):
    """变化项"""
    type: Literal["verb", "time_adverbial"]
    from_text: str
    to_text: str
    span: tuple[int, int]
    reason: str


class RewriteRequest(BaseModel):
    """改写请求"""
    sentence: str
    analysis_id: Optional[str] = None
    target_verb_id: str
    target_zone: TimeZone
    scope: RewriteScope = RewriteScope.SINGLE_VERB
    preserve_aspect: bool = True
    mode: Literal["offline", "local_ai", "cloud_ai"] = "offline"


class RewriteResponse(BaseModel):
    """改写响应"""
    new_sentence: str
    new_analysis: AnalyzeResponse
    changes: List[ChangeItem]
    explanation: str
    warnings: List[str] = []
    naturalness_score: Optional[float] = None
    ai_insight: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    model_loaded: bool
    model_version: Optional[str] = None
    version: str = "0.1.0"


# ===================== 句剖析 (Anatomy) 模型 =====================

class ChunkRole(str, Enum):
    """语义块角色"""
    SUBJECT = "subject"
    PREDICATE = "predicate"
    OBJECT = "object"
    ADVERBIAL = "adverbial"
    CLAUSE = "clause"
    PUNCT = "punct"


class Chunk(BaseModel):
    """语义块"""
    id: str
    role: ChunkRole
    text: str = Field(..., description="该块文本(词组)")
    label: str = Field(..., description="中文角色标签,如 主语/谓语/宾语")
    subordinate: Optional[str] = Field(default=None, description="从句类型 relative/adverbial/object_clause,仅从句块非空")
    token_indices: List[int] = Field(default_factory=list, description="该块覆盖的词索引(供前端编辑搬移)")


class ClauseElement(BaseModel):
    """分句内成分(主语/谓语/宾语/状语 inline 标签)"""
    word: str
    label: str = Field(..., description="中文标签,如 主语/谓语")
    # class 是 Python 关键字倾向,这里用字段别名
    element_class: str = Field(..., alias="class", description="角色英文 key,对齐 ChunkRole 值")

    model_config = {"populate_by_name": True}


class Clause(BaseModel):
    """主从分句"""
    id: str
    kind: Literal["main", "relative", "adverbial", "object_clause"]
    text: str
    label: str = Field(..., description="中文标签,如 主句/定语从句")
    antecedent: Optional[str] = Field(default=None, description="定语从句修饰的先行词文本")
    elements: List[ClauseElement] = Field(default_factory=list)


class AnatomySummary(BaseModel):
    """句剖析摘要"""
    chunk_count: int
    clause_count: int
    has_subordinate_clause: bool
    warnings: List[str] = []


class AnatomyResponse(BaseModel):
    """句剖析响应"""
    sentence: str
    chunks: List[Chunk]
    clauses: List[Clause]
    summary: AnatomySummary


# ===================== 句扩展 (Expansion) 模型 — M3a =====================
# spec §2.7:phrase-level 数据模型。字段是 phrases(不是 nodes)。

class PhraseTypeInfo(BaseModel):
    """短语类型信息"""
    type: str = Field(..., description="NP / VP / PP ...")
    label_cn: str = Field(..., description="名词短语 / 动词短语 ...")


class ExpansionKindInfo(BaseModel):
    """扩展项类型元数据"""
    kind: str
    label_cn: str
    level: int = Field(..., description="1=词级, 2=短语级, 3=从句级")
    available: bool = Field(..., description="当前是否已开放")


class ExpansionTemplateInfo(BaseModel):
    """单个扩展模板(带预览)"""
    template_id: str
    surface: str = Field(..., description="填充词,如 cute / really")
    preview: str = Field(..., description="预览短语,如 cute dogs")
    semantic_class: str = Field(..., description="语义类,如 appearance / degree")


class ExpansionCandidate(BaseModel):
    """一个 kind 的一组模板候选"""
    kind: str
    kind_label_cn: str
    level: int
    available: bool
    templates: List[ExpansionTemplateInfo] = Field(default_factory=list)


class PhraseNodeInfo(BaseModel):
    """短语节点(phrase-level,含特征槽 + Parent-Child 挂载)"""
    id: str
    type: str = Field(..., description="NP / VP / PP ...")
    text: str = Field(..., description="短语文本,如 the dogs / has been working")
    head_token_text: str = Field(..., description="中心词,如 dogs")
    head_pos: str = Field(..., description="中心词 POS")
    syntactic_role: str = Field(..., description="subject / predicate / object / adverbial / other")
    span: tuple[int, int] = Field(..., description="字符位置 [start, end)")
    features: dict = Field(
        default_factory=dict,
        description="特征槽:NP{number,person}; VP{tense,modal,aux_chain,aspect}",
    )
    parent_id: Optional[str] = Field(default=None, description="父短语 id;None=顶层")
    children_ids: List[str] = Field(default_factory=list, description="子短语 id 列表")
    is_expandable: bool = Field(default=False, description="该短语是否有 L1 可扩展项")
    candidates: List[ExpansionCandidate] = Field(default_factory=list, description="候选菜单,仅 is_expandable=True 时非空")


class ExpansionAnalyzeResponse(BaseModel):
    """句扩展分析响应(注意字段是 phrases,不是 nodes)"""
    sentence: str
    phrases: List[PhraseNodeInfo]
    warnings: List[str] = []
