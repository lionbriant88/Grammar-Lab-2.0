import { useState, useCallback } from 'react';
import type { SentenceAnalysis, SentenceVersion, ApplyActionSummary, PhraseNodeInfo, ExpansionBackend, ValidationReport } from '../types';

interface AppState {
  currentAnalysis: SentenceAnalysis | null;
  isLoading: boolean;
  error: string | null;
  expansionHistory: SentenceVersion[];       // M3a+1:history 数组
  expansionCurrentIndex: number;             // M3a+1:currentIndex 指针
}

interface AppActions {
  analyzeSentence: (sentence: string) => Promise<void>;
  analyzeAnatomy: (sentence: string) => Promise<void>;
  analyzeExpansion: (sentence: string) => Promise<void>;
  applyExpansion: (sentence: string, phraseId: string, templateId: string) => Promise<void>;  // M3a+1
  undoExpansion: () => void;                  // M3a+1
  redoExpansion: () => void;                  // M3a+1
  clearAnalysis: () => void;
  clearError: () => void;
}

export function useAppState(): [AppState, AppActions] {
  const [currentAnalysis, setCurrentAnalysis] = useState<SentenceAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expansionHistory, setExpansionHistory] = useState<SentenceVersion[]>([]);
  const [expansionCurrentIndex, setExpansionCurrentIndex] = useState(0);

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
      const sentenceChanged = !currentAnalysis || currentAnalysis.sentence !== sentence;
      const analysis: SentenceAnalysis = {
        sentence,
        translation: '',
        translationExplanation: '',
        skeleton: { subject: '', verb: '', object_or_predicative: '', modifier: '' },
        decomposition: { mainClause: { text: sentence, elements: [] } },
        syntaxTree: [],
        posTags: [],
        tenses: {
          past: '',
          present: '',
          summary: result.data?.summary?.primaryTense || 'unknown',
          detailList: [],
          backend: result.data,
        },
        expansions: { word: '', progressiveSteps: [], categories: {} },
        aiTeacherInsight: '',
        anatomy: sentenceChanged ? undefined : currentAnalysis?.anatomy,
        expansion: sentenceChanged ? undefined : currentAnalysis?.expansion,
      };
      setCurrentAnalysis(analysis);
      // M3a+1:analyzeSentence 重置 history
      if (sentenceChanged) {
        setExpansionHistory([]);
        setExpansionCurrentIndex(0);
      }
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

  const analyzeExpansion = useCallback(async (sentence: string) => {
    if (!sentence.trim()) {
      setError('请输入句子');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await window.electronAPI.analyzeExpansion(sentence);
      if (!result.success) {
        setError((result as { success: false; error?: string }).error || '分析失败');
        return;
      }
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
        return { ...base, expansion: { backend: result.data } };
      });

      // M3a+1:首次 analyzeExpansion 后,初始化 history[0] = 原句
      setExpansionHistory((prev) => {
        if (prev.length === 0) {
          const data: ExpansionBackend = result.data;
          return [{
            version_id: crypto.randomUUID(),
            sentence: data.sentence,
            phrases: data.phrases as PhraseNodeInfo[],
            warnings: data.warnings,
            validation: { severity: 'PASS', is_valid: true, errors: [], warnings: [], infos: [], auto_corrections: [] },
            action_summary: null,
            timestamp: Date.now(),
          }];
        }
        return prev;
      });
      setExpansionCurrentIndex((prev) => prev === 0 ? 0 : prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // M3a+1:applyExpansion — 调后端 → 拿完整响应 → 推入 history → 更新 currentIndex
  const applyExpansion = useCallback(async (sentence: string, phraseId: string, templateId: string) => {
    if (!sentence.trim()) {
      setError('请输入句子');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await window.electronAPI.applyExpansion(sentence, phraseId, templateId);
      if (!result.success) {
        setError((result as { success: false; error?: string }).error || 'apply 失败');
        return;
      }
      const data: ExpansionBackend = result.data;
      const validation: ValidationReport = (data as any).validation || {
        severity: 'PASS',
        is_valid: true,
        errors: [],
        warnings: [],
        infos: [],
        auto_corrections: [],
      };

      // 找模板元信息(从当前 history 的任意版本的 phrases 里查)
      const targetPhrase = (() => {
        // 先看 currentAnalysis.expansion.backend
        const backendPhrases = currentAnalysis?.expansion?.backend?.phrases;
        if (backendPhrases) {
          const found = backendPhrases.find((p) => p.id === phraseId);
          if (found) return found;
        }
        // 再看 history[currentIndex]
        const hist = expansionHistory[expansionCurrentIndex];
        if (hist) {
          const found = hist.phrases.find((p) => p.id === phraseId);
          if (found) return found;
        }
        return null;
      })();
      const phraseText = targetPhrase?.text ?? '';
      const kindLabel = (() => {
        const cand = targetPhrase?.candidates.find((c) => c.kind === templateId.replace(/^tpl_/, '').replace(/_.*$/, ''));
        return cand?.kind_label_cn ?? templateId;
      })();

      const actionSummary: ApplyActionSummary = {
        phrase_id: phraseId,
        phrase_text: phraseText,
        template_id: templateId,
        template_surface: templateId.replace(/^tpl_[^_]+_/, ''),
        kind: templateId.replace(/^tpl_/, '').replace(/_.*$/, ''),
        kind_label_cn: kindLabel,
      };

      const newVersion: SentenceVersion = {
        version_id: crypto.randomUUID(),
        sentence: data.sentence,
        phrases: data.phrases as PhraseNodeInfo[],
        warnings: data.warnings,
        validation,
        action_summary: actionSummary,
        timestamp: Date.now(),
      };

      // 更新 currentAnalysis(画布重画)
      setCurrentAnalysis((prev) => prev ? { ...prev, expansion: { backend: data } } : prev);

      // 推入 history:截断 future + 追加
      setExpansionHistory((prev) => {
        const newHist = [...prev.slice(0, expansionCurrentIndex + 1), newVersion];
        return newHist;
      });
      setExpansionCurrentIndex((prev) => prev + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'apply 失败');
    } finally {
      setIsLoading(false);
    }
  }, [currentAnalysis, expansionHistory, expansionCurrentIndex]);

  // M3a+1:Undo — 改 currentIndex + 替换 currentAnalysis.expansion.backend(不调后端)
  const undoExpansion = useCallback(() => {
    setExpansionCurrentIndex((idx) => {
      if (idx <= 0) return idx;
      const newIdx = idx - 1;
      const target = expansionHistory[newIdx];
      if (target) {
        setCurrentAnalysis((prev) => prev ? { ...prev, expansion: { backend: { sentence: target.sentence, phrases: target.phrases, warnings: target.warnings } } } : prev);
      }
      return newIdx;
    });
  }, [expansionHistory]);

  // M3a+1:Redo
  const redoExpansion = useCallback(() => {
    setExpansionCurrentIndex((idx) => {
      if (idx >= expansionHistory.length - 1) return idx;
      const newIdx = idx + 1;
      const target = expansionHistory[newIdx];
      if (target) {
        setCurrentAnalysis((prev) => prev ? { ...prev, expansion: { backend: { sentence: target.sentence, phrases: target.phrases, warnings: target.warnings } } } : prev);
      }
      return newIdx;
    });
  }, [expansionHistory]);

  const clearAnalysis = useCallback(() => {
    setCurrentAnalysis(null);
    setError(null);
    setExpansionHistory([]);
    setExpansionCurrentIndex(0);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return [
    { currentAnalysis, isLoading, error, expansionHistory, expansionCurrentIndex },
    { analyzeSentence, analyzeAnatomy, analyzeExpansion, applyExpansion, undoExpansion, redoExpansion, clearAnalysis, clearError },
  ];
}
