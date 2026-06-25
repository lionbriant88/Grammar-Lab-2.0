import { describe, it, expect } from 'vitest';
import { ExplainContextBuilder } from '../ExplainContextBuilder';

describe('ExplainContextBuilder', () => {
  const builder = new ExplainContextBuilder();

  it('builds context for timeline tense', () => {
    const ctx = builder.build(
      {
        scene: 'timeline',
        node: {
          id: 'v1',
          type: 'tense',
          data: { verb: 'have lived', tense: 'present_perfect', position: 0 },
        },
      },
      'I have lived here.',
    );
    expect(ctx.scene).toBe('timeline');
    expect(ctx.node_type).toBe('tense');
    expect(ctx.selected_node_id).toBe('v1');
    expect(ctx.selected_node.text).toBe('have lived');
    expect(ctx.input_sentence).toBe('I have lived here.');
    expect(ctx.language).toBe('zh');
  });

  it('builds context for anatomy phrase', () => {
    const ctx = builder.build(
      {
        scene: 'anatomy',
        node: {
          id: 'c1',
          type: 'phrase',
          data: { text: 'When I arrived', role: 'ADVCL', head: 'arrived' },
        },
      },
      'When I arrived, he left.',
    );
    expect(ctx.scene).toBe('anatomy');
    expect(ctx.node_type).toBe('phrase');
    expect(ctx.selected_node.text).toBe('When I arrived');
    expect(ctx.selected_node.role).toBe('ADVCL');
  });

  it('builds context for expansion template', () => {
    const ctx = builder.build(
      {
        scene: 'expand',
        node: {
          id: 't1',
          type: 'template',
          data: { template_id: 'adj-1', surface: 'cute', kind: 'adjective' },
        },
      },
      'I have a dog.',
    );
    // M4d fix: UI scene 'expand' maps to backend contract 'expansion'
    expect(ctx.scene).toBe('expansion');
    expect(ctx.node_type).toBe('template');
  });

  it("translates 'expand' SelectionEvent to 'expansion' ExplainContext", () => {
    const ctx = builder.build(
      {
        scene: 'expand',
        node: {
          id: 't1',
          type: 'template',
          data: { template_id: 'adj-1', surface: 'cute', kind: 'adjective' },
        },
      },
      'I have a dog.',
    );
    expect(ctx.scene).toBe('expansion');
  });

  it('builds context for validation warning', () => {
    const ctx = builder.build(
      {
        scene: 'expand',
        node: {
          id: 'w1',
          type: 'validation_warning',
          data: { warning: 'subject-verb disagreement', rule: 'sv_agree', span: [0, 5] },
        },
      },
      'He go home.',
    );
    expect(ctx.node_type).toBe('validation_warning');
  });

  it('engine_result_summary has limited keys', () => {
    const ctx = builder.build(
      {
        scene: 'timeline',
        node: { id: 'n', type: 'tense', data: {} },
      },
      'Hello.',
    );
    const keys = Object.keys(ctx.engine_result_summary);
    expect(keys.length).toBeLessThanOrEqual(10);
  });
});
