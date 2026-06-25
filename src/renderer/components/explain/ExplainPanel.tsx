import { useEffect, useRef, useState, useCallback } from 'react';
import { ExplainContextBuilder } from './ExplainContextBuilder';
import { SourceBadge } from './SourceBadge';
import { DegradedBanner } from './DegradedBanner';
import { ExplainSkeleton } from './ExplainSkeleton';
import { MarkdownView } from './MarkdownView';
import { useExplainStore } from '../../stores/explainStore';
import type { SelectionEvent } from '../../types/selection';
import type { ExplainResult, ExplainAPIResponse } from '../../types/explain';

type ExplainState =
  | { kind: 'empty' }
  | { kind: 'loading' }
  | { kind: 'ready'; result: ExplainResult; degraded: boolean }
  | { kind: 'error'; message: string };

const BUILTIN_FALLBACK: ExplainResult = {
  title: '解释',
  summary: 'AI 暂不可用。',
  why: '请稍后重试,或检查 AI provider 配置。',
  example: '',
  commonMistakes: [],
  tips: [],
  source: 'fallback',
  provider: 'builtin',
  model: 'builtin',
  promptVersion: 'M4a_v1',
  cached: false,
  generatedAt: new Date().toISOString(),
  degraded: true,
};

interface Props {
  selection: SelectionEvent | null;
  sentence: string;
  darkMode: boolean;
}

export function ExplainPanel({ selection, sentence, darkMode }: Props) {
  const [state, setState] = useState<ExplainState>({ kind: 'empty' });
  const [pinned, setPinned] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const pushHistory = useExplainStore((s) => s.pushHistory);
  const builder = useRef(new ExplainContextBuilder()).current;

  const fetchExplain = useCallback(
    async (sel: SelectionEvent, signal: AbortSignal) => {
      const ctx = builder.build(sel, sentence);
      try {
        // @ts-ignore — electronAPI 由 preload 注入
        const r = await window.electronAPI.explainNode(ctx);
        if (signal.aborted) return;
        if (r?.success && r.data) {
          const apiResp: ExplainAPIResponse = r.data;
          const res = apiResp.result;
          const result: ExplainResult = {
            title: res.title,
            summary: res.summary,
            why: res.why,
            example: res.example,
            commonMistakes: res.common_mistakes,
            tips: res.tips,
            source: res.source,
            provider: res.provider,
            model: res.model,
            promptVersion: res.prompt_version,
            cached: res.cached,
            generatedAt: res.generated_at,
            degraded: apiResp.degraded,
          };
          setState({ kind: 'ready', result, degraded: apiResp.degraded });
          pushHistory({ context: ctx, result, viewedAt: new Date().toISOString() });
        } else {
          setState({ kind: 'ready', result: BUILTIN_FALLBACK, degraded: true });
        }
      } catch (e) {
        if (signal.aborted) return;
        setState({ kind: 'error', message: String(e) });
      }
    },
    [sentence, builder, pushHistory],
  );

  useEffect(() => {
    if (pinned || !selection) return;

    // 双保险:AbortController + request_id
    controllerRef.current?.abort();
    const controller = new AbortController();
    const myId = ++requestIdRef.current;
    controllerRef.current = controller;

    setState({ kind: 'loading' });
    fetchExplain(selection, controller.signal).then(() => {
      if (myId !== requestIdRef.current) return;
    });

    return () => controller.abort();
  }, [selection, pinned, fetchExplain]);

  if (state.kind === 'empty') {
    return (
      <div className={`p-4 text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        点击节点,查看 AI 解释(为什么?)。
      </div>
    );
  }

  if (state.kind === 'loading') {
    return <ExplainSkeleton />;
  }

  if (state.kind === 'error') {
    return (
      <div className="p-4 text-sm text-red-600">
        出错了:{state.message}
      </div>
    );
  }

  const { result, degraded } = state;

  return (
    <div className={`p-4 space-y-3 ${darkMode ? 'bg-slate-800 text-slate-100' : 'bg-white'}`}>
      {degraded && <DegradedBanner />}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold flex-1">{result.title}</h2>
        <SourceBadge source={result.source} />
      </div>

      <div className="flex items-center gap-2">
        <button
          data-testid="pin-button"
          onClick={() => setPinned((p) => !p)}
          className={pinned ? 'pin-active' : 'pin-inactive'}
          title={pinned ? '取消 Pin' : 'Pin 当前解释'}
        >
          {pinned ? '📌' : '📍'}
        </button>
        <span className="text-xs text-slate-500">
          {result.provider} / {result.model}
        </span>
      </div>

      {result.summary && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Summary</h3>
          <MarkdownView content={result.summary} />
        </div>
      )}

      {result.why && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Why</h3>
          <MarkdownView content={result.why} />
        </div>
      )}

      {result.example && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Example</h3>
          <MarkdownView content={result.example} />
        </div>
      )}

      {result.commonMistakes.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Common Mistakes</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {result.commonMistakes.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {result.tips.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Tips</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            {result.tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
