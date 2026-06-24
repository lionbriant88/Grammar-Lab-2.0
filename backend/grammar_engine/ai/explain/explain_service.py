"""M4 — AIExplainService.

职责:把 engine_result 翻译成 ExplainResult。
铁律:任何异常都降级到 fallback,不外抛。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError


class ExplainSource(str, Enum):
    AI = "ai"
    CACHE = "cache"
    FALLBACK = "fallback"


@dataclass
class ExplainResult:
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list = field(default_factory=list)
    tips: list = field(default_factory=list)
    source: ExplainSource = ExplainSource.FALLBACK
    provider: str = "fallback"
    model: str = "builtin"
    prompt_version: str = "M4a_v1"
    cached: bool = False
    generated_at: datetime = field(default_factory=datetime.now)


class ExplainResponseModel(BaseModel):
    """Pydantic 模型,验证 LLM JSON 输出。"""
    title: str = ""
    summary: str = ""
    why: str = ""
    example: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


class ParseFail(Exception):
    """LLM 输出解析失败(内部异常,外层 try/except 走 fallback)。"""
    pass


def parse_response(raw: str) -> ExplainResponseModel:
    try:
        return ExplainResponseModel.model_validate_json(raw)
    except (ValidationError, ValueError) as e:
        logger.warning(f"[AI] Parse failed: {e}")
        raise ParseFail(str(e))


logger = logging.getLogger(__name__)
