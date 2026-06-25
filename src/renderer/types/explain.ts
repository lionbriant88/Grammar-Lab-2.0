// ExplainResult — 后端响应结构
export type ExplainSource = 'ai' | 'cache' | 'fallback';

import type { NodeType } from './selection';

export interface ExplainResult {
  title: string;
  summary: string;
  why: string;
  example: string;
  commonMistakes: string[];
  tips: string[];
  source: ExplainSource;
  provider: string;
  model: string;
  promptVersion: string;
  cached: boolean;
  generatedAt: string;
  degraded: boolean;
}

export interface ExplainContext {
  scene: 'timeline' | 'anatomy' | 'expansion';
  input_sentence: string;
  selected_node_id: string;
  node_type: NodeType;
  selected_node: Record<string, any>;
  engine_result_summary: Record<string, any>;
  language: 'zh' | 'en';
  student_level: 'beginner' | 'intermediate' | 'advanced';
}

export interface ExplainAPIResponse {
  ok: boolean;
  degraded: boolean;
  result: {
    title: string;
    summary: string;
    why: string;
    example: string;
    common_mistakes: string[];
    tips: string[];
    source: ExplainSource;
    provider: string;
    model: string;
    prompt_version: string;
    cached: boolean;
    generated_at: string;
  };
}

export interface HealthState {
  status: 'unknown' | 'ready' | 'degraded' | 'offline';
  provider?: string;
  model?: string;
  latencyMs?: number;
  reason?: string;
}
