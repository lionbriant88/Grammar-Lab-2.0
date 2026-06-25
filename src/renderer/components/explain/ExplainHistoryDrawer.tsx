import { useExplainStore, type ExplainHistoryItem } from '../../stores/explainStore';
import { SourceBadge } from './SourceBadge';

interface Props {
  open: boolean;
  onClose: () => void;
  onSelect: (item: ExplainHistoryItem) => void;
  darkMode: boolean;
}

function groupByDate(items: ExplainHistoryItem[]) {
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();
  const groups: Record<string, ExplainHistoryItem[]> = { Today: [], Yesterday: [], Earlier: [] };
  for (const item of items) {
    const d = new Date(item.viewedAt).toDateString();
    if (d === today) groups.Today.push(item);
    else if (d === yesterday) groups.Yesterday.push(item);
    else groups.Earlier.push(item);
  }
  return Object.entries(groups).filter(([, v]) => v.length > 0);
}

export function ExplainHistoryDrawer({ open, onClose, onSelect, darkMode }: Props) {
  const history = useExplainStore((s) => s.history);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      <div
        data-testid="history-drawer"
        className={`fixed right-0 top-0 h-full w-80 shadow-xl z-50 overflow-y-auto ${
          darkMode ? 'bg-slate-800 text-slate-100' : 'bg-white'
        }`}
      >
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-bold">🕘 History</h3>
          <button onClick={onClose} className="text-sm">✕</button>
        </div>
        <div className="p-2">
          {history.length === 0 && (
            <p className="text-sm text-slate-500 p-4">暂无历史</p>
          )}
          {groupByDate(history).map(([date, items]) => (
            <div key={date} className="mb-4">
              <h4 className="text-xs font-semibold text-slate-500 px-2 py-1">{date}</h4>
              {items.map((item, i) => (
                <button
                  key={i}
                  onClick={() => onSelect(item)}
                  className="w-full text-left p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded flex items-start gap-2"
                >
                  <SourceBadge source={item.result.source} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{item.result.title}</p>
                    <p className="text-xs text-slate-500">
                      {item.context.scene} · {item.context.selected_node_id}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
