import type { PhraseNodeInfo } from '../types';

/**
 * Quota 是前端派生(spec §4.7):DFS 数当前 phrase 树的 modifier,对照静态规则表。
 * 后端响应永不含 quota 字段(架构铁律)。
 */

// 扩展类型枚举(对应后端 ExpansionCandidate.kind)
export type ExpansionKind =
  | 'adjective'
  | 'adverb'
  | 'number'
  | 'degree_adverb'
  | 'prepositional_phrase'
  | 'relative_clause'
  | 'modal'
  | 'perfect'
  | 'progressive';

type PhraseTypeKey = PhraseNodeInfo['type'];

// 静态规则表:NP:adj≤2, number≤1, pp≤1, relcl≤1 / VP:adv≤2, modal≤1, perfect≤1, progressive≤1 / ADJP/ADVP:degree≤2
export const QUOTA_RULES: Record<PhraseTypeKey, Partial<Record<ExpansionKind, number>>> = {
  NP: { adjective: 2, number: 1, prepositional_phrase: 1, relative_clause: 1 },
  VP: { adverb: 2, modal: 1, perfect: 1, progressive: 1 },
  ADJP: { degree_adverb: 2 },
  ADVP: { degree_adverb: 2 },
  PP: {},
  CLAUSE: {},
  OTHER: {},
};

export interface PhraseQuota {
  used: number;
  max: number;
  reached: boolean;
}

export type QuotaMap = Record<string, Record<ExpansionKind, PhraseQuota>>;

/**
 * 从当前 phrases 树 DFS 数每个短语各 kind 的已用配额。
 * 简化版:遍历 phrases 数组,直接看 children_ids 递归。
 */
export function computeQuotas(phrases: PhraseNodeInfo[]): QuotaMap {
  const quotaMap: QuotaMap = {};

  // 1. 初始化每个 phrase 的 quota 结构
  for (const phrase of phrases) {
    const rules = QUOTA_RULES[phrase.type] ?? {};
    const record: Record<ExpansionKind, PhraseQuota> = {} as Record<ExpansionKind, PhraseQuota>;
    for (const [kind, max] of Object.entries(rules)) {
      if (max !== undefined) {
        record[kind as ExpansionKind] = { used: 0, max, reached: false };
      }
    }
    quotaMap[phrase.id] = record;
  }

  // 2. 统计每个父 phrase 下属的子 phrase type 对应 kind
  for (const phrase of phrases) {
    if (phrase.children_ids.length === 0) continue;
    const parent = quotaMap[phrase.id];
    if (!parent) continue;

    for (const childId of phrase.children_ids) {
      const child = phrases.find((p) => p.id === childId);
      if (!child) continue;

      // 简化映射:child.type → parent 上的 kind
      // NP 下的 ADJP/adjective, NP 下的 NP(数词)/number, VP 下的 ADVP/adverb
      // ADJP 下的 ADVP(degree)/degree_adverb
      const kind = mapChildTypeToKind(child.type, phrase.type);
      if (kind && parent[kind]) {
        parent[kind].used += 1;
        if (parent[kind].used >= parent[kind].max) {
          parent[kind].reached = true;
        }
      }
    }
  }

  return quotaMap;
}

function mapChildTypeToKind(childType: PhraseTypeKey, parentType: PhraseTypeKey): ExpansionKind | null {
  if (parentType === 'NP') {
    if (childType === 'ADJP') return 'adjective';
    if (childType === 'NP') return 'number';
    if (childType === 'PP') return 'prepositional_phrase';
  }
  if (parentType === 'VP') {
    if (childType === 'ADVP') return 'adverb';
  }
  if (parentType === 'ADJP' || parentType === 'ADVP') {
    if (childType === 'ADVP') return 'degree_adverb';
  }
  return null;
}
