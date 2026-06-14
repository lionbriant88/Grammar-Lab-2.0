import { useState, useCallback } from 'react';
import type { SentenceAnalysis } from '../types';

interface AppState {
  currentAnalysis: SentenceAnalysis | null;
  isLoading: boolean;
  error: string | null;
}

interface AppActions {
  analyzeSentence: (sentence: string) => Promise<void>;
  analyzeAnatomy: (sentence: string) => Promise<void>;
  clearAnalysis: () => void;
  clearError: () => void;
}

export function useAppState(): [AppState, AppActions] {
  const [currentAnalysis, setCurrentAnalysis] = useState<SentenceAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeSentence = useCallback(async (sentence: string) => {
    if (!sentence.trim()) {
      setError('请输入句子');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await window.electronAPI.analyzeSentence(sentence);

      if (!result.success) {
        setError((result as { success: false; error?: string }).error || '分析失败');
        setCurrentAnalysis(null);
        return;
      }

      // 构造 SentenceAnalysis 对象（保持现有结构兼容）
      // 注意:若句子变了,旧的 anatomy 数据失效(属于上一个句子),必须清空,
      // 否则切到句剖析会显示旧句子的解剖结果。
      const sentenceChanged = !currentAnalysis || currentAnalysis.sentence !== sentence;
      const analysis: SentenceAnalysis = {
        sentence,
        translation: '',  // 暂未实现翻译
        translationExplanation: '',
        skeleton: {
          subject: '',
          verb: '',
          object_or_predicative: '',
          modifier: '',
        },
        decomposition: {
          mainClause: {
            text: sentence,
            elements: [],
          },
        },
        syntaxTree: [],
        posTags: [],
        tenses: {
          past: '',
          present: '',
          summary: result.data?.summary?.primaryTense || 'unknown',
          detailList: [],
          backend: result.data,
        },
        expansions: {
          word: '',
          progressiveSteps: [],
          categories: {},
        },
        aiTeacherInsight: '',
        anatomy: sentenceChanged ? undefined : currentAnalysis?.anatomy,
      };

      setCurrentAnalysis(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
      setCurrentAnalysis(null);
    } finally {
      setIsLoading(false);
    }
  }, [currentAnalysis]);

  const analyzeAnatomy = useCallback(async (sentence: string) => {
    if (!sentence.trim()) {
      setError('请输入句子');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await window.electronAPI.analyzeAnatomy(sentence);

      if (!result.success) {
        setError((result as { success: false; error?: string }).error || '分析失败');
        return;
      }

      // 合并到现有 analysis(保留 tense 等其它场景数据),或新建一个骨架
      setCurrentAnalysis((prev) => {
        const base: SentenceAnalysis = prev && prev.sentence === sentence ? prev : {
          sentence,
          translation: '',
          translationExplanation: '',
          skeleton: { subject: '', verb: '', object_or_predicative: '', modifier: '' },
          decomposition: { mainClause: { text: sentence, elements: [] } },
          syntaxTree: [],
          posTags: [],
          tenses: { past: '', present: '', summary: 'unknown', detailList: [] },
          expansions: { word: '', progressiveSteps: [], categories: {} },
          aiTeacherInsight: '',
        };
        return { ...base, anatomy: { backend: result.data } };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setCurrentAnalysis(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return [
    { currentAnalysis, isLoading, error },
    { analyzeSentence, analyzeAnatomy, clearAnalysis, clearError },
  ];
}
