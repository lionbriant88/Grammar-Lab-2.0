"""句子解剖 (Anatomy) 分析 - 基于 spaCy 依存关系

把一个英文句子按 **语义块** 切开,并识别主从分句:

输出三大块:
  - chunks : 语义块(主语 / 谓语 / 宾语 / 状语 / 从句),按词序排列,
             每个 chunk 携带 role、中文 label、覆盖的 token 索引(供前端编辑搬移)。
  - clauses: 主从分句分解(主句 + 定语/状语/宾语从句),每句含内部成分。
  - summary: 块数 / 分句数 / 是否含从句 / 警告。

设计要点:
  - 主干 root = 句子根 token (dep_ == 'ROOT')。
  - **逐词归类**:遍历整句,按每个 token 的 dep_ 决定角色,连续同角色 token
    合并成一个 chunk。相比用 token.subtree 切块,逐词策略对复合句更稳健
    (en_core_web_sm 对主从复合句的依存分析常把从句树错误挂在 aux 下,
     subtree 切法会把主语��并入谓语块)。
  - **从句剥离**:扫 dep_ in {relcl, advcl, ccomp, acl, csubj} 的 token,
    其 subtree 里的所有词标为 in_clause;这些词归入从句块,不再重复出现在
    主句块里。
  - 谓语块 = root + aux/auxpass/neg/advmod/prt(助动词、否定、副词、短语动词小词)。
  - 从句类型映射:relcl/acl→定语从句, advcl→状语从句, ccomp/csubj→宾语从句。

注:spaCy en_core_web_sm 对复杂句的分析必然有错;前端提供手动��辑模式兜底。
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Set, Tuple

from .nlp_loader import nlp_loader

# ----------------------------- 常量 -----------------------------

# 从句引导依存标签
CLAUSE_DEPS: Set[str] = {"relcl", "advcl", "ccomp", "acl", "csubj"}

# 从句类型映射: dep_ -> (kind, 中文 label)
CLAUSE_KIND_MAP: Dict[str, Tuple[str, str]] = {
    "relcl": ("relative", "定语从句"),
    "acl": ("relative", "定语从句"),
    "advcl": ("adverbial", "状语从句"),
    "ccomp": ("object_clause", "宾语从句"),
    "csubj": ("object_clause", "宾语从句"),
}

# 角色常量
ROLE_SUBJECT = "subject"
ROLE_PREDICATE = "predicate"
ROLE_OBJECT = "object"
ROLE_ADVERBIAL = "adverbial"
ROLE_CLAUSE = "clause"
ROLE_PUNCT = "punct"

# 角色 → 中文标签
ROLE_LABEL_CN: Dict[str, str] = {
    ROLE_SUBJECT: "主语",
    ROLE_PREDICATE: "谓语",
    ROLE_OBJECT: "宾语",
    ROLE_ADVERBIAL: "状语",
    ROLE_CLAUSE: "从句",
    ROLE_PUNCT: "标点",
}

# 角色说明(前端点击块时展示)
ROLE_DESC_CN: Dict[str, str] = {
    ROLE_SUBJECT: "动作的执行者或被描述的对象",
    ROLE_PREDICATE: "句子的核心动作(含助动词、否定、副词)",
    ROLE_OBJECT: "动作的承受者或介词短语",
    ROLE_ADVERBIAL: "修饰动作的时间、地点、方式等",
    ROLE_CLAUSE: "作为成分的从句(定语/状语/宾语)",
}

# 依存标签 → 角色
# 谓语相关(挂在 root 上,与主动词一起构成谓语块)
PRED_AUX_DEPS: Set[str] = {"aux", "auxpass", "neg", "advmod", "prt"}
# 宾语/状语相关(放在 object 或 adverbial 块)
OBJECT_DEPS: Set[str] = {"dobj", "attr", "dative", "oprd", "agent"}
# 介词短语 / 名词性状语 → 视作状语块(含其 pobj/nummod 等子节点)
ADVERBIAL_DEPS: Set[str] = {"prep", "npadvmod", "advmod", "possessive", "parataxis"}
# 名词块内部成分(归并到最近的 subject/object 头)
NOUN_INNER_DEPS: Set[str] = {"det", "compound", "amod", "nummod", "poss", "nmod", "pobj", "nummod"}
# 主语标签
SUBJECT_DEPS: Set[str] = {"nsubj", "nsubjpass", "expl", "csubj"}


# ----------------------------- 主分析器 -----------------------------

def analyze(sentence: str) -> Dict[str, Any]:
    """主入口:返回完整 anatomy 响应字典。"""
    sentence_clean = (sentence or "").strip()
    if not sentence_clean:
        return _empty_response("")

    nlp = nlp_loader.get()
    doc = nlp(sentence_clean)

    if len(doc) == 0:
        return _empty_response(sentence_clean)

    # 单句处理(取第一个 sent;多句时其余忽略,符合教学单句场景)
    sents = list(doc.sents)
    root = sents[0].root if sents else doc[0]

    warnings: List[str] = []

    # 1. 找出所有从句子树,收集 in-clause 词索引
    clause_tokens: List[Any] = []  # 每个 clause 的根 token
    in_clause_indices: Set[int] = set()
    for t in doc:
        if t.dep_ in CLAUSE_DEPS:
            clause_tokens.append(t)
            for x in t.subtree:
                in_clause_indices.add(x.i)

    # 2. 逐词归类 → 角色序列
    token_roles: List[str] = [ROLE_PUNCT] * len(doc)  # 默认标点兜底
    for t in doc:
        token_roles[t.i] = _classify_token(t, root, in_clause_indices)

    # 3. 构造 chunks:连续同角色合并;从句单列
    chunks = _build_chunks(doc, token_roles, in_clause_indices, clause_tokens, sentence_clean)

    # 4. 构造 clauses:主句 + 各从句
    clauses = _build_clauses(doc, root, clause_tokens, token_roles, in_clause_indices)

    # 5. summary
    has_sub = len(clause_tokens) > 0
    if root.pos_ not in ("VERB", "AUX") and root.dep_ == "ROOT":
        # 没有 verb root(纯名词句等)
        warnings.append("未识别到明确的主谓结构,可能为短语或不完整句。")

    return {
        "sentence": sentence_clean,
        "chunks": chunks,
        "clauses": clauses,
        "summary": {
            "chunk_count": len(chunks),
            "clause_count": len(clauses),
            "has_subordinate_clause": has_sub,
            "warnings": warnings,
        },
    }


def _empty_response(sentence: str) -> Dict[str, Any]:
    return {
        "sentence": sentence,
        "chunks": [],
        "clauses": [],
        "summary": {
            "chunk_count": 0,
            "clause_count": 0,
            "has_subordinate_clause": False,
            "warnings": ["空句子"],
        },
    }


# ----------------------------- 内部函数 -----------------------------

def _classify_token(tok: Any, root: Any, in_clause: Set[int]) -> str:
    """给单个 token 归一个角色。"""
    # 从句内的词交给从句块处理(标记占位,后续构造 chunks 时合并)
    # 注意:从句根 token 自身不在此集合(它触发从句),其 subtree 含自身
    if tok.i in in_clause:
        return ROLE_CLAUSE

    if tok.dep_ == "punct" or tok.pos_ == "PUNCT":
        return ROLE_PUNCT

    if tok == root:
        return ROLE_PREDICATE

    # root 的谓语相关子节点 → 谓语
    if tok.dep_ in PRED_AUX_DEPS and tok.head == root:
        return ROLE_PREDICATE

    # 主语
    if tok.dep_ in SUBJECT_DEPS:
        return ROLE_SUBJECT

    # 宾语
    if tok.dep_ in OBJECT_DEPS:
        return ROLE_OBJECT

    # 介词短语 / 状语
    if tok.dep_ in ADVERBIAL_DEPS:
        # 介词短语的引导词 at/on/in + 宾语整体作状语
        return ROLE_ADVERBIAL

    # 名词块内部成分:归并到所在名词块的角色(主语或宾语)
    # 判断该 token 所属名词块的头是不是主语/宾语
    if tok.dep_ in NOUN_INNER_DEPS:
        head_role = _head_role(tok.head, root)
        return head_role

    # 兜底:标点
    return ROLE_PUNCT


def _head_role(tok: Any, root: Any) -> str:
    """判断一个名词块的 head token 应属主语还是宾语(向上追溯到 root 的直接子节点)。"""
    cur = tok
    # 向上找,直到 root 的直接子节点或 root 本身
    while cur != root and cur.head != root and cur.head is not None:
        cur = cur.head
        if cur == root:
            break
    if cur == root:
        return ROLE_PREDICATE
    if cur.dep_ in SUBJECT_DEPS:
        return ROLE_SUBJECT
    if cur.dep_ in OBJECT_DEPS:
        return ROLE_OBJECT
    if cur.dep_ in ADVERBIAL_DEPS:
        return ROLE_ADVERBIAL
    return ROLE_ADVERBIAL  # 名词性成分默认归状语(介词宾语等)


def _build_chunks(
    doc: Any,
    token_roles: List[str],
    in_clause: Set[int],
    clause_tokens: List[Any],
    sentence: str,
) -> List[Dict[str, Any]]:
    """按词序合并连续同角色 token 成 chunk;从句单独成块(按出现位置插入)。

    策略:遍历 doc,跳过从句内 token(它们会被作为从句块按其根 token 首位置插入),
    其余连续同角色 token 合并;遇到从句根 token 时在其位置插入一个从句块。
    """
    # 建从句根 token.i -> clause 数据(用 subtree 文本)
    clause_at: Dict[int, Dict[str, Any]] = {}
    clause_subtree_index_set: Set[int] = set()
    for ct in clause_tokens:
        indices = sorted(x.i for x in ct.subtree)
        for x in ct.subtree:
            clause_subtree_index_set.add(x.i)
        kind, label = CLAUSE_KIND_MAP.get(ct.dep_, ("relative", "定语从句"))
        clause_at[ct.i] = {
            "role": ROLE_CLAUSE,
            "text": " ".join(doc[i].text for i in indices),
            "label": label,
            "subordinate": kind,
            "_indices": indices,
        }

    chunks: List[Dict[str, Any]] = []
    cid = 0
    i = 0
    n = len(doc)
    while i < n:
        tok = doc[i]
        # 若是从句根 token,插入从句块,并跳过整段从句 token
        if tok.i in clause_at:
            c = clause_at[tok.i]
            chunk = {
                "id": f"c{cid}",
                "role": c["role"],
                "text": c["text"],
                "label": c["label"],
                "subordinate": c["subordinate"],
                "token_indices": c["_indices"],
            }
            chunks.append(chunk)
            cid += 1
            # 跳过从句 subtree
            i = max(c["_indices"]) + 1
            continue

        # 跳过被从句吞掉但根 token 之外的词(理论上已被 clause_at 段跳过)
        if tok.i in clause_subtree_index_set and tok.i not in clause_at:
            i += 1
            continue

        role = token_roles[i]
        # 合并连续同角色(且都不在从句内)的 token
        j = i
        indices: List[int] = []
        while j < n:
            tj = doc[j]
            if tj.i in clause_at:
                break
            if tj.i in clause_subtree_index_set:
                break
            if token_roles[j] != role:
                break
            indices.append(j)
            j += 1
        text = " ".join(doc[k].text for k in indices)
        chunk = {
            "id": f"c{cid}",
            "role": role,
            "text": text,
            "label": ROLE_LABEL_CN.get(role, role),
            "subordinate": None,
            "token_indices": indices,
        }
        chunks.append(chunk)
        cid += 1
        i = j if j > i else i + 1

    # 过滤掉空文本块(理论上不出现)
    return [c for c in chunks if c["text"]]


def _build_clauses(
    doc: Any,
    root: Any,
    clause_tokens: List[Any],
    token_roles: List[str],
    in_clause: Set[int],
) -> List[Dict[str, Any]]:
    """构造主句 + 各从句。主句 = 不在从句内的 token;从句按各自 subtree。"""
    clauses: List[Dict[str, Any]] = []

    # ---- 主句 ----
    main_indices = [t.i for t in doc if t.i not in in_clause]
    if main_indices:
        main_text = " ".join(doc[i].text for i in main_indices)
        main_elements = _extract_elements(doc, main_indices, token_roles, is_main=True)
        clauses.append({
            "id": "cl0",
            "kind": "main",
            "text": main_text,
            "label": "主句",
            "elements": main_elements,
        })

    # ---- 从句 ----
    sub_clause_tokens = sorted(clause_tokens, key=lambda t: t.i)
    for idx, ct in enumerate(sub_clause_tokens, start=1):
        indices = sorted(x.i for x in ct.subtree)
        text = " ".join(doc[i].text for i in indices)
        kind, label = CLAUSE_KIND_MAP.get(ct.dep_, ("relative", "定语从句"))
        # 从句内成分:用同样归类逻辑,但以从句根为主干
        elements = _extract_elements(doc, indices, token_roles, is_main=False, clause_root=ct)
        # 找先行词(定语从句修饰的名词 = 从句根的 head)
        antecedent = None
        if kind == "relative" and ct.head is not None:
            antecedent = ct.head.text
        clauses.append({
            "id": f"cl{idx}",
            "kind": kind,
            "text": text,
            "label": label,
            "antecedent": antecedent,
            "elements": elements,
        })

    return clauses


def _extract_elements(
    doc: Any,
    indices: List[int],
    token_roles: List[str],
    is_main: bool,
    clause_root: Any = None,
) -> List[Dict[str, str]]:
    """从一个分句的 token 索引里提取「主语/谓语/宾语/状语」成分标签序列。

    用于 ClauseBreakdown 卡片正文里的 [主语] 文本 inline 标签。
    - 主句 (is_main=True):直接复用已算好的全局 token_roles,按角色合并。
    - 从句 (is_main=False, clause_root 给出):用 _role_within_clause 以从句根
      为本地主干重新归类。
    """
    if not indices:
        return []

    def role_of(doc_idx: int) -> str:
        tok = doc[doc_idx]
        if is_main:
            return token_roles[doc_idx]
        return _role_within_clause(tok, clause_root)

    elements: List[Dict[str, str]] = []
    i = 0
    n = len(indices)
    while i < n:
        role = role_of(indices[i])
        j = i
        while j < n and role_of(indices[j]) == role:
            j += 1
        seg = indices[i:j]
        text = " ".join(doc[k].text for k in seg)
        # 过滤掉纯标点(不作为分句成分展示)
        if role == ROLE_PUNCT:
            i = j
            continue
        elements.append({
            "word": text,
            "label": ROLE_LABEL_CN.get(role, role),
            "class": role,
        })
        i = j
    return [e for e in elements if e["word"]]


def _role_within_clause(tok: Any, clause_root: Any) -> str:
    """从句内的 token 角色归类(主语/谓语/宾语/状语/标点)。

    以 clause_root 为本地主干:clause_root 自身 + 其 aux/neg/advmod/prt = 谓语。
    """
    if tok.dep_ == "punct" or tok.pos_ == "PUNCT":
        return ROLE_PUNCT
    if tok == clause_root:
        return ROLE_PREDICATE
    if tok.dep_ in PRED_AUX_DEPS and tok.head == clause_root:
        return ROLE_PREDICATE
    if tok.dep_ in SUBJECT_DEPS:
        return ROLE_SUBJECT
    if tok.dep_ in OBJECT_DEPS:
        return ROLE_OBJECT
    # 关系词 who/which/that 在从句里可能作 dobj/nsubj/obj
    if tok.dep_ in ("obj", "obl", "expl"):
        return ROLE_OBJECT
    # 名词内部 / 介词短语 → 状语
    if tok.dep_ in ADVERBIAL_DEPS or tok.dep_ in NOUN_INNER_DEPS:
        # 若其 head 是宾语,跟随归宾语
        if tok.head.dep_ in OBJECT_DEPS and tok.head.head == clause_root:
            return ROLE_OBJECT
        return ROLE_ADVERBIAL
    return ROLE_ADVERBIAL


__all__ = ["analyze"]
