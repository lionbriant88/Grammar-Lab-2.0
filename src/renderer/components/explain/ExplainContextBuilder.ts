import type { ExplainContext } from '../../types/explain';
import type { NodeType, SelectionEvent, SceneType } from '../../types/selection';

// UI tab name → backend contract key
// 前端 SceneType 用 'expand'(用户视角的 tab 名)
// 后端 prompt_templates / fallback_explanations 用 'expansion'
const SCENE_TO_BACKEND: Record<SceneType, 'timeline' | 'anatomy' | 'expansion'> = {
  timeline: 'timeline',
  anatomy: 'anatomy',
  expand: 'expansion',
};

export class ExplainContextBuilder {
  build(event: SelectionEvent, sentence: string): ExplainContext {
    return {
      scene: SCENE_TO_BACKEND[event.scene],
      input_sentence: sentence,
      selected_node_id: event.node.id,
      node_type: event.node.type,
      selected_node: this.projectNode(event),
      engine_result_summary: this.summarizeEngine(event),
      language: 'zh',
      student_level: 'intermediate',
    };
  }

  private projectNode(event: SelectionEvent): Record<string, any> {
    const { type, data } = event.node;
    // 从 scene-specific data 投影到 AI 友好的最小子集
    // 不传整棵 tree
    switch (type as NodeType) {
      case 'tense':
        return {
          text: data.verb || data.text || '',
          tense: data.tense || 'unknown',
          position: data.position ?? null,
        };
      case 'phrase':
        return {
          text: data.text || '',
          role: data.role || 'unknown',
          head: data.head || '',
        };
      case 'template':
        return {
          template_id: data.template_id || '',
          surface: data.surface || '',
          kind: data.kind || '',
        };
      case 'validation_warning':
        return {
          warning: data.warning || '',
          rule: data.rule || '',
          span: data.span || [],
        };
      default:
        return { raw: data };
    }
  }

  private summarizeEngine(event: SelectionEvent): Record<string, any> {
    // 5-10 个 key 的极简统计,不含整棵 tree
    // M4a 用 stub,M4c 接入真实 analysis 时填充
    const data = event.node.data || {};
    return {
      scene: event.scene as SceneType,
      node_type: event.node.type,
      has_subordinate: !!data.has_subordinate,
      verb_count: data.verb_count ?? 0,
      chunk_count: data.chunk_count ?? 0,
      template_count: data.template_count ?? 0,
    };
  }
}
