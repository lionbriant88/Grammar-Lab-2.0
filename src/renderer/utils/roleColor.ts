import type { ChunkRole } from '../types';

/**
 * 句法角色 → Tailwind 配色 (对齐时间轴场景的柔和风格)
 * 浅色 / 深色 双主题。
 */
export const ROLE_COLORS: Record<ChunkRole, { light: string; dark: string; solid: string }> = {
  subject: {
    light: 'bg-blue-100 text-blue-800 border-blue-200',
    dark: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    solid: 'bg-blue-400',
  },
  predicate: {
    light: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    dark: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    solid: 'bg-emerald-400',
  },
  object: {
    light: 'bg-violet-100 text-violet-800 border-violet-200',
    dark: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    solid: 'bg-violet-400',
  },
  adverbial: {
    light: 'bg-amber-100 text-amber-800 border-amber-200',
    dark: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    solid: 'bg-amber-400',
  },
  clause: {
    light: 'bg-pink-100 text-pink-800 border-pink-200',
    dark: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    solid: 'bg-pink-400',
  },
  punct: {
    light: 'bg-slate-100 text-slate-500 border-slate-200',
    dark: 'bg-slate-700/40 text-slate-400 border-slate-700',
    solid: 'bg-slate-400',
  },
};

/** 角色 → 中文标签 */
export const ROLE_LABELS: Record<ChunkRole, string> = {
  subject: '主语',
  predicate: '谓语',
  object: '宾语',
  adverbial: '状语',
  clause: '从句',
  punct: '标点',
};

/** 角色 → 角色说明(点击块时展开) */
export const ROLE_DESCRIPTIONS: Record<ChunkRole, string> = {
  subject: '动作的执行者或被描述的对象',
  predicate: '句子的核心动作(含助动词、否定、副词)',
  object: '动作的承受者或介词短语',
  adverbial: '修饰动作的时间、地点、方式等',
  clause: '作为成分的从句(定语 / 状语 / 宾语)',
  punct: '标点符号',
};

/** 取角色的色块 class(浅/深主题) */
export function getRoleColorClass(role: ChunkRole, darkMode: boolean): string {
  const theme = darkMode ? 'dark' : 'light';
  return ROLE_COLORS[role]?.[theme] || ROLE_COLORS.punct[theme];
}

/** 取角色的实心色(用于图例小方块、分句色条) */
export function getRoleSolidColor(role: ChunkRole): string {
  return ROLE_COLORS[role]?.solid || ROLE_COLORS.punct.solid;
}

/** 取角色中文标签 */
export function getRoleLabel(role: ChunkRole): string {
  return ROLE_LABELS[role] || role;
}

/** 取角色说明 */
export function getRoleDescription(role: ChunkRole): string {
  return ROLE_DESCRIPTIONS[role] || '';
}

/** 图例展示用的角色顺序(标点不展示) */
export const LEGEND_ROLES: ChunkRole[] = ['subject', 'predicate', 'object', 'adverbial', 'clause'];
