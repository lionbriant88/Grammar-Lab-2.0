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
