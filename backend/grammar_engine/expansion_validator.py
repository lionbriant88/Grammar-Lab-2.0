"""扩展验证器 (Expansion Validator) — 渲染前验证语法正确性

M3a+1:Validator 升级为 4 级 severity 包装(PASS/INFO/WARNING/ERROR),但仍顾问非权威。
- /apply 永远返回 200(由 endpoint 决定,不是 validator 决定)
- severity 反映问题严重程度,不阻断提交
- 旧 is_valid 字段保留:severity=="ERROR" → False,否则 True
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from .phrase_segmenter import PhraseNode

# M3a+1:severity 4 级
Severity = Literal["PASS", "INFO", "WARNING", "ERROR"]
SEVERITY_ORDER = {"PASS": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


@dataclass
class ValidationReport:
    """单项校验结果(M3a+1 加 severity + infos)。"""

    severity: Severity = "PASS"
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)
    auto_corrections: List[Dict[str, str]] = field(default_factory=list)


# ----------------------------- 统一入口 -----------------------------

def validate(sentence: str, doc: Any, phrases: List[PhraseNode]) -> ValidationReport:
    """5 项检查统一入口。M3a:第 1 项实现,2-5 占位。

    phrases 是 phrase_segmenter.segment(doc) 的输出(含特征槽)。
    """
    reports = [
        validate_subject_verb_agreement(sentence, doc, phrases),  # M3a 实现
        validate_tense_consistency(sentence, doc, phrases),       # M3b 占位
        validate_clause_completeness(sentence, doc, phrases),     # M3c 占位
        validate_non_finite_legality(sentence, doc, phrases),     # M3c 占位
        validate_relative_pronoun_match(sentence, doc, phrases),  # M3c 占位
    ]
    return _merge_reports(reports)


def _merge_reports(reports: List[ValidationReport]) -> ValidationReport:
    merged = ValidationReport()
    max_sev = "PASS"
    for r in reports:
        sev_rank = SEVERITY_ORDER.get(r.severity, 0)
        max_rank = SEVERITY_ORDER.get(max_sev, 0)
        if sev_rank > max_rank:
            max_sev = r.severity
        merged.errors.extend(r.errors)
        merged.warnings.extend(r.warnings)
        merged.infos.extend(r.infos)
        merged.auto_corrections.extend(r.auto_corrections)
    merged.severity = max_sev
    merged.is_valid = max_sev != "ERROR"
    return merged


# ----------------------------- 第 1 项:主谓一致(M3a 实现) -----------------------------

def validate_subject_verb_agreement(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """M3a 唯一实现的校验项。读短语特征槽(原则 #6):

    - 找 subject NP(syntactic_role=="subject")和 predicate VP
    - 若判定为 simple present(见下)且 NP 为 3sg(person==3, number=="singular")
      且 VP 中心词未带 -s 词尾
      → auto-correction {from: VP.head, to: VP.head+"s"}

    simple present 判定(宽松,容忍 spaCy 小模型误标):
      - VP.features["tense"]=="simple_present" → 直接命中
      - 或 VP.features["tense"] in ("unknown","infinitive") 且无 modal / 无 aux_chain
        且主动词非分词(无 perfect/progressive 信号)→ 视为 simple present 兜底
        (覆盖 `He like dogs.` 这类 spaCy 把 like 误标 ADP/无 Tense 的教学场景)
    """
    report = ValidationReport()

    subject_np = next(
        (p for p in phrases if p.type == "NP" and p.syntactic_role == "subject"),
        None,
    )
    predicate_vp = next(
        (p for p in phrases if p.type == "VP" and p.syntactic_role == "predicate"),
        None,
    )
    if subject_np is None or predicate_vp is None:
        return report

    feat_np = subject_np.features or {}
    feat_vp = predicate_vp.features or {}

    number = feat_np.get("number")
    person = feat_np.get("person")
    if number != "singular" or person != 3:
        # 1sg / 2 / 3pl 在 simple present 下不触发 -s,视为正确
        return report

    tense = feat_vp.get("tense")
    aux_chain = feat_vp.get("aux_chain") or []
    modal = feat_vp.get("modal")
    aspect = feat_vp.get("aspect")

    is_simple_present = tense == "simple_present"
    if tense in ("unknown", "infinitive", None) and not modal and not aux_chain:
        # 无时态信号(可能 spaCy 误标),且无 modal/aux → 按 simple present 兜底
        # 但若 aspect 显示 perfect/progressive,不兜底
        if aspect not in ("perfect", "perfect_progressive", "progressive"):
            is_simple_present = True

    if not is_simple_present:
        return report

    head = predicate_vp.head_token_text
    if not _verb_needs_third_person_s(head):
        return report  # 已带 -s / 不规则 / 情态型,无需修正

    corrected = _add_third_person_s(head)
    report.severity = "WARNING"  # ← 新增
    report.is_valid = False
    report.errors.append(
        f"主谓不一致:主语 '{subject_np.text}' 为第三人称单数,"
        f"动词 '{head}' 应使用第三人称单数形式 '{corrected}'。"
    )
    report.auto_corrections.append({
        "from": head,
        "to": corrected,
        "reason": "主谓一致(第三人称单数加 -s)",
    })
    return report


def _verb_needs_third_person_s(verb_text: str) -> bool:
    """该动词是否还需要加 -s(即当前未带第三人称单数标记)。"""
    w = verb_text.lower()
    # 已带 -s 的常见第三人称单数形式
    if w.endswith("s") and not w.endswith("ss"):
        # likes/runs/works → 已带 -s;但 pass/miss/kiss 等以 ss 结尾原形不算
        # 简化:endswith s 且非 ss 视为已带
        return False
    # 情态 / be 动词不加 -s
    if w in {"be", "is", "am", "are", "was", "were", "has", "have", "had",
             "do", "does", "did", "can", "could", "will", "would", "shall",
             "should", "may", "might", "must"}:
        return False
    return True


def _add_third_person_s(verb_text: str) -> str:
    """给动词原形加第三人称单数 -s(含基本拼写规则)。"""
    w = verb_text
    wl = w.lower()
    if wl.endswith(("s", "x", "z", "ch", "sh")):
        return w + "es"
    # 辅音 + y → ies
    if wl.endswith("y") and len(wl) >= 2 and wl[-2] not in "aeiou":
        return w[:-1] + "ies"
    return w + "s"


# ----------------------------- 第 2 项:助动词链完整性(M3b 实现) -----------------------------

def validate_tense_consistency(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """M3b 实现:检查单个 VP 内部的助动词链完整性。

    架构决策:不实现跨 VP 时态一致性检查(那是语义级,属 M4 AI Validator)。
    仅检查单个 VP 内部 aux_chain 与 tense 的组合是否合法。

    检查规则:
    1. present_perfect → aux_chain 必须含 have/has
    2. present_perfect_progressive → aux_chain 必须含 have/has + been
    3. past_perfect → aux_chain 必须含 had
    4. past_perfect_progressive → aux_chain 必须含 had + been
    5. *_progressive (非 perfect) → aux_chain 必须含 be/is/am/are/was/were
    6. modal 后动词必须是原形(暂不实现,需复杂 POS 检查)

    示例错误:
    - "He has working." → ERROR: present_perfect 需要 past_participle(worked),不是 present_participle(working)
    - "He has work." → ERROR: present_perfect 需要 worked,不是原形 work
    - "He is worked." → WARNING: is + past_participle 通常是被动语态,需语义判断
    """
    errors = []
    warnings = []
    infos = []

    for phrase in phrases:
        # 只检查 VP
        if phrase.type != "VP":
            continue

        tense = phrase.features.get("tense", "unknown")
        aux_chain = phrase.features.get("aux_chain", [])
        aux_lower = [a.lower() for a in aux_chain]

        # 规则 1: present_perfect 必须有 have/has
        if tense == "present_perfect":
            if not any(a in ["have", "has"] for a in aux_lower):
                errors.append(
                    f"VP '{phrase.text}' 标记为 present_perfect，但 aux_chain 缺少 have/has"
                )

        # 规则 2: present_perfect_progressive 必须有 have/has + been
        if tense == "present_perfect_progressive":
            has_have = any(a in ["have", "has"] for a in aux_lower)
            has_been = "been" in aux_lower
            if not (has_have and has_been):
                errors.append(
                    f"VP '{phrase.text}' 标记为 present_perfect_progressive，"
                    f"但 aux_chain 不完整(需要 have/has + been)"
                )

        # 规则 3: past_perfect 必须有 had
        if tense == "past_perfect":
            if "had" not in aux_lower:
                errors.append(
                    f"VP '{phrase.text}' 标记为 past_perfect，但 aux_chain 缺少 had"
                )

        # 规则 4: past_perfect_progressive 必须有 had + been
        if tense == "past_perfect_progressive":
            has_had = "had" in aux_lower
            has_been = "been" in aux_lower
            if not (has_had and has_been):
                errors.append(
                    f"VP '{phrase.text}' 标记为 past_perfect_progressive，"
                    f"但 aux_chain 不完整(需要 had + been)"
                )

        # 规则 5: *_progressive (非 perfect) 必须有 be 动词
        if tense in ["present_progressive", "past_progressive"]:
            has_be = any(
                a in ["be", "is", "am", "are", "was", "were", "being"]
                for a in aux_lower
            )
            if not has_be:
                errors.append(
                    f"VP '{phrase.text}' 标记为 {tense}，但 aux_chain 缺少 be 动词"
                )

    # 合并 severity
    severity = "ERROR" if errors else ("WARNING" if warnings else "PASS")
    is_valid = (severity != "ERROR")

    return ValidationReport(
        severity=severity,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        infos=infos,
        auto_corrections=[]  # aux_chain 错误无自动修正
    )


def validate_clause_completeness(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """M3c 占位。"""
    return ValidationReport()


def validate_non_finite_legality(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """M3c 占位。"""
    return ValidationReport()


def validate_relative_pronoun_match(
    sentence: str, doc: Any, phrases: List[PhraseNode]
) -> ValidationReport:
    """M3c 占位。"""
    return ValidationReport()


__all__ = [
    "ValidationReport",
    "validate",
    "validate_subject_verb_agreement",
    "validate_tense_consistency",
    "validate_clause_completeness",
    "validate_non_finite_legality",
    "validate_relative_pronoun_match",
]
