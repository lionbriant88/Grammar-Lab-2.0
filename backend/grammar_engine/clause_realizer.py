"""从句实现器 - M3c2

ClauseRealizer 负责将模板 + 槽位值 → 最终从句文本。

职责：
1. 槽位替换（将 <VERB> 替换为实际动词）
2. 语法调整（agreement, tense, etc. - M3c3 实现）
3. 上下文感知（考虑原句的语法环境）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from .template_base import ClauseTemplate, Slot
from .phrase_segmenter import PhraseNode


# ----------------------------- RealizationContext -----------------------------

@dataclass
class RealizationContext:
    """从句实现的上下文信息。

    包含原句的所有语法信息，用于：
    - 提取槽位值
    - 语法一致性调整
    - 约束验证
    """
    original_sentence: str  # 原始句子
    doc: Any  # spaCy Doc 对象
    phrases: List[PhraseNode]  # 短语列表
    target_phrase_id: str  # 目标短语 ID（扩展点）

    def get_phrase_by_id(self, phrase_id: str) -> PhraseNode | None:
        """根据 ID 获取短语"""
        for phrase in self.phrases:
            if phrase.id == phrase_id:
                return phrase
        return None

    def get_target_phrase(self) -> PhraseNode | None:
        """获取目标短语（扩展点）"""
        return self.get_phrase_by_id(self.target_phrase_id)


# ----------------------------- ClauseRealizer 基类 -----------------------------

class ClauseRealizer(ABC):
    """从句实现器基类（抽象）。

    子类：
    - RelativeClauseRealizer (M3c3)
    - AdverbialClauseRealizer (M3c4)
    - NounClauseRealizer (M3c5)
    """

    @abstractmethod
    def realize(
        self,
        template: ClauseTemplate,
        slot_values: Dict[str, str],
        context: RealizationContext
    ) -> str:
        """将模板实现为最终从句文本。

        Args:
            template: 从句模板
            slot_values: 槽位值（name → value）
            context: 实现上下文

        Returns:
            最终从句文本
        """
        pass

    def _replace_slots(self, template: ClauseTemplate, slot_values: Dict[str, str]) -> str:
        """槽位替换（通用逻辑）。

        将模板中的 <SLOT_NAME> 替换为实际值。

        Args:
            template: 从句模板
            slot_values: 槽位值

        Returns:
            替换后的文本
        """
        text = template.surface

        # 替换所有槽位
        for slot in template.slots:
            placeholder = f"<{slot.name.upper()}>"
            value = slot_values.get(slot.name, slot.default or "")
            text = text.replace(placeholder, value)

        return text

    def _validate_constraints(
        self,
        template: ClauseTemplate,
        context: RealizationContext
    ) -> List[str]:
        """验证模板约束（通用逻辑）。

        Args:
            template: 从句模板
            context: 实现上下文

        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []

        # M3c2: 基础约束验证
        # M3c3-5: 子类覆盖实现具体约束

        return errors


# ----------------------------- 具体实现器（占位） -----------------------------

