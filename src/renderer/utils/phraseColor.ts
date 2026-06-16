import type { PhraseType, ExpansionCandidate } from '../types';

/**
 * 短语类型 → Tailwind 配色(对齐句剖析 anatomy 场景的语义角色配色)。
 * NP=蓝(主语/宾语都是名词短语,统一蓝)、VP=绿(谓语)、PP=琥珀(状语)。
 * 与 roleColor.ts 的 ROLE_COLORS 保持视觉一致,使三栏 UI 与既有场景统一。
 */
export const PHRASE_COLORS: Record<PhraseType, {
  /** 卡片填充(浅/深自适应由 darkMode 切换,这里给两套) */
  light: string;
  dark: string;
  /** 边框高亮色(可扩展描边) */
  border: string;
  borderDark: string;
  /** 角标徽章 */
  badgeLight: string;
  badgeDark: string;
  /** 实心色(图例/圆点) */
  solid: string;
}> = {
  NP: {
    light: 'bg-blue-50 text-blue-900 border-blue-200',
    dark: 'bg-blue-500/15 text-blue-200 border-blue-500/30',
    border: 'border-blue-400',
    borderDark: 'border-blue-400',
    badgeLight: 'bg-blue-100 text-blue-700',
    badgeDark: 'bg-blue-500/25 text-blue-200',
    solid: 'bg-blue-400',
  },
  VP: {
    light: 'bg-emerald-50 text-emerald-900 border-emerald-200',
    dark: 'bg-emerald-500/15 text-emerald-200 border-emerald-500/30',
    border: 'border-emerald-400',
    borderDark: 'border-emerald-400',
    badgeLight: 'bg-emerald-100 text-emerald-700',
    badgeDark: 'bg-emerald-500/25 text-emerald-200',
    solid: 'bg-emerald-400',
  },
  PP: {
    light: 'bg-amber-50 text-amber-900 border-amber-200',
    dark: 'bg-amber-500/15 text-amber-200 border-amber-500/30',
    border: 'border-amber-400',
    borderDark: 'border-amber-400',
    badgeLight: 'bg-amber-100 text-amber-700',
    badgeDark: 'bg-amber-500/25 text-amber-200',
    solid: 'bg-amber-400',
  },
  ADJP: {
    light: 'bg-violet-50 text-violet-900 border-violet-200',
    dark: 'bg-violet-500/15 text-violet-200 border-violet-500/30',
    border: 'border-violet-400',
    borderDark: 'border-violet-400',
    badgeLight: 'bg-violet-100 text-violet-700',
    badgeDark: 'bg-violet-500/25 text-violet-200',
    solid: 'bg-violet-400',
  },
  ADVP: {
    light: 'bg-teal-50 text-teal-900 border-teal-200',
    dark: 'bg-teal-500/15 text-teal-200 border-teal-500/30',
    border: 'border-teal-400',
    borderDark: 'border-teal-400',
    badgeLight: 'bg-teal-100 text-teal-700',
    badgeDark: 'bg-teal-500/25 text-teal-200',
    solid: 'bg-teal-400',
  },
  CLAUSE: {
    light: 'bg-pink-50 text-pink-900 border-pink-200',
    dark: 'bg-pink-500/15 text-pink-200 border-pink-500/30',
    border: 'border-pink-400',
    borderDark: 'border-pink-400',
    badgeLight: 'bg-pink-100 text-pink-700',
    badgeDark: 'bg-pink-500/25 text-pink-200',
    solid: 'bg-pink-400',
  },
  OTHER: {
    light: 'bg-slate-50 text-slate-700 border-slate-200',
    dark: 'bg-slate-700/40 text-slate-300 border-slate-700',
    border: 'border-slate-300',
    borderDark: 'border-slate-500',
    badgeLight: 'bg-slate-100 text-slate-600',
    badgeDark: 'bg-slate-700/50 text-slate-300',
    solid: 'bg-slate-400',
  },
};

const FALLBACK = PHRASE_COLORS.OTHER;

/** 短语中文标签 */
export const PHRASE_LABEL_CN: Record<PhraseType, string> = {
  NP: '名词短语',
  VP: '动词短语',
  PP: '介词短语',
  ADJP: '形容词短语',
  ADVP: '副词短语',
  CLAUSE: '从句',
  OTHER: '其它',
};

export function getPhraseColor(type: PhraseType, darkMode: boolean): string {
  const c = PHRASE_COLORS[type] ?? FALLBACK;
  return darkMode ? c.dark : c.light;
}

export function getPhraseBadge(type: PhraseType, darkMode: boolean): string {
  const c = PHRASE_COLORS[type] ?? FALLBACK;
  return darkMode ? c.badgeDark : c.badgeLight;
}

export function getPhraseSolid(type: PhraseType): string {
  return (PHRASE_COLORS[type] ?? FALLBACK).solid;
}

export function getPhraseLabel(type: PhraseType): string {
  return PHRASE_LABEL_CN[type] ?? type;
}

/**
 * 把短语特征槽(features dict)渲染成缩写徽章序列。
 * NP → "3sg" / "3pl" / "1sg" 等;VP → "simple_present" / "modal" 等。
 * 对齐 spec §4.2「特征槽缩写」与原则 #6 Feature Slots 的可视化。
 */
export function featuresToBadges(type: PhraseType, features: Record<string, unknown>): string[] {
  const f = features;
  if (type === 'NP') {
    const person = f['person'];
    const number = f['number'];
    const tags: string[] = [];
    if (number === 'singular') tags.push(`${person ?? 3}sg`);
    else if (number === 'plural') tags.push(`${person ?? 3}pl`);
    return tags;
  }
  if (type === 'VP') {
    const tags: string[] = [];
    if (f['modal']) tags.push(`modal:${f['modal']}`);
    if (f['tense']) tags.push(String(f['tense']));
    if (f['aspect'] && f['aspect'] !== 'simple' && f['aspect'] !== 'modal') tags.push(String(f['aspect']));
    return tags;
  }
  return [];
}

/** candidate kind → 中文短标签 + level,用于结构图分支 */
export function candidateLabel(c: ExpansionCandidate): string {
  return c.kind_label_cn;
}
