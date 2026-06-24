// SelectionEvent — Scene 组件 emit 的最小事件,ExplainPanel 内部转 ExplainContext
export type NodeType = 'tense' | 'phrase' | 'template' | 'validation_warning';

export type SceneType = 'timeline' | 'anatomy' | 'expand';

export interface SelectionEvent {
  scene: SceneType;
  node: {
    id: string;
    type: NodeType;
    // scene-specific data, ExplainContextBuilder 投影成 AI 友好的最小子集
    data: any;
  };
}
