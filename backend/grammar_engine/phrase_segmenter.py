"""短语识别 (Phrase Segmentation) — M3a 过渡实现(无 Benepar)

把一个英文句子切成 **短语节点** (NP / VP / PP / ADJP / ADVP / CLAUSE),
每个节点带 **特征槽** (features) 和 **Parent-Child 挂载关系** (parent_id / children_ids)。

这是 spec §2.0 原则 #1/#2/#6 的代码化:
  - 原则 #1/#2:扩展单位是短语(NP/VP/PP),不是单个 token。
  - 原则 #6:特征槽(NP: number/person;VP: tense/modal/aux_chain/aspect)。
  - 调整 1/2:Parent-Child 挂载 + VP 完整时态链(见 spec §2.2)。

设计精神(最高优先级):**数据模型稳定优先于分析精度**。
M3a 不追求句法分析精度,只保证 PhraseNode 字段集稳定 —— M3b 装 Benepar
时,只需替换 `segment()` 的函数体,数据模型与返回契约保持不变。

流程(过渡实现,基于 spaCy `noun_chunks` + `dep_`):
  1. NP  : doc.noun_chunks → 带 number/person 特征
  2. VP  : 从每个主动词(ROOT / VERB)向前回溯,吞掉连续 auxiliaries + modal +
           main verb + particles(prt dep_)→ 合成一个 VP span,features 含
           aux_chain / modal / aspect / tense。
           - `has been working` → 一个 VP(present_perfect_progressive)
           - `would like`      → 一个 VP(modal="would")
           - `to help`         → **不纳入 VP**(留 M3b 的 infinitive phrase)
  3. PP  : 介词(ADP / prep dep)引导的 chunk → PP。
           挂载规则(调整 1 简化版):
             - PP 紧跟一个 NP(右侧相邻,且该 NP 在 PP 左边)→ parent_id = 该 NP
             - PP 紧跟一个 VP(右侧相邻)→ parent_id = 该 VP
             - 否则 PP 顶层漂浮(parent_id=None)
           例:`likes the dog in the park` → PP(`in the park`).parent_id = NP(`the dog`)
  4. 其余 token(冠词已被 noun_chunks 吞入 NP / 连词 / 标点)不单独成节点。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

# ----------------------------- 类型常量 -----------------------------

PhraseType = Literal["NP", "VP", "PP", "ADJP", "ADVP", "CLAUSE", "OTHER"]

# 语法角色(对齐 anatomy 的角色值,供 Validator 读 NP 的 subject / VP 的 predicate)
ROLE_SUBJECT = "subject"
ROLE_PREDICATE = "predicate"
ROLE_OBJECT = "object"
ROLE_ADVERBIAL = "adverbial"
ROLE_OTHER = "other"

# 代词 → (person, number) 映射(en_core_web_sm 的 morph 对部分代词 person 缺失,兜底)
PRONOUN_FEATURES: Dict[str, Tuple[int, str]] = {
    "i": (1, "singular"),
    "me": (1, "singular"),
    "we": (1, "plural"),
    "us": (1, "plural"),
    "you": (2, "singular"),   # you 单复同形,默认 singular
    "he": (3, "singular"),
    "him": (3, "singular"),
    "she": (3, "singular"),
    "her": (3, "singular"),
    "it": (3, "singular"),
    "they": (3, "plural"),
    "them": (3, "plural"),
}

# 常见情态动词(M3a 用 token.text 小写匹配;spaCy 把 modal 也标 dep_=aux)
MODAL_WORDS: set = {
    "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "ought",
}

# 高频动词 lemma 兜底:spaCy 小模型偶尔把动词误标 ADP/ROOT(如 `He like dogs.` /
# `I beautiful like dogs.`),靠 lemma 兜底仍识别为谓语头。M3a 不追求全覆盖,
# 只兜教学常用句的动词。
VERB_LEMMA_FALLBACK: set = {
    "be", "have", "do", "go", "get", "like", "love", "want", "need",
    "run", "walk", "eat", "drink", "see", "look", "make", "take",
    "work", "play", "study", "help", "live", "give", "come", "know",
    "think", "say", "tell", "ask", "drive", "read", "write", "sing",
    "sit", "stand", "sleep", "speak", "buy", "sell", "find", "open",
    "close", "start", "stop", "break", "fix", "build", "teach", "learn",
    "feel", "hear", "smell", "taste", "watch", "listen", "meet", "call",
}


@dataclass
class PhraseNode:
    """短语节点。

    字段集为 M3b/M3c 预留稳定契约:装 Benepar / 接 LanguageTool 时只填不同来源
    的数据,不改字段定义。
    """

    id: str
    type: PhraseType
    text: str
    head_token_text: str
    head_pos: str
    syntactic_role: str
    span: Tuple[int, int]
    # 特征槽(原则 #6)——M3a 仅 NP/VP 填充
    features: Dict[str, Any] = field(default_factory=dict)
    # Parent-Child 挂载(调整 1)——M3a 建立内部挂载,右栏不显示
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    # 扩展候选(由 expansion_engine 填充,segment 时留空)
    is_expandable: bool = False
    candidates: List[Any] = field(default_factory=list)
    # 内部用:该短语覆盖的 token 索引(不入 API 响应)
    token_indices: List[int] = field(default_factory=list)


# ----------------------------- 主入口 -----------------------------

def segment(doc: Any) -> List[PhraseNode]:
    """M3a 短语识别(过渡实现,无 Benepar)。

    返回扁平 list[PhraseNode],按句中出现的字符顺序排列。每个节点内部已具备
    parent_id / children_ids,可重建树结构(调整 1:即使 M3a 不显示关系树,
    也必须建立内部挂载)。

    M3b 升级:函数体改用 Benepar 成分树,parent_id/children_ids 直接来自
    Benepar 的嵌套结构,无需改数据模型 / 返回契约。
    """
    if len(doc) == 0:
        return []

    # 1. NP:遍历 noun_chunks,带 number/person 特征
    np_nodes: List[PhraseNode] = []
    np_index_set: set = set()  # 被 NP 覆盖的 token 索引
    for idx, chunk in enumerate(doc.noun_chunks):
        indices = [t.i for t in chunk]
        np_index_set.update(indices)
        head = chunk.root  # noun_chunk 的 root 是中心名词
        role = _np_syntactic_role(head)
        features = _np_features(head)
        np_nodes.append(PhraseNode(
            id=f"p{idx}",
            type="NP",
            text=chunk.text,
            head_token_text=head.text,
            head_pos=head.pos_,
            syntactic_role=role,
            span=(chunk.start_char, chunk.end_char),
            features=features,
            token_indices=indices,
        ))

    # 2. VP:从每个主动词(ROOT 或 VERB)向前回溯吞 aux + modal + particle
    #    排除已被 NP 覆盖的 token,排除 xcomp(如 `to help`,留 M3b)
    vp_nodes: List[PhraseNode] = []
    vp_index_set: set = set()
    used_heads: set = set()
    pid = len(np_nodes)
    for t in doc:
        is_predicate_head = (
            (t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX"))
            or (t.pos_ == "VERB" and t.dep_ in ("ROOT", "conj"))
        )
        # 兜底:spaCy 偶尔把动词误标 ADP/ROOT(如 `He like dogs.` 的 like 被标 ADP;
        # `I beautiful like` 的 like 被标 ADP)。若 ROOT 是非 VERB 但 lemma 命中
        # 常见动词,仍当作谓语头,避免丢失 VP。
        if t.dep_ == "ROOT" and t.pos_ not in ("VERB", "AUX"):
            if t.lemma_.lower() in VERB_LEMMA_FALLBACK:
                is_predicate_head = True
        # xcomp(不定式补语,如 would like 里的 `to help`)不作为独立 VP
        if t.dep_ == "xcomp":
            continue
        if not is_predicate_head or t.i in used_heads:
            continue

        vp_data = _build_vp(doc, t)
        if vp_data is None:
            continue
        indices, aux_chain, modal, head_tok = vp_data
        used_heads.update(indices)
        vp_index_set.update(indices)
        features = _vp_features(head_tok, aux_chain, modal)
        vp_nodes.append(PhraseNode(
            id=f"p{pid}",
            type="VP",
            text=" ".join(doc[i].text for i in indices),
            head_token_text=head_tok.text,
            head_pos=head_tok.pos_,
            syntactic_role=ROLE_PREDICATE,
            span=(doc[indices[0]].idx, doc[indices[-1]].idx + len(doc[indices[-1]].text)),
            features=features,
            token_indices=indices,
        ))
        pid += 1

    # 3. PP:介词(ADP / prep dep)引导 → PP,挂载到相邻 NP/VP(调整 1)
    pp_nodes: List[PhraseNode] = []
    pp_index_set: set = set()
    for t in doc:
        if t.pos_ == "ADP" or t.dep_ == "prep":
            # 收集该介词的 subtree(介词 + 其宾语 + 宾语的限定词等)
            indices = sorted(x.i for x in t.subtree if x.pos_ != "PUNCT")
            # 避免吞掉已被 VP 覆盖的主动词本身
            indices = [i for i in indices if i not in vp_index_set or i in _prep_subtree_core(doc, t)]
            if not indices:
                continue
            span_start = doc[min(indices)].idx
            last = doc[max(indices)]
            span_end = last.idx + len(last.text)
            # head 介词本身是 PP 的中心?教学上 PP 中心是介词,但这里 head_token
            # 用介词的宾语名词更便于后续 NP 规则判断。M3a 用介词文本作 head_text,
            # head_pos 用介词 pos,role=adverbial。
            pp_nodes.append(PhraseNode(
                id=f"p{pid}",
                type="PP",
                text=" ".join(doc[i].text for i in indices),
                head_token_text=t.text,
                head_pos=t.pos_,
                syntactic_role=ROLE_ADVERBIAL,
                span=(span_start, span_end),
                features={},
                token_indices=indices,
            ))
            pp_index_set.update(indices)
            pid += 1

    # 4. 合并 + 按字符起始位置排序(扁平序列)
    all_nodes: List[PhraseNode] = np_nodes + vp_nodes + pp_nodes
    all_nodes.sort(key=lambda n: n.span[0])

    # 5. 调整 1:建立 Parent-Child 挂载(PP → 相邻 NP / VP)
    _attach_pps(all_nodes)

    return all_nodes


# ----------------------------- 内部函数 -----------------------------

def _np_syntactic_role(head: Any) -> str:
    """判断 NP 中心名词的语法角色(主语/宾语/其他)。"""
    dep = head.dep_
    if dep in ("nsubj", "nsubjpass", "csubj", "expl"):
        return ROLE_SUBJECT
    if dep in ("dobj", "obj", "attr", "dative", "oprd", "pobj", "iobj"):
        return ROLE_OBJECT
    return ROLE_OTHER


def _np_features(head: Any) -> Dict[str, Any]:
    """提取 NP 的特征槽:number / person。

    优先用 spaCy morph;代词用兜底词表(morph 对部分代词 person 缺失)。
    """
    text_lower = head.text.lower()
    if text_lower in PRONOUN_FEATURES:
        person, number = PRONOUN_FEATURES[text_lower]
        return {"number": number, "person": person}

    number = "plural"
    person: Any = 3
    morph = head.morph
    num_morph = morph.get("Number")
    if num_morph:
        number = "singular" if "Sing" in num_morph else "plural"
    per_morph = morph.get("Person")
    if per_morph:
        person = int(per_morph[0])
    return {"number": number, "person": person}


def _build_vp(
    doc: Any, main_verb: Any
) -> Optional[Tuple[List[int], List[str], Optional[str], Any]]:
    """从主动词向前回溯,吞掉连续 auxiliaries + modal,合成 VP token 索引序列。

    返回 (indices, aux_chain, modal, head_token)。
    - aux_chain:按句中顺序的助动词文本列表(不含 modal)
    - modal:情态动词文本(若有)
    - to help(xcomp)不纳入
    """
    # 收集挂在主动词下的 aux(且不是 xcomp/advcl 等从句根)
    aux_indices: List[int] = []
    aux_chain: List[str] = []
    modal: Optional[str] = None
    for child in main_verb.children:
        if child.dep_ == "aux" and child.i < main_verb.i:
            if child.text.lower() in MODAL_WORDS:
                modal = child.text.lower()
            else:
                aux_chain.append(child.text)
            aux_indices.append(child.i)
        elif child.dep_ == "aux" and child.i > main_verb.i and child.pos_ == "AUX":
            # 后置助动词(罕见,如疑问句倒装)——M3a 不处理复杂倒装,保守吞掉连续的
            aux_chain.append(child.text)
            aux_indices.append(child.i)

    # 收集 particle(prt dep_,短语动词小词,如 give up 的 up)
    prt_indices: List[int] = [
        child.i for child in main_verb.children if child.dep_ == "prt"
    ]

    indices = sorted(aux_indices + [main_verb.i] + prt_indices)
    return indices, aux_chain, modal, main_verb


def _vp_features(
    head_verb: Any, aux_chain: List[str], modal: Optional[str]
) -> Dict[str, Any]:
    """提取 VP 的特征槽:tense / modal / aux_chain / aspect。

    tense 推断(简化,基于 morph + aux 链):
      - 含 modal → "modal"
      - 含 have + been + Ving → present_perfect_progressive
      - 含 have + Ving(be 的 ing)→ present_perfect / past_perfect(看 have 的时态)
      - 含 be + Ving → progressive(看 be 的时态:present/past)
      - 主动词 morph Tense=Pres 且 VerbForm=Fin → simple_present
      - 主动词 morph Tense=Past → simple_past
      - 其余 → "unknown"
    """
    morph = head_verb.morph
    aux_lower = [a.lower() for a in aux_chain]
    has_have = any(a in ("has", "have", "had") for a in aux_lower)
    has_be = any(a in ("is", "are", "was", "were", "am", "be", "been", "being") for a in aux_lower)
    verb_form = morph.get("VerbForm")
    main_is_participle = "Part" in (verb_form or [])

    aspect = "simple"
    tense = "unknown"

    if modal is not None:
        tense = "modal"
        aspect = "modal"
    elif has_have and has_be and main_is_participle:
        # has/have/had + been + Ving → perfect progressive
        aspect = "perfect_progressive"
        tense = _perfect_progressive_tense(aux_lower)
    elif has_have and main_is_participle:
        aspect = "perfect"
        tense = _perfect_tense(aux_lower)
    elif has_be and main_is_participle:
        aspect = "progressive"
        tense = _be_tense(aux_lower)
    else:
        mtense = morph.get("Tense")
        if mtense:
            tense = "simple_present" if "Pres" in mtense else "simple_past"
            aspect = "simple"
        elif "Inf" in (verb_form or []):
            tense = "infinitive"
            aspect = "simple"

    return {
        "tense": tense,
        "modal": modal,
        "aux_chain": aux_chain,
        "aspect": aspect,
    }


def _perfect_tense(aux_lower: List[str]) -> str:
    """have/has → present_perfect;had → past_perfect。"""
    if "had" in aux_lower:
        return "past_perfect"
    return "present_perfect"


def _perfect_progressive_tense(aux_lower: List[str]) -> str:
    """have/has been Ving → present_perfect_progressive;had been Ving → past_perfect_progressive。"""
    if "had" in aux_lower:
        return "past_perfect_progressive"
    return "present_perfect_progressive"


def _be_tense(aux_lower: List[str]) -> str:
    """be 的进行体:is/am/are → present_progressive;was/were → past_progressive。"""
    if any(a in ("was", "were") for a in aux_lower):
        return "past_progressive"
    return "present_progressive"


def _prep_subtree_core(doc: Any, prep: Any) -> List[int]:
    """介词 subtree 的核心索引(介词自身 + pobj/nummod/det 等),排除已被 VP 吞的主动词。"""
    core = []
    for x in prep.subtree:
        if x.pos_ == "PUNCT":
            continue
        core.append(x.i)
    return core


def _attach_pps(nodes: List[PhraseNode]) -> None:
    """调整 1:建立 PP → 相邻 NP/VP 的 Parent-Child 挂载。

    简化规则(spec §2.2):
      - 找到 PP 字符区间左侧紧邻的 NP → parent_id = 该 NP
      - 否则左侧紧邻的 VP → parent_id = 该 VP
      - 否则漂浮(parent_id=None)
    回填父节点的 children_ids。
    """
    nps_vps = [n for n in nodes if n.type in ("NP", "VP")]
    for pp in nodes:
        if pp.type != "PP":
            continue
        pp_start = pp.span[0]
        # 左侧相邻:span 结束 <= pp_start,取最靠近的那个
        candidates = [n for n in nps_vps if n.span[1] <= pp_start]
        if candidates:
            parent = max(candidates, key=lambda n: n.span[1])
            pp.parent_id = parent.id
            if pp.id not in parent.children_ids:
                parent.children_ids.append(pp.id)


__all__ = ["PhraseType", "PhraseNode", "segment"]
