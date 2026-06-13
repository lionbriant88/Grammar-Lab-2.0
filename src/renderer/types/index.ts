// 功能场景类型
export type SceneType = 'timeline' | 'anatomy' | 'expand';

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
}

export interface Clause {
  text: string;
  elements: ClauseElement[];
}

export interface ClauseElement {
  word: string;
  label: string;
  class: string;
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