class RelativeClauseRealizer(ClauseRealizer):
    """定语从句实现器（M3c3 完整实现）"""

    def realize(
        self,
        template: ClauseTemplate,
        slot_values: Dict[str, str],
        context: RealizationContext
    ) -> str:
        """M3c3: 完整实现，包含约束验证"""
        # 验证槽位值
        errors = template.validate_slot_values(slot_values)
        if errors:
            raise ValueError(f"Invalid slot values: {', '.join(errors)}")

        # 验证先行词约束
        constraint_errors = self._validate_antecedent_constraints(template, context)
        if constraint_errors:
            raise ValueError(f"Constraint violation: {', '.join(constraint_errors)}")

        # 槽位替换
        return self._replace_slots(template, slot_values)

    def _validate_antecedent_constraints(
        self,
        template: ClauseTemplate,
        context: RealizationContext
    ) -> List[str]:
        """验证先行词约束（M3c3 新增）

        检查先行词类型是否符合模板要求：
        - who/whom 要求 person
        - which 要求 thing
        - that 接受 any
        - where 要求 place
        - when 要求 time
        - whose 接受 any
        """
        errors = []

        # 获取先行词（目标短语）
        antecedent = context.get_target_phrase()
        if not antecedent:
            errors.append("Target phrase not found in context")
            return errors

        if antecedent.type != "NP":
            errors.append("Target phrase must be an NP for relative clause expansion")
            return errors

        # 获取模板要求的先行词类型
        required_type = template.constraints.get("antecedent_type")
        if not required_type or required_type == "any":
            return errors  # 无约束或通用（that/whose）

        # 判断实际先行词类型
        actual_type = self._get_antecedent_type(antecedent)

        # 类型匹配检查
        if required_type != actual_type:
            errors.append(
                f"Antecedent type mismatch: template requires '{required_type}', "
                f"but antecedent is '{actual_type}'"
            )

        return errors

    def _get_antecedent_type(self, phrase: PhraseNode) -> str:
        """判断先行词的语义类型（M3c3 启发式规则）

        返回: "person", "thing", "place", "time", "reason"
        """
        head_text = (phrase.head_token_text or "").lower()
        head_lemma = phrase.features.get("head_lemma", "").lower()
        head_pos = phrase.head_pos

        # 人称代词 → person
        if head_pos == "PRON" and head_text in {
            "he", "she", "who", "i", "you", "we", "they",
            "him", "her", "me", "us", "them"
        }:
            return "person"

        # 地点名词
        if head_lemma in {
            "place", "city", "country", "town", "home", "school",
            "park", "building", "location", "street", "room",
            "house", "office", "restaurant", "store", "hospital"
        }:
            return "place"

        # 时间名词
        if head_lemma in {
            "time", "day", "year", "month", "moment", "period",
            "when", "date", "hour", "week", "season", "century",
            "morning", "afternoon", "evening", "night"
        }:
            return "time"

        # 原因名词
        if head_lemma in {"reason", "why", "cause"}:
            return "reason"

        # 人物名词
        if head_lemma in {
            "person", "man", "woman", "boy", "girl", "teacher",
            "student", "friend", "people", "child", "baby", "adult",
            "doctor", "worker", "engineer", "artist", "writer",
            "player", "singer", "actor", "musician", "scientist"
        }:
            return "person"

        # 默认为物
        return "thing"


class AdverbialClauseRealizer(ClauseRealizer):
    """状语从句实现器（M3c2 占位，M3c4 完善）"""

    def realize(
        self,
        template: ClauseTemplate,
        slot_values: Dict[str, str],
        context: RealizationContext
    ) -> str:
        """M3c2: 简单槽位替换，无语法调整"""
        errors = template.validate_slot_values(slot_values)
        if errors:
            raise ValueError(f"Invalid slot values: {', '.join(errors)}")

        return self._replace_slots(template, slot_values)


class NounClauseRealizer(ClauseRealizer):
    """名词性从句实现器（M3c2 占位，M3c5 完善）"""

    def realize(
        self,
        template: ClauseTemplate,
        slot_values: Dict[str, str],
        context: RealizationContext
    ) -> str:
        """M3c2: 简单槽位替换，无语法调整"""
        errors = template.validate_slot_values(slot_values)
        if errors:
            raise ValueError(f"Invalid slot values: {', '.join(errors)}")

        return self._replace_slots(template, slot_values)


# ----------------------------- 工厂函数 -----------------------------

def get_realizer(clause_type: str) -> ClauseRealizer:
    """根据从句类型获取对应的实现器。

    Args:
        clause_type: "relative", "adverbial", or "noun"

    Returns:
        对应的实现器实例
    """
    if clause_type == "relative":
        return RelativeClauseRealizer()
    elif clause_type == "adverbial":
        return AdverbialClauseRealizer()
    elif clause_type == "noun":
        return NounClauseRealizer()
    else:
        raise ValueError(f"Unknown clause type: {clause_type}")


# ----------------------------- 导出 -----------------------------

__all__ = [
    "RealizationContext",
    "ClauseRealizer",
    "RelativeClauseRealizer",
    "AdverbialClauseRealizer",
    "NounClauseRealizer",
    "get_realizer",
]
