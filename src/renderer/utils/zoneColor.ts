import { TimeZone, VisualShape } from '../types';

/**
 * 时区颜色映射 (Tailwind CSS 类)
 * light/dark 模式分别配置
 */
export const ZONE_COLORS = {
  past: {
    light: 'bg-orange-200 border-orange-400 text-orange-800',
    dark: 'bg-orange-900/50 border-orange-600 text-orange-200',
    dot: 'bg-orange-500',
  },
  present: {
    light: 'bg-blue-200 border-blue-400 text-blue-800',
    dark: 'bg-blue-900/50 border-blue-600 text-blue-200',
    dot: 'bg-blue-500',
  },
  future: {
    light: 'bg-purple-200 border-purple-400 text-purple-800',
    dark: 'bg-purple-900/50 border-purple-600 text-purple-200',
    dot: 'bg-purple-500',
  },
  past_to_present: {
    light: 'bg-green-200 border-green-400 text-green-800',
    dark: 'bg-green-900/50 border-green-600 text-green-200',
    dot: 'bg-green-500',
  },
  past_future: {
    light: 'bg-slate-300 border-slate-500 text-slate-800',
    dark: 'bg-slate-700/50 border-slate-500 text-slate-200',
    dot: 'bg-slate-500',
  },
};

/**
 * 时间轴背景色
 */
export const TIMELINE_BACKGROUND = {
  light: {
    past: 'bg-orange-100',
    present: 'bg-blue-100',
    future: 'bg-purple-100',
  },
  dark: {
    past: 'bg-orange-950/30',
    present: 'bg-blue-950/30',
    future: 'bg-purple-950/30',
  },
};

/**
 * 节点形状对应的 SVG 图标路径
 */
export const SHAPE_ICONS: Record<VisualShape, string> = {
  point: 'M6 6a2 2 0 100 4 2 2 0 000-4z',  // 圆点
  segment: 'M4 8h8',  // 短线段
  arrow: 'M4 8h8l-4-4',  // 箭头
  extended_segment: 'M2 8h10l2 2',  // 长条带箭头
};

/**
 * 获取时区颜色类（暗黑模式）
 */
export function getZoneColorClass(zone: TimeZone, darkMode: boolean): string {
  const theme = darkMode ? 'dark' : 'light';
  return ZONE_COLORS[zone]?.[theme] || ZONE_COLORS.present.light;
}

/**
 * 获取时区背景色
 */
export function getZoneBackgroundColor(zone: TimeZone, darkMode: boolean): string {
  const theme = darkMode ? 'dark' : 'light';
  return TIMELINE_BACKGROUND[theme][zone === 'past_to_present' ? 'present' : zone as 'past' | 'present' | 'future'] || TIMELINE_BACKGROUND.light.present;
}

/**
 * 获取时区圆点颜色
 */
export function getZoneDotColor(zone: TimeZone): string {
  return ZONE_COLORS[zone]?.dot || ZONE_COLORS.present.dot;
}
