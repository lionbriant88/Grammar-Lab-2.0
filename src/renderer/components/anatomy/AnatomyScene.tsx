import type { SentenceAnalysis } from '../../types';

interface AnatomySceneProps {
  analysis: SentenceAnalysis | null;
}

export default function AnatomyScene({ analysis }: AnatomySceneProps) {
  // analysis 预留用于后续句剖析功能
  void analysis; // 标记为有意使用
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">句剖析分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析"查看语法结构</p>
      </div>
    </div>
  );
}
