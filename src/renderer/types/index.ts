// 功能场景类型
export type SceneType = 'timeline' | 'anatomy' | 'expand';

// 句剖析:语义块角色
export type ChunkRole = 'subject' | 'predicate' | 'object' | 'adverbial' | 'clause' | 'punct';

// 句剖析:语义块
export interface AnatomyChunk {
  id: string;
  role: ChunkRole;
  text: string;
  label: string;
  subordinate?: string | null;
  token_indices: number[];
}

// 句剖析:分句内成分
export interface ClauseElement {
  word: string;
  label: string;
  class: ChunkRole;
}

// 句剖析:主从分句
export interface AnatomyClause {
  id: string;
  kind: 'main' | 'relative' | 'adverbial' | 'object_clause';
  text: string;
  label: string;
  antecedent?: string | null;
  elements: ClauseElement[];
}

// 句剖析:后端响应
export interface AnatomyBackend {
  sentence: string;
  chunks: AnatomyChunk[];
  clauses: AnatomyClause[];
  summary: {
    chunk_count: number;
    clause_count: number;
    has_subordinate_clause: boolean;
    warnings: string[];
  };
}

// ===================== 句扩展 (Expansion) 类型 — M3a =====================
// spec §2.7:phrase-level 数据模型,字段是 phrases(不是 nodes)。

// 短语类型
export type PhraseType = 'NP' | 'VP' | 'PP' | 'ADJP' | 'ADVP' | 'CLAUSE' | 'OTHER';

// 单个扩展模板(带预览)
export interface ExpansionTemplateInfo {
  template_id: string;
  surface: string;
  preview: string;
  semantic_class: string;
}

// 一个 kind 的一组模板候选
export interface ExpansionCandidate {
  kind: string;
  kind_label_cn: string;
  level: number;
  available: boolean;
  templates: ExpansionTemplateInfo[];
}

// 短语节点(phrase-level,含特征槽 + Parent-Child 挂载)
export interface PhraseNodeInfo {
  id: string;
  type: PhraseType;
  text: string;
  head_token_text: string;
  head_pos: string;
  syntactic_role: string;
  span: [number, number];
  features: Record<string, unknown>;
  parent_id: string | null;
  children_ids: string[];
  is_expandable: boolean;
  candidates: ExpansionCandidate[];
  // M3b 新增字段
  head_word?: string;        // 中心词(与 head_token_text 同值)
  role?: string;             // 语法角色(与 syntactic_role 同值)
  modifiers?: string[];      // 修饰语 phrase_id 列表
}

// 句扩展后端响应
export interface ExpansionBackend {
  sentence: string;
  phrases: PhraseNodeInfo[];
  warnings: string[];
}

// ===================== 句扩展 (Expansion) Apply 类型 — M3a+1 =====================
// spec §3.2:history[] 数组每个元素的快照格式

// 一次 apply 操作的元信息
export interface ApplyActionSummary {
  phrase_id: string;
  phrase_text: string;
  template_id: string;
  template_surface: string;
  kind: string;
  kind_label_cn: string;
}

// 4 级 severity
export type ValidationSeverity = 'PASS' | 'INFO' | 'WARNING' | 'ERROR';

// 验证报告(对应后端 ValidationReport)
export interface ValidationReport {
  severity: ValidationSeverity;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  infos: string[];
  auto_corrections: Array<{ from: string; to: string; reason: string }>;
}

// 一个 SentenceVersion 快照(history 数组里的一项)
export interface SentenceVersion {
  version_id: string;
  sentence: string;
  phrases: PhraseNodeInfo[];
  warnings: string[];
  validation: ValidationReport;
  action_summary: ApplyActionSummary | null;
  timestamp: number;
}

// 句子分析数据类型
export interface SentenceAnalysis {
  sentence: string;
  translation: string;
  translationExplanation: string;
  skeleton: {
    subject: string;
    verb: string;
    object_or_predicative: string;
    modifier: string;
  };
  decomposition: {
    mainClause: Clause;
    subClause?: Clause;
  };
  syntaxTree: SyntaxNode[];
  posTags: PosTag[];
  tenses: TenseAnalysis;
  expansions: ExpansionData;
  aiTeacherInsight: string;
  // 阶段 2:句剖析后端数据(切到 anatomy 场景时按需拉取)
  anatomy?: {
    backend: AnatomyBackend;
  };
  // 阶段 3:句扩展后端数据(切到 expand 场景时按需拉取,M3a 只读)
  expansion?: {
    backend: ExpansionBackend;
  };
}

export interface Clause {
  text: string;
  elements: ClauseElement[];
}

export interface SyntaxNode {
  id: string;
  label: string;
  text: string;
  sublabel?: string;
  parent?: string;
  type?: string;
  isDashed?: boolean;
}

export interface PosTag {
  word: string;
  pos: string;
  type: string;
  detail: string;
}

export interface TenseAnalysis {
  past: string;
  present: string;
  summary: string;
  detailList: TenseDetail[];
  // 后端响应字段
  backend?: {
    sentence: string;
    verbs: BackendVerb[];
    timeAdverbials: BackendTimeAdverbial[];
    timeline: {
      nodes: TimelineNode[];
      pastZone: [number, number];
      presentZone: [number, number];
      futureZone: [number, number];
    };
    summary: {
      verbCount: number;
      supportedVerbCount: number;
      primaryTense: string;
      warnings?: string[];
    };
  };
}

export type SupportedTense =
  | 'simple_present'
  | 'simple_past'
  | 'simple_future_will'
  | 'simple_future_going_to'
  | 'past_future_would'
  | 'past_future_going_to'
  | 'present_progressive'
  | 'past_progressive'
  | 'present_perfect'
  | 'past_perfect';

export type TimeZone =
  | 'past'
  | 'present'
  | 'future'
  | 'past_to_present'
  | 'past_future';

export type Aspect = 'simple' | 'progressive' | 'perfect' | 'perfect_progressive';

export type VisualShape = 'point' | 'segment' | 'arrow' | 'extended_segment';

export interface BackendVerb {
  id: string;
  surface: string;
  lemma: string;
  phrase: string;
  tense: SupportedTense;
  time_zone: TimeZone;
  aspect: Aspect;
  subject_text: string | null;
  person: 1 | 2 | 3 | null;
  number: 'singular' | 'plural' | null;
  clause_text: string | null;
  span: [number, number];
  confidence: number;
  supported: boolean;
}

export interface BackendTimeAdverbial {
  id: string;
  surface: string;
  semantic_type:
    | 'past_point'
    | 'present_point'
    | 'future_point'
    | 'duration'
    | 'since_start'
    | 'frequency'
    | 'reference_clause';
  time_zone: TimeZone;
  span: [number, number];
  confidence: number;
}

export interface TimelineNode {
  verb_id: string;
  label: string;
  x_position: number;
  visual_shape: VisualShape;
  zone: TimeZone;
}

export interface TenseDetail {
  verb: string;
  tense: string;
  role: string;
  voice: string;
  info: string;
}

export interface ExpansionData {
  word: string;
  progressiveSteps: ExpansionStep[];
  categories: Record<string, ExpansionCategory[]>;
}

export interface ExpansionStep {
  step: string;
  text: string;
  desc: string;
}

export interface ExpansionCategory {
  type: string;
  example: string;
}

// 应用状态类型
export interface AppState {
  activeScene: SceneType;
  darkMode: boolean;
  inputText: string;
  currentAnalysis: SentenceAnalysis | null;
  isLoading: boolean;
}

// Toast 通知类型
export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}
