"""M4 — AIExplainService.

职责:把 engine_result 翻译成 ExplainResult。
铁律:任何异常都降级到 fallback,不外抛。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from grammar_engine.ai.inference.inference_gateway import InferenceGateway, InferenceError
from grammar_engine.ai.explain.explain_cache import ExplainCache
from grammar_engine.ai.explain.prompt_templates import build_system, USER_TEMPLATE, PROMPT_VERSION
from grammar_engine.ai.explain.fallback_explanations import fallback_for
from grammar_engine.ai.explain.models import ExplainResult, ExplainSource

logger = logging.getLogger(__name__)


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


@dataclass
class ExplainContext:
    """发给 /api/explain 的输入。scene + node_type 必填。"""
    scene: str
    input_sentence: str
    selected_node_id: str
    node_type: str
    selected_node: dict
    engine_result_summary: dict
    language: str = "zh"
    student_level: str = "intermediate"


def _make_cache_key(ctx: ExplainContext) -> str:
    """Cache key 不含 provider/model/prompt_version。"""
    payload = (
        f"{ctx.scene}|"
        f"{ctx.selected_node_id}|"
        f"{ctx.input_sentence}|"
        f"{ctx.student_level}|"
        f"{ctx.language}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class AIExplainService:
    """M4 核心:把 engine_result 翻译成教学解释。"""

    def __init__(self, gateway: InferenceGateway, cache: ExplainCache):
        self.gateway = gateway
        self.cache = cache
        self.provider_name = gateway.provider.name
        self.provider_model = gateway.provider.model_id

    async def explain(self, ctx: ExplainContext) -> ExplainResult:
        # 1. 查缓存
        key = _make_cache_key(ctx)
        cached = await self.cache.get(key)
        if cached is not None:
            return ExplainResult(
                title=cached.title, summary=cached.summary, why=cached.why,
                example=cached.example, common_mistakes=cached.common_mistakes,
                tips=cached.tips, source=ExplainSource.CACHE,
                provider=self.provider_name, model=self.provider_model,
                prompt_version=PROMPT_VERSION, cached=True,
                generated_at=datetime.now(),
            )

        # 2. 调 LLM
        try:
            system = build_system(ctx.scene, ctx.node_type)
            user = USER_TEMPLATE.format(
                input_sentence=ctx.input_sentence,
                selected_node_id=ctx.selected_node_id,
                node_type=ctx.node_type,
                selected_node=ctx.selected_node,
                engine_result_summary=ctx.engine_result_summary,
                student_level=ctx.student_level,
            )
            raw = await self.gateway.complete(system, user)
            parsed = parse_response(raw)
            result = ExplainResult(
                title=parsed.title, summary=parsed.summary, why=parsed.why,
                example=parsed.example, common_mistakes=parsed.common_mistakes,
                tips=parsed.tips, source=ExplainSource.AI,
                provider=self.provider_name, model=self.provider_model,
                prompt_version=PROMPT_VERSION, cached=False,
                generated_at=datetime.now(),
            )
        except (InferenceError, ParseFail, ValueError) as e:
            logger.warning(f"[Explain] Failed: {e}, fallback")
            return self.fallback_for(ctx)

        # 3. 写缓存
        await self.cache.set(key, result)
        return result

    def fallback_for(self, ctx: ExplainContext) -> ExplainResult:
        """硬编码 fallback,永远不抛异常。"""
        base = fallback_for(ctx.scene, ctx.node_type)
        return ExplainResult(
            title=base.title, summary=base.summary, why=base.why,
            example=base.example, common_mistakes=base.common_mistakes,
            tips=base.tips, source=ExplainSource.FALLBACK,
            provider="fallback", model="builtin",
            prompt_version=PROMPT_VERSION, cached=False,
            generated_at=datetime.now(),
        )
