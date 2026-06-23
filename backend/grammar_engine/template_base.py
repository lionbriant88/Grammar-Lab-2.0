"""模板基础架构 - M3c2

定义从句扩展的模板抽象层：
- TemplateBase: 所有模板的基类
- ClauseTemplate: 从句模板（relative/adverbial/noun）
- Slot: 槽位系统（从句中的占位符）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


# ----------------------------- Slot 槽位系统 -----------------------------

@dataclass
class Slot:
    """从句模板中的槽位（占位符）。

    示例:
        Template: "who <VERB>"
        Slot(name="verb", type="VP", required=True)

        Realization: "who runs fast"
        verb slot ← "runs fast" (从原句提取或生成)
    """
    name: str  # 槽位名称，例如 "verb", "subject"
    type: str  # 期望的短语类型，例如 "VP", "NP", "ADJ"
    required: bool  # 是否必填
    default: Optional[str] = None  # 默认值（如果非必填）

    def __post_init__(self):
        """验证槽位定义"""
        if not self.name:
            raise ValueError("Slot name cannot be empty")
        if not self.type:
            raise ValueError("Slot type cannot be empty")
        if not self.required and self.default is None:
            raise ValueError(f"Optional slot '{self.name}' must have a default value")


# ----------------------------- TemplateBase 基类 -----------------------------

@dataclass
class TemplateBase(ABC):
    """所有模板的基类（抽象）。

    M3a: WordTemplate (adj/adv/number) - 已实现
    M3c2: ClauseTemplate (relative/adverbial/noun) - 新增
    """
    template_id: str  # 唯一标识符，例如 "tpl_rel_who_verb"
    surface: str  # 表面形式，例如 "who <VERB>" 或 "cute"
    available: bool = False  # 是否对外开放（M3c2 全部 False）

    @abstractmethod
    def get_preview(self, context: Any) -> str:
        """生成预览文本"""
        pass

    def __post_init__(self):
        """验证模板定义"""
        if not self.template_id:
            raise ValueError("template_id cannot be empty")
        if not self.surface:
            raise ValueError("surface cannot be empty")


# ----------------------------- ClauseTemplate 从句模板 -----------------------------

@dataclass
class ClauseTemplate(TemplateBase):
    """从句模板 (M3c2)。

    支持三类从句：
    - relative: 定语从句（who/which/that/where/when）
    - adverbial: 状语从句（because/when/if/although）
    - noun: 名词性从句（that/whether/what/how）
    """
    clause_type: Literal["relative", "adverbial", "noun"] = "relative"  # 必须有默认值
    slots: List[Slot] = field(default_factory=list)  # 槽位列表
    constraints: Dict[str, Any] = field(default_factory=dict)  # 语法约束
    semantic_class: str = ""  # 语义类别，例如 "person" (who), "time" (when)

    def get_preview(self, context: Any = None) -> str:
        """生成预览文本（M3c2 简化版，M3c3 完善）"""
        # M3c2: 直接返回 surface 作为预览
        # M3c3: 根据 context 填充槽位生成真实预览
        return self.surface

    def get_required_slots(self) -> List[Slot]:
        """获取所有必填槽位"""
        return [slot for slot in self.slots if slot.required]

    def get_optional_slots(self) -> List[Slot]:
        """获取所有可选槽位"""
        return [slot for slot in self.slots if not slot.required]

    def validate_slot_values(self, slot_values: Dict[str, str]) -> List[str]:
        """验证槽位值是否完整。

        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []

        # 检查必填槽位
        for slot in self.get_required_slots():
            if slot.name not in slot_values or not slot_values[slot.name]:
                errors.append(f"Required slot '{slot.name}' is missing")

        return errors

    def __post_init__(self):
        """验证从句模板定义"""
        super().__post_init__()

        if self.clause_type not in ("relative", "adverbial", "noun"):
            raise ValueError(f"Invalid clause_type: {self.clause_type}")

        # 验证槽位名称唯一性
        slot_names = [slot.name for slot in self.slots]
        if len(slot_names) != len(set(slot_names)):
            raise ValueError("Slot names must be unique")


# ----------------------------- 导出 -----------------------------

__all__ = [
    "Slot",
    "TemplateBase",
    "ClauseTemplate",
]
