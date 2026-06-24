"""Shared models for explain service."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
