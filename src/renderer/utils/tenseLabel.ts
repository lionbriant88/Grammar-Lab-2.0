import { SupportedTense, Aspect, TimeZone } from '../types';

/**
 * 时态中文名映射
 */
export const TENSE_LABEL_CN: Record<SupportedTense, string> = {
  simple_present: '一般现在时',
  simple_past: '一般过去时',
  simple_future_will: '一般将来时 (will)',
  simple_future_going_to: '一般将来时 (be going to)',
  past_future_would: '过去将来时 (would)',
  past_future_going_to: '过去将来时 (was/were going to)',
  present_progressive: '现在进行时',
  past_progressive: '过去进行时',
  present_perfect: '现在完成时',
  past_perfect: '过去完成时',
};

/**
 * 时态英文全称映射
 */
export const TENSE_LABEL_EN: Record<SupportedTense, string> = {
  simple_present: 'Simple Present',
  simple_past: 'Simple Past',
  simple_future_will: 'Simple Future (will)',
  simple_future_going_to: 'Simple Future (be going to)',
  past_future_would: 'Past Future (would)',
  past_future_going_to: 'Past Future (be going to)',
  present_progressive: 'Present Progressive',
  past_progressive: 'Past Progressive',
  present_perfect: 'Present Perfect',
  past_perfect: 'Past Perfect',
};

/**
 * 时区中文名映射
 */
export const ZONE_LABEL_CN: Record<TimeZone, string> = {
  past: '过去',
  present: '现在',
  future: '将来',
  past_to_present: '过去至现在',
  past_future: '过去将来',
};

/**
 * 体中文名映射
 */
export const ASPECT_LABEL_CN: Record<Aspect, string> = {
  simple: '一般体',
  progressive: '进行体',
  perfect: '完成体',
  perfect_progressive: '完成进行体',
};

/**
 * 获取时态中文名
 */
export function getTenseLabelCn(tense: SupportedTense): string {
  return TENSE_LABEL_CN[tense] || tense;
}

/**
 * 获取时态英文全称
 */
export function getTenseLabelEn(tense: SupportedTense): string {
  return TENSE_LABEL_EN[tense] || tense;
}

/**
 * 获取时区中文名
 */
export function getZoneLabelCn(zone: TimeZone): string {
  return ZONE_LABEL_CN[zone] || zone;
}

/**
 * 获取体中文名
 */
export function getAspectLabelCn(aspect: Aspect): string {
  return ASPECT_LABEL_CN[aspect] || aspect;
}
