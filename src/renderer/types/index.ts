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
