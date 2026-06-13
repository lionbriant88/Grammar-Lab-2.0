import { useState, useCallback } from 'react';
import type { SentenceAnalysis } from '../types';

interface AppState {
  currentAnalysis: SentenceAnalysis | null;
  isLoading: boolean;
  error: string | null;
}

interface AppActions {
  analyzeSentence: (sentence: string) => Promise<void>;
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
      };

      setCurrentAnalysis(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
      setCurrentAnalysis(null);
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
    { analyzeSentence, clearAnalysis, clearError },
  ];
}
