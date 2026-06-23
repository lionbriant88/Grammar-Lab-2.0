"""Benepar-based Phrase Segmentation (M3b)

使用 Berkeley Neural Parser 进行成分句法分析，产出高精度的短语树。

架构原则:
- 数据模型与 M3a spaCy 版本完全相同 (PhraseNode)
- 返回契约相同 (List[PhraseNode])
- Parent-Child 挂载直接来自 Benepar 树结构
- verb_form 特征从 Benepar VP 子树提取
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from .phrase_segmenter import PhraseNode, PRONOUN_FEATURES, MODAL_WORDS


def segment_benepar(doc: Any, parser: Any) -> List[PhraseNode]:
    """使用 Benepar 进行短语识别。

    参数:
    - doc: spaCy Doc 对象
    - parser: benepar.Parser 实例

    返回:
    - List[PhraseNode]: 扁平短语列表，按字符位置排序

    流程:
    1. parser.parse(doc.sents) → nltk.Tree
    2. DFS 遍历树，非终结符 → PhraseNode
    3. 填充 features (NP: number/person; VP: verb_form/tense/aux_chain)
    4. 填充 M3b 新字段 (head_word/role/modifiers)
    5. 返回扁平列表
    """
    if len(doc) == 0:
        return []

    all_phrases: List[PhraseNode] = []
    phrase_id_counter = 0

    # 遍历每个句子
    for sent in doc.sents:
        # Benepar 解析
        try:
            parsed = list(parser.parse(sent.text.split()))
            if not parsed:
                continue
            tree = parsed[0]
        except Exception as e:
            print(f"[WARN] Benepar parse failed for sentence: {sent.text[:50]}... Error: {e}")
            continue

        # DFS 遍历树，提取短语节点
        phrases, phrase_id_counter = _extract_phrases_from_tree(
            tree, doc, sent, phrase_id_counter
        )
        all_phrases.extend(phrases)

    # 按字符位置排序
    all_phrases.sort(key=lambda p: p.span[0])

    # 填充 modifiers 字段 (从 children 中识别修饰性短语)
    _fill_modifiers(all_phrases)

    return all_phrases


def _extract_phrases_from_tree(
    tree: Any,
    doc: Any,
    sent: Any,
    phrase_id_counter: int,
    parent_id: Optional[str] = None
) -> Tuple[List[PhraseNode], int]:
    """递归提取短语节点。

    参数:
    - tree: nltk.Tree 节点
    - doc: spaCy Doc
    - sent: spaCy Sent
    - phrase_id_counter: 当前短语 ID 计数器
    - parent_id: 父节点 ID

    返回:
    - (phrases, new_counter)
    """
    phrases: List[PhraseNode] = []

    # 只处理非终结符 (NP, VP, PP, ADJP, ADVP, S, SBAR, etc.)
    if isinstance(tree, str) or not hasattr(tree, 'label'):
        return phrases, phrase_id_counter

    label = tree.label()

    # 映射 Benepar 标签到 PhraseType
    phrase_type = _map_label_to_type(label)

    # 如果不是我们关心的短语类型，继续递归子节点
    if phrase_type == "OTHER":
        for child in tree:
            child_phrases, phrase_id_counter = _extract_phrases_from_tree(
                child, doc, sent, phrase_id_counter, parent_id
            )
            phrases.extend(child_phrases)
        return phrases, phrase_id_counter

    # 提取短语文本和 span
    leaves = tree.leaves()
    if not leaves:
        return phrases, phrase_id_counter

    phrase_text = " ".join(leaves)

    # 在 sent 中查找匹配的 token span
    token_span = _find_token_span(sent, leaves)
    if token_span is None:
        # 无法匹配，跳过
        for child in tree:
            child_phrases, phrase_id_counter = _extract_phrases_from_tree(
                child, doc, sent, phrase_id_counter, parent_id
            )
            phrases.extend(child_phrases)
        return phrases, phrase_id_counter

    start_token, end_token = token_span
    char_start = sent[start_token].idx
    char_end = sent[end_token].idx + len(sent[end_token].text)

    # 创建当前短语节点
    current_id = f"p{phrase_id_counter}"
    phrase_id_counter += 1

    # 提取 head token
    head_token = _find_head_token(sent, start_token, end_token, phrase_type)

    # 填充 features
    features = {}
    if phrase_type == "NP":
        features = _extract_np_features(head_token)
    elif phrase_type == "VP":
        features = _extract_vp_features(tree, sent, start_token, end_token)

    # 提取 syntactic_role
    syntactic_role = _infer_syntactic_role(head_token, phrase_type)

    # 创建节点
    node = PhraseNode(
        id=current_id,
        type=phrase_type,
        text=phrase_text,
        head_token_text=head_token.text,
        head_pos=head_token.pos_,
        syntactic_role=syntactic_role,
        span=(char_start, char_end),
        features=features,
        parent_id=parent_id,
        children_ids=[],
        head_word=head_token.text,  # M3b 新增
        role=syntactic_role,        # M3b 新增
        modifiers=[],               # M3b 新增，后续填充
        token_indices=[i for i in range(start_token, end_token + 1)]
    )

    phrases.append(node)

    # 递归处理子节点
    for child in tree:
        child_phrases, phrase_id_counter = _extract_phrases_from_tree(
            child, doc, sent, phrase_id_counter, current_id
        )
        for child_phrase in child_phrases:
            node.children_ids.append(child_phrase.id)
        phrases.extend(child_phrases)

    return phrases, phrase_id_counter


def _map_label_to_type(label: str) -> str:
    """映射 Benepar 标签到 PhraseType。"""
    if label.startswith("NP"):
        return "NP"
    elif label.startswith("VP"):
        return "VP"
    elif label.startswith("PP"):
        return "PP"
    elif label.startswith("ADJP"):
        return "ADJP"
    elif label.startswith("ADVP"):
        return "ADVP"
    elif label in ("S", "SBAR", "SBARQ", "SINV", "SQ"):
        return "CLAUSE"
    else:
        return "OTHER"


def _find_token_span(sent: Any, leaves: List[str]) -> Optional[Tuple[int, int]]:
    """在 sent 中查找 leaves 对应的 token span。

    返回: (start_idx, end_idx) 相对于 sent 的索引
    """
    # 简单匹配: 连续 token 文本匹配 leaves
    sent_tokens = [t.text for t in sent]
    leaves_text = " ".join(leaves)

    for i in range(len(sent)):
        candidate = " ".join(sent_tokens[i:i+len(leaves)])
        if candidate == leaves_text:
            return (i, i + len(leaves) - 1)

    # 模糊匹配: 允许大小写差异
    leaves_lower = [l.lower() for l in leaves]
    for i in range(len(sent)):
        if i + len(leaves) > len(sent):
            break
        candidate_lower = [sent[j].text.lower() for j in range(i, i + len(leaves))]
        if candidate_lower == leaves_lower:
            return (i, i + len(leaves) - 1)

    return None


def _find_head_token(sent: Any, start: int, end: int, phrase_type: str) -> Any:
    """查找短语的中心词。

    规则:
    - NP: 查找 noun 或 pronoun (pos_ = NOUN/PROPN/PRON)
    - VP: 查找主动词 (pos_ = VERB/AUX)
    - PP: 查找介词 (pos_ = ADP)
    - 其他: 返回第一个 token
    """
    tokens = [sent[i] for i in range(start, end + 1)]

    if phrase_type == "NP":
        for t in tokens:
            if t.pos_ in ("NOUN", "PROPN", "PRON"):
                return t
    elif phrase_type == "VP":
        for t in tokens:
            if t.pos_ in ("VERB", "AUX"):
                return t
    elif phrase_type == "PP":
        for t in tokens:
            if t.pos_ == "ADP":
                return t

    return tokens[0] if tokens else sent[start]


def _extract_np_features(head_token: Any) -> Dict[str, Any]:
    """提取 NP 特征: number, person。"""
    text_lower = head_token.text.lower()

    # 代词特征兜底
    if text_lower in PRONOUN_FEATURES:
        person, number = PRONOUN_FEATURES[text_lower]
        return {"number": number, "person": person}

    # 从 spaCy morph 提取
    number = "singular"
    person = 3  # 默认第三人称

    if head_token.morph:
        morph_dict = head_token.morph.to_dict()
        if "Number" in morph_dict:
            num = morph_dict["Number"].lower()
            number = "plural" if num == "plur" else "singular"
        if "Person" in morph_dict:
            try:
                person = int(morph_dict["Person"])
            except:
                person = 3

    return {"number": number, "person": person}


def _extract_vp_features(tree: Any, sent: Any, start: int, end: int) -> Dict[str, Any]:
    """提取 VP 特征: verb_form, tense, aux_chain, modal, aspect。

    M3b 新增 verb_form:
    - finite: 限定动词 (has been working)
    - present_participle: 现在分词 (running)
    - past_participle: 过去分词 (covered)
    - infinitive: 不定式 (to help)
    - gerund: 动名词 (swimming is fun)
    """
    tokens = [sent[i] for i in range(start, end + 1)]

    # 识别 verb_form
    verb_form = _identify_verb_form(tree, tokens)

    # 提取 aux_chain 和 modal
    aux_chain = []
    modal = None
    main_verb = None

    for t in tokens:
        if t.pos_ == "AUX":
            aux_chain.append(t.text.lower())
        elif t.text.lower() in MODAL_WORDS:
            modal = t.text.lower()
        elif t.pos_ == "VERB":
            main_verb = t

    # 推断 tense 和 aspect (仅对 finite VP)
    tense = "unknown"
    aspect = "simple"

    if verb_form == "finite":
        tense, aspect = _infer_tense_and_aspect(aux_chain, modal, main_verb)

    return {
        "verb_form": verb_form,
        "tense": tense,
        "aux_chain": aux_chain,
        "modal": modal,
        "aspect": aspect
    }


def _identify_verb_form(tree: Any, tokens: List[Any]) -> str:
    """识别 VP 的 verb_form。

    规则:
    - 含 TO → infinitive
    - 含 VBG 且无 aux 前置 → present_participle
    - 含 VBN 且无 aux 前置 → past_participle
    - 含 modal 或 finite verb → finite
    - VBG 作主语/宾语 → gerund (暂不实现，归为 present_participle)
    """
    # 检查是否有 TO
    for t in tokens:
        if t.pos_ == "PART" and t.text.lower() == "to":
            return "infinitive"

    # 检查 modal 或 aux
    has_aux_or_modal = any(
        t.pos_ == "AUX" or t.text.lower() in MODAL_WORDS for t in tokens
    )

    # 检查主要动词形式
    for t in tokens:
        if t.pos_ == "VERB":
            tag = t.tag_  # VB/VBZ/VBP/VBD/VBG/VBN
            if tag == "VBG" and not has_aux_or_modal:
                return "present_participle"
            elif tag == "VBN" and not has_aux_or_modal:
                return "past_participle"

    # 默认为 finite
    return "finite"


def _infer_tense_and_aspect(aux_chain: List[str], modal: Optional[str], main_verb: Any) -> Tuple[str, str]:
    """推断 tense 和 aspect (仅限 finite VP)。"""
    # 简化版本，复用 M3a 逻辑
    if modal:
        if modal in ("will", "shall"):
            return ("simple_future_will", "simple")
        else:
            return ("unknown", "simple")

    if "have" in aux_chain or "has" in aux_chain or "had" in aux_chain:
        if "been" in aux_chain:
            if "had" in aux_chain:
                return ("past_perfect_progressive", "perfect_progressive")
            else:
                return ("present_perfect_progressive", "perfect_progressive")
        else:
            if "had" in aux_chain:
                return ("past_perfect", "perfect")
            else:
                return ("present_perfect", "perfect")

    if "be" in aux_chain or "is" in aux_chain or "am" in aux_chain or "are" in aux_chain or "was" in aux_chain or "were" in aux_chain:
        if any(a in ("was", "were") for a in aux_chain):
            return ("past_progressive", "progressive")
        else:
            return ("present_progressive", "progressive")

    # Simple tense
    if main_verb:
        if main_verb.tag_ in ("VBD",):
            return ("simple_past", "simple")
        elif main_verb.tag_ in ("VBZ", "VBP", "VB"):
            return ("simple_present", "simple")

    return ("unknown", "simple")


def _infer_syntactic_role(head_token: Any, phrase_type: str) -> str:
    """推断短语的语法角色。"""
    dep = head_token.dep_

    if phrase_type == "NP":
        if dep in ("nsubj", "nsubjpass", "csubj", "expl"):
            return "subject"
        elif dep in ("dobj", "obj", "attr", "dative", "oprd", "pobj", "iobj"):
            return "object"
        else:
            return "other"
    elif phrase_type == "VP":
        if dep == "ROOT" or head_token.pos_ == "VERB":
            return "predicate"
        else:
            return "other"
    elif phrase_type == "PP":
        return "adverbial"
    else:
        return "other"


def _fill_modifiers(phrases: List[PhraseNode]) -> None:
    """填充 modifiers 字段。

    从 children 中识别修饰性短语:
    - NP 的 children 中的 ADJP → modifier
    - NP 的 children 中的 PP → modifier
    - VP 的 children 中的 ADVP → modifier
    """
    for phrase in phrases:
        if phrase.type == "NP":
            for child_id in phrase.children_ids:
                child = next((p for p in phrases if p.id == child_id), None)
                if child and child.type in ("ADJP", "PP"):
                    phrase.modifiers.append(child_id)
        elif phrase.type == "VP":
            for child_id in phrase.children_ids:
                child = next((p for p in phrases if p.id == child_id), None)
                if child and child.type == "ADVP":
                    phrase.modifiers.append(child_id)
