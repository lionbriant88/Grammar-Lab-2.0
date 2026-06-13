"""9 种常见时态识别 - 启发式规则实现

支持时态：
  - simple_present         一般现在
  - simple_past            一般过去
  - simple_future_will     一般将来 (will)
  - simple_future_going_to 一般将来 (be going to)
  - past_future_would      过去将来 (would)
  - past_future_going_to   过去将来 (was/were going to)
  - present_progressive    现在进行
  - past_progressive       过去进行
  - present_perfect        现在完成
  - past_perfect           过去完成
  - present_perfect_progressive  现在完成进行（降级为 perfect + 提示）

设计：基于词形 + 时间状语佐证 + 上下文标记（"said"/"told" 引导宾从 → 过去时基线）
- 主规则：助动词 + 主动词形态
- 时间状语词典：past/present/future 时间点 + duration 提升置信度
- 句子内 NOW 锚点 = 0.5；past_zone=[0, 0.33], present_zone=[0.33, 0.67], future_zone=[0.67, 1]
- x_position 基于动词在句中位置 + 时区共同决定
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple

# ----------------------------- 常量 -----------------------------

TENSE_PRESENT = "simple_present"
TENSE_PAST = "simple_past"
TENSE_FUTURE_WILL = "simple_future_will"
TENSE_FUTURE_GOING = "simple_future_going_to"
TENSE_PAST_FUTURE_WOULD = "past_future_would"
TENSE_PAST_FUTURE_GOING = "past_future_going_to"
TENSE_PRESENT_PROG = "present_progressive"
TENSE_PAST_PROG = "past_progressive"
TENSE_PRESENT_PERFECT = "present_perfect"
TENSE_PAST_PERFECT = "past_perfect"

ASPECT_SIMPLE = "simple"
ASPECT_PROG = "progressive"
ASPECT_PERFECT = "perfect"

ZONE_PAST = "past"
ZONE_PRESENT = "present"
ZONE_FUTURE = "future"
ZONE_PAST_TO_PRESENT = "past_to_present"
ZONE_PAST_FUTURE = "past_future"

# 时态 → 时区 映射
TENSE_TO_ZONE: Dict[str, str] = {
    TENSE_PRESENT: ZONE_PRESENT,
    TENSE_PAST: ZONE_PAST,
    TENSE_FUTURE_WILL: ZONE_FUTURE,
    TENSE_FUTURE_GOING: ZONE_FUTURE,
    TENSE_PAST_FUTURE_WOULD: ZONE_PAST_FUTURE,
    TENSE_PAST_FUTURE_GOING: ZONE_PAST_FUTURE,
    TENSE_PRESENT_PROG: ZONE_PRESENT,
    TENSE_PAST_PROG: ZONE_PAST,
    TENSE_PRESENT_PERFECT: ZONE_PAST_TO_PRESENT,
    TENSE_PAST_PERFECT: ZONE_PAST,
}

# 时态 → 体
TENSE_TO_ASPECT: Dict[str, str] = {
    TENSE_PRESENT: ASPECT_SIMPLE,
    TENSE_PAST: ASPECT_SIMPLE,
    TENSE_FUTURE_WILL: ASPECT_SIMPLE,
    TENSE_FUTURE_GOING: ASPECT_SIMPLE,
    TENSE_PAST_FUTURE_WOULD: ASPECT_SIMPLE,
    TENSE_PAST_FUTURE_GOING: ASPECT_SIMPLE,
    TENSE_PRESENT_PROG: ASPECT_PROG,
    TENSE_PAST_PROG: ASPECT_PROG,
    TENSE_PRESENT_PERFECT: ASPECT_PERFECT,
    TENSE_PAST_PERFECT: ASPECT_PERFECT,
}

# 时区 → x 中心位置（用于无位置信息的回退）
ZONE_X_CENTER: Dict[str, float] = {
    ZONE_PAST: 0.15,
    ZONE_PRESENT: 0.50,
    ZONE_FUTURE: 0.85,
    ZONE_PAST_TO_PRESENT: 0.40,
    ZONE_PAST_FUTURE: 0.30,  # 过去将来 = 站在过去看将来，靠近 PAST 一侧
}

# 视觉形状（基于 aspect + zone）
def shape_for(tense: str, zone: str) -> str:
    aspect = TENSE_TO_ASPECT.get(tense, ASPECT_SIMPLE)
    if aspect == ASPECT_PROG:
        return "segment"
    if aspect == ASPECT_PERFECT:
        return "extended_segment"
    if zone in (ZONE_FUTURE, ZONE_PAST_FUTURE):
        return "arrow"
    return "point"

# 词性词典（最小集，用于主语识别 + 变形回退）
BE_FORMS_PRESENT = {"am", "is", "are"}
BE_FORMS_PAST = {"was", "were"}
HAVE_FORMS_PRESENT = {"has", "have"}
HAVE_FORMS_PAST = {"had"}
DO_FORMS_PRESENT = {"does", "do"}
DO_FORMS_PAST = {"did"}
MODAL_FUTURE = {"will", "would", "shall", "'ll"}
MODAL_PAST_FUTURE = {"would"}

# 常见过去式/过去分词不规则映射（小集合，覆盖高频词）
IRREGULAR_PAST: Dict[str, str] = {
    "go": "went", "goes": "went", "gone": "went",
    "have": "had", "has": "had",
    "do": "did", "does": "did", "done": "did",
    "say": "said", "says": "said", "said": "said",
    "tell": "told", "tells": "told", "told": "told",
    "come": "came", "comes": "came", "come_p": "came",
    "see": "saw", "sees": "saw", "seen": "saw",
    "take": "took", "takes": "took", "taken": "took",
    "give": "gave", "gives": "gave", "given": "gave",
    "make": "made", "makes": "made", "made": "made",
    "find": "found", "finds": "found", "found": "found",
    "buy": "bought", "buys": "bought", "bought": "bought",
    "read": "read",
    "write": "wrote", "writes": "wrote", "written": "wrote",
    "speak": "spoke", "speaks": "spoke", "spoken": "spoke",
    "break": "broke", "breaks": "broke", "broken": "broke",
    "choose": "chose", "chooses": "chose", "chosen": "chose",
    "drive": "drove", "drives": "drove", "driven": "drove",
    "eat": "ate", "eats": "ate", "eaten": "ate",
    "fall": "fell", "falls": "fell", "fallen": "fell",
    "fly": "flew", "flies": "flew", "flown": "flew",
    "forget": "forgot", "forgets": "forgot", "forgotten": "forgot",
    "get": "got", "gets": "got", "gotten": "got",
    "give": "gave", "gives": "gave", "given": "gave",
    "know": "knew", "knows": "knew", "known": "knew",
    "leave": "left", "leaves": "left", "left": "left",
    "lose": "lost", "loses": "lost", "lost": "lost",
    "meet": "met", "meets": "met", "met": "met",
    "pay": "paid", "pays": "paid", "paid": "paid",
    "put": "put",
    "run": "ran", "runs": "ran", "run_p": "ran",
    "sell": "sold", "sells": "sold", "sold": "sold",
    "send": "sent", "sends": "sent", "sent": "sent",
    "set": "set",
    "sit": "sat", "sits": "sat", "sat": "sat",
    "sleep": "slept", "sleeps": "slept", "slept": "slept",
    "spend": "spent", "spends": "spent", "spent": "spent",
    "stand": "stood", "stands": "stood", "stood": "stood",
    "swim": "swam", "swims": "swam", "swum": "swam",
    "teach": "taught", "teaches": "taught", "taught": "taught",
    "think": "thought", "thinks": "thought", "thought": "thought",
    "understand": "understood",
    "wake": "woke", "wakes": "woke", "woken": "woke",
    "wear": "wore", "wears": "wore", "worn": "wore",
    "win": "won", "wins": "won", "won": "won",
    "visit": "visited", "visits": "visited",
    "finish": "finished", "finishes": "finished",
    "arrive": "arrived", "arrives": "arrived",
    "cook": "cooked", "cooks": "cooked",
    "study": "studied", "studies": "studied",
    "play": "played", "plays": "played",
    "work": "worked", "works": "worked",
    "rain": "rained", "rains": "rained",
    "travel": "traveled", "travels": "traveled",
    "decide": "decided", "decides": "decided",
    "look": "looked", "looks": "looked",
}

IRREGULAR_PAST_PARTICIPLE: Dict[str, str] = {
    "go": "gone", "goes": "gone",
    "have": "had", "has": "had",
    "do": "done", "does": "done",
    "say": "said", "says": "said",
    "tell": "told", "tells": "told",
    "come": "come",
    "see": "seen",
    "take": "taken",
    "give": "given",
    "make": "made",
    "find": "found",
    "buy": "bought",
    "read": "read",
    "write": "written",
    "speak": "spoken",
    "break": "broken",
    "choose": "chosen",
    "drive": "driven",
    "eat": "eaten",
    "fall": "fallen",
    "fly": "flown",
    "forget": "forgotten",
    "get": "gotten", "got": "got",
    "know": "known",
    "leave": "left",
    "lose": "lost",
    "meet": "met",
    "pay": "paid",
    "run": "run",
    "sell": "sold",
    "send": "sent",
    "sit": "sat",
    "sleep": "slept",
    "spend": "spent",
    "stand": "stood",
    "swim": "swum",
    "teach": "taught",
    "think": "thought",
    "understand": "understood",
    "wake": "woken",
    "wear": "worn",
    "win": "won",
    "visit": "visited",
    "finish": "finished",
    "arrive": "arrived",
    "cook": "cooked",
    "study": "studied",
    "play": "played",
    "work": "worked",
    "rain": "rained",
    "travel": "traveled",
    "decide": "decided",
    "look": "looked",
}

# 时间状语词典
ADVERBIAL_RULES: List[Tuple[str, str, str]] = [
    # (regex, semantic_type, zone)
    (r"\blast\s+(?:night|weekend|month|year|summer|winter|spring|fall|autumn|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "past_point", ZONE_PAST),
    (r"\byesterday\b", "past_point", ZONE_PAST),
    (r"\b(?:just\s+now|a\s+moment\s+ago|earlier\s+today|in\s+\d{4})\b", "past_point", ZONE_PAST),
    (r"\bago\b", "past_point", ZONE_PAST),
    (r"\b(?:now|at\s+present|at\s+the\s+moment|right\s+now|today|these\s+days|currently)\b", "present_point", ZONE_PRESENT),
    (r"\b(?:tomorrow|next\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday|summer|winter|spring|fall))\b", "future_point", ZONE_FUTURE),
    (r"\bin\s+the\s+future\b", "future_point", ZONE_FUTURE),
    (r"\bsoon\b", "future_point", ZONE_FUTURE),
    (r"\b(?:the\s+next\s+day|the\s+following\s+day)\b", "future_point", ZONE_PAST_FUTURE),  # 间接引语中 = 过去将来
    (r"\bfor\s+\d+\s+(?:years?|months?|weeks?|days?|hours?|minutes?)\b", "duration", ZONE_PAST_TO_PRESENT),
    (r"\bsince\s+\d{4}\b", "since_start", ZONE_PAST_TO_PRESENT),
    (r"\bsince\s+(?:yesterday|last\s+\w+)\b", "since_start", ZONE_PAST_TO_PRESENT),
    (r"\b(?:every|each)\s+(?:day|morning|evening|night|week|month|year)\b", "frequency", ZONE_PRESENT),
    (r"\b(?:always|usually|often|sometimes|seldom|rarely|never)\b", "frequency", ZONE_PRESENT),
    (r"\bby\s+the\s+time\b", "reference_clause", ZONE_PAST),  # 引导过去完成
    (r"\bat\s+(?:ten|one|two|three|four|five|six|seven|eight|nine|eleven|twelve)\s+o'?clock\s+(?:last\s+night|this\s+morning|this\s+evening)\b", "past_point", ZONE_PAST),
]

# 间接引语标记词（提示主句为过去，宾从用过去将来/过去完成）
INDIRECT_SPEECH_TRIGGERS = {"said", "told", "asked", "thought", "knew", "believed", "hoped", "promised"}


# ----------------------------- 工具函数 -----------------------------

def _tokenize(sentence: str) -> List[Tuple[str, int, int]]:
    """把句子切成 (token, start, end) 列表，保留空白信息。"""
    tokens: List[Tuple[str, int, int]] = []
    for m in re.finditer(r"\S+", sentence):
        tokens.append((m.group(0), m.start(), m.end()))
    return tokens


def _is_ving(word: str) -> bool:
    """粗略判断 -ing 形态。"""
    if not word:
        return False
    lw = word.lower()
    if lw.endswith("ing") and len(lw) > 4:
        return True
    # 特殊：lie → lying, die → dying
    if lw.endswith("ying") and len(lw) > 5:
        return True
    return False


def _is_past_form(word: str) -> bool:
    """粗略判断规则过去式 -ed/不规则过去式。"""
    lw = word.lower()
    if lw.endswith("ed") and len(lw) > 3:
        return True
    if lw in IRREGULAR_PAST.values():
        return True
    return False


def _is_past_participle(word: str) -> bool:
    """粗略判断过去分词。"""
    lw = word.lower()
    if lw.endswith("ed") and len(lw) > 3:
        return True
    if lw.endswith("en") and len(lw) > 4:
        return True
    if lw in IRREGULAR_PAST_PARTICIPLE.values():
        return True
    return False


def _lemma_from_past(word: str) -> str:
    """从过去式回推原形。"""
    lw = word.lower()
    for base, past in IRREGULAR_PAST.items():
        if past == lw:
            return base
    if lw.endswith("ied") and len(lw) > 4:
        return lw[:-3] + "y"
    if lw.endswith("ed") and len(lw) > 3:
        stem = lw[:-2]
        if stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            return stem[:-1]  # stopped -> stop
        if stem.endswith("i"):
            return stem[:-1] + "y"  # studied -> study (粗略)
        return stem
    return lw


def _lemma_from_pp(word: str) -> str:
    """从过去分词回推原形。"""
    return _lemma_from_past(word)


def _x_position_for(span: Tuple[int, int], sentence_len: int, zone: str) -> float:
    """根据动词在句中位置 + 时区共同决定 x_position。"""
    if sentence_len == 0:
        return ZONE_X_CENTER[zone]
    # 基础：句子相对位置
    mid_char = (span[0] + span[1]) / 2
    pos = mid_char / sentence_len
    # 时区中心
    zone_center = ZONE_X_CENTER[zone]
    # 60% 时区 + 40% 位置
    return round(0.6 * zone_center + 0.4 * pos, 4)


def _build_verb_node(
    vid: str,
    surface: str,
    phrase: str,
    span: Tuple[int, int],
    tense: str,
    confidence: float,
    sentence_len: int,
    subject_text: Optional[str] = None,
    clause_text: Optional[str] = None,
) -> Dict[str, Any]:
    zone = TENSE_TO_ZONE[tense]
    aspect = TENSE_TO_ASPECT[tense]
    lemma = _lemma_from_past(surface) if _is_past_form(surface) else surface.lower()
    # V-ing 时主动词原形：去掉 -ing
    if _is_ving(surface):
        ll = surface.lower()
        if ll.endswith("ying") and len(ll) > 5:
            lemma = ll[:-4] + "y"
        elif ll.endswith("ing") and len(ll) > 4:
            stem = ll[:-3]
            if stem[-1] == stem[-2] and stem[-1] not in "aeiou":
                lemma = stem[:-1]
            elif stem.endswith("i"):
                lemma = stem[:-1] + "y"
            else:
                lemma = stem
        else:
            lemma = ll
    return {
        "id": vid,
        "surface": surface,
        "lemma": lemma,
        "phrase": phrase,
        "tense": tense,
        "time_zone": zone,
        "aspect": aspect,
        "subject_text": subject_text,
        "person": None,
        "number": None,
        "clause_text": clause_text,
        "span": list(span),
        "confidence": confidence,
        "supported": True,
    }


# ----------------------------- 主分析器 -----------------------------

def analyze(sentence: str) -> Dict[str, Any]:
    """主入口：返回完整 AnalyzeResponse 字典。"""
    sentence_clean = (sentence or "").strip()
    if not sentence_clean:
        return _empty_response("")

    tokens = _tokenize(sentence_clean)
    sentence_len = len(sentence_clean)
    tokens_lower = [(t, s, e, t.lower()) for t, s, e in tokens]

    # 检测间接引语语境（句首或主语后含 said/told/...）
    indirect_speech = _detect_indirect_speech(tokens_lower)

    # 1. 扫描时间状语
    adverbials = _scan_adverbials(sentence_clean)

    # 2. 扫描动词节点
    verbs: List[Dict[str, Any]] = []
    warnings: List[str] = []
    i = 0
    verb_counter = 0
    while i < len(tokens_lower):
        word, start, end, lw = tokens_lower[i]
        matched = _try_match_verb_phrase(tokens_lower, i, indirect_speech)
        if matched is None:
            i += 1
            continue
        verb_counter += 1
        phrase, phrase_span, tense, confidence = matched
        # 调整 confidence：若句子有佐证时间状语，置信度提升
        confidence = _adjust_confidence(tense, adverbials, confidence)
        vid = f"v{verb_counter}"
        # 主语：向前找最近的名词/��词（最多 6 个 token）
        subject = _find_subject(tokens_lower, i)
        # 分句文本：粗略用整句（避免复杂分句切分）
        node = _build_verb_node(
            vid=vid,
            surface=phrase.split()[-1] if " " in phrase else phrase,
            phrase=phrase,
            span=phrase_span,
            tense=tense,
            confidence=confidence,
            sentence_len=sentence_len,
            subject_text=subject,
            clause_text=sentence_clean,
        )
        verbs.append(node)
        # 跳过该短语覆盖的 token
        consumed = len(phrase.split())
        i += max(consumed, 1)

    # 3. 若未识别到任何动词，警告
    if not verbs:
        warnings.append("未在句中识别到已知时态的动词；可能是名词、形容词或不规则结构。")

    # 4. 主时态：取置信度最高的动词
    if verbs:
        primary = max(verbs, key=lambda v: v["confidence"])["tense"]
    else:
        primary = "unknown"

    # 5. 时间轴节点
    timeline_nodes = [
        {
            "verb_id": v["id"],
            "label": v["surface"],
            "x_position": _x_position_for(v["span"], sentence_len, v["time_zone"]),
            "visual_shape": shape_for(v["tense"], v["time_zone"]),
            "zone": v["time_zone"],
        }
        for v in verbs
    ]

    return {
        "sentence": sentence_clean,
        "verbs": verbs,
        "time_adverbials": adverbials,
        "timeline": {
            "nodes": timeline_nodes,
            "past_zone": [0.0, 0.33],
            "present_zone": [0.33, 0.67],
            "future_zone": [0.67, 1.0],
        },
        "summary": {
            "verb_count": len(verbs),
            "supported_verb_count": sum(1 for v in verbs if v["supported"]),
            "primary_tense": primary,
            "warnings": warnings,
        },
    }


def _empty_response(sentence: str) -> Dict[str, Any]:
    return {
        "sentence": sentence,
        "verbs": [],
        "time_adverbials": [],
        "timeline": {
            "nodes": [],
            "past_zone": [0.0, 0.33],
            "present_zone": [0.33, 0.67],
            "future_zone": [0.67, 1.0],
        },
        "summary": {
            "verb_count": 0,
            "supported_verb_count": 0,
            "primary_tense": "unknown",
            "warnings": ["空句子"],
        },
    }


# ----------------------------- 内部函数 -----------------------------

def _detect_indirect_speech(tokens_lower: List[Tuple[str, int, int, str]]) -> bool:
    """检测主句是否含 said/told 等间接引语触发词。"""
    for _, _, _, lw in tokens_lower:
        if lw in INDIRECT_SPEECH_TRIGGERS:
            return True
    return False


def _scan_adverbials(sentence: str) -> List[Dict[str, Any]]:
    """扫描时间状语。"""
    result: List[Dict[str, Any]] = []
    counter = 0
    for pattern, sem_type, zone in ADVERBIAL_RULES:
        for m in re.finditer(pattern, sentence, flags=re.IGNORECASE):
            counter += 1
            result.append({
                "id": f"a{counter}",
                "surface": m.group(0),
                "semantic_type": sem_type,
                "time_zone": zone,
                "span": [m.start(), m.end()],
                "confidence": 0.9,
            })
    # 按 span 起始排序
    result.sort(key=lambda a: a["span"][0])
    return result


def _try_match_verb_phrase(
    tokens: List[Tuple[str, int, int, str]],
    i: int,
    indirect_speech: bool,
) -> Optional[Tuple[str, Tuple[int, int], str, float]]:
    """从位置 i 起尝试匹配一个完整动词短语，返回 (phrase, span, tense, confidence)。
    不匹配返回 None。
    优先级（在同一 token 上）从左到右检测；匹配后整段消耗。
    """
    word, start, end, lw = tokens[i]

    # ---- 进行时（is/am/are/was/were + V-ing）----
    if lw in BE_FORMS_PRESENT or lw in BE_FORMS_PAST:
        # 后面紧跟 V-ing
        if i + 1 < len(tokens):
            nw, ns, ne, nlw = tokens[i + 1]
            if _is_ving(nw):
                phrase = f"{word} {nw}"
                span = (start, ne)
                if lw in BE_FORMS_PAST:
                    return phrase, span, TENSE_PAST_PROG, 0.95
                else:
                    return phrase, span, TENSE_PRESENT_PROG, 0.9
        # 进行时降级：be + 名词/形容词 → 不当成动词，跳过 be（让 i+1 单独处理）
        return None

    # ---- 现在完成 / 过去完成（has/have/had + p.p.）----
    if lw in HAVE_FORMS_PRESENT or lw in HAVE_FORMS_PAST:
        if i + 1 < len(tokens):
            nw, ns, ne, nlw = tokens[i + 1]
            if _is_past_participle(nw) or _is_past_form(nw):
                phrase = f"{word} {nw}"
                span = (start, ne)
                if lw == "had":
                    return phrase, span, TENSE_PAST_PERFECT, 0.95
                else:
                    return phrase, span, TENSE_PRESENT_PERFECT, 0.9
        return None

    # ---- will / would + V ----
    if lw == "will" or lw == "'ll":
        if i + 1 < len(tokens):
            nw, ns, ne, nlw = tokens[i + 1]
            if nw.isalpha() and not _is_ving(nw) and not _is_past_participle(nw) and nlw not in BE_FORMS_PRESENT and nlw not in BE_FORMS_PAST:
                phrase = f"{word} {nw}"
                span = (start, ne)
                return phrase, span, TENSE_FUTURE_WILL, 0.95
        return None

    if lw == "would":
        if i + 1 < len(tokens):
            nw, ns, ne, nlw = tokens[i + 1]
            if nw.isalpha() and not _is_ving(nw) and not _is_past_participle(nw):
                phrase = f"{word} {nw}"
                span = (start, ne)
                if indirect_speech:
                    return phrase, span, TENSE_PAST_FUTURE_WOULD, 0.9
                return phrase, span, TENSE_PAST_FUTURE_WOULD, 0.7
        return None

    # ---- be going to ----
    if lw in BE_FORMS_PRESENT or lw in BE_FORMS_PAST:
        # be + going + to + V
        if i + 3 < len(tokens):
            w1, _, _, l1 = tokens[i + 1]
            w2, _, _, l2 = tokens[i + 2]
            w3, ws, we, l3 = tokens[i + 3]
            if l1 == "going" and l2 == "to" and w3.isalpha() and not _is_ving(w3):
                phrase = f"{word} going to {w3}"
                span = (start, we)
                if lw in BE_FORMS_PAST:
                    return phrase, span, TENSE_PAST_FUTURE_GOING, 0.85
                return phrase, span, TENSE_FUTURE_GOING, 0.9
        return None

    # ---- 主动词（裸词）----
    # 过去式（-ed 或不规则）→ simple_past
    if _is_past_form(word):
        # 排除过去分词被 have/has/had 修饰的场景（前面是 have/has/had 时已经被处理）
        # 排除 be + past（那是被动语态，简化为一般过去）
        if i > 0:
            prev_lw = tokens[i - 1][3]
            if prev_lw in HAVE_FORMS_PRESENT or prev_lw in HAVE_FORMS_PAST:
                return None
        return word, (start, end), TENSE_PAST, 0.85

    # V-ing 裸出现（罕见，前面漏了 be 助动词） → 当作 present_progressive
    if _is_ving(word):
        return word, (start, end), TENSE_PRESENT_PROG, 0.6

    # 原形 → simple_present（默认）
    if word.isalpha() and len(word) > 1 and not word[0].isupper() and word not in {
        "the", "a", "an", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
        "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
        "in", "on", "at", "by", "to", "for", "with", "from", "of", "into", "onto", "over", "under",
        "and", "or", "but", "so", "because", "although", "though", "if", "when", "while", "before", "after",
        "very", "quite", "rather", "too", "also", "just", "already", "still", "even", "only",
    }:
        # 启发式：动词在句中 + 后面有名词/代词/介词/冠词 → 当动词
        # 否则不识别（避免误判名词）
        if i + 1 < len(tokens):
            nw, ns, ne, nlw = tokens[i + 1]
            if nlw in {"the", "a", "an", "to", "at", "in", "on", "for", "with", "it", "me", "you", "him", "her", "us", "them", "medicine", "english", "japan", "homework", "book", "dinner", "party", "college", "garden"}:
                return word, (start, end), TENSE_PRESENT, 0.7
        return None

    return None


def _find_subject(tokens: List[Tuple[str, int, int, str]], i: int) -> Optional[str]:
    """向前找主语。粗略：跳过冠词/形容词/介词，找最近的名词/代词。"""
    SUBJECT_PRONOUNS = {"i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those"}
    SKIP = {"the", "a", "an", "my", "your", "his", "her", "its", "our", "their", "this", "that", "in", "on", "at", "by", "for", "with", "from"}
    for j in range(i - 1, max(-1, i - 6), -1):
        word, start, end, lw = tokens[j]
        if lw in SKIP or lw in {"will", "would", "shall", "be", "been", "being", "have", "has", "had", "am", "is", "are", "was", "were"}:
            continue
        if word[0:1].isupper() or lw in SUBJECT_PRONOUNS:
            return word
        if word.isalpha() and len(word) > 1:
            return word
    return None


def _adjust_confidence(tense: str, adverbials: List[Dict[str, Any]], base: float) -> float:
    """根据时间状语佐证调整置信度。"""
    if not adverbials:
        return base
    zone = TENSE_TO_ZONE[tense]
    matches = [a for a in adverbials if a["time_zone"] == zone]
    if matches:
        return min(1.0, base + 0.05)
    # 跨区佐证
    if zone == ZONE_PAST_TO_PRESENT and any(a["semantic_type"] in ("duration", "since_start") for a in adverbials):
        return min(1.0, base + 0.05)
    return max(0.4, base - 0.05)


# 让外部可直接调用本模块内的函数
__all__ = ["analyze", "ADVERBIAL_RULES", "TENSE_PRESENT", "TENSE_PAST", "TENSE_FUTURE_WILL",
           "TENSE_FUTURE_GOING", "TENSE_PAST_FUTURE_WOULD", "TENSE_PAST_FUTURE_GOING",
           "TENSE_PRESENT_PROG", "TENSE_PAST_PROG", "TENSE_PRESENT_PERFECT", "TENSE_PAST_PERFECT"]
