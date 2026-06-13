import type { SentenceAnalysis } from '../../types';

interface ExpandSceneProps {
  analysis: SentenceAnalysis | null;
}

export default function ExpandScene({ analysis }: ExpandSceneProps) {
  // analysis 预留用于后续句扩展功能
  void analysis; // 标记为有意使用
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg">句扩展分析 - 等待分析</p>
        <p className="text-sm mt-2">输入句子后点击"开始分析"查看扩展示例</p>
      </div>
    </div>
  );
}
