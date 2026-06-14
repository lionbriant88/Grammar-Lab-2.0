import type { ChunkRole } from '../../types';
import {
  getRoleColorClass,
  getRoleLabel,
  getRoleDescription,
  getRoleSolidColor,
  LEGEND_ROLES,
} from '../../utils/roleColor';

/**
 * 可编辑的语义块(供编辑态搬词使用)。
 * 展示态直接由 AnatomyChunk 派生为同结构。
 */
export interface EditableChunk {
  id: string;
  role: ChunkRole;
  words: string[]; // 该块的词(编辑时可增删)
  label: string;
  subordinate?: string | null;
}

export interface ChunkBlocksProps {
  chunks: EditableChunk[];
  darkMode: boolean;
  isEditing: boolean;
  selectedId: string | null;
  onSelectChunk: (id: string | null) => void;
  /** 把某词从 sourceChunkId 移到 targetChunkId(插在 wordIndex 处) */
  onMoveWord: (sourceChunkId: string, wordIndex: number, targetChunkId: string, insertIndex: number) => void;
}

export default function ChunkBlocks({
  chunks,
  darkMode,
  isEditing,
  selectedId,
  onSelectChunk,
  onMoveWord,
}: ChunkBlocksProps) {
  const handleDragStart = (e: React.DragEvent, chunkId: string, wordIndex: number) => {
    e.dataTransfer.effectAllowed = 'move';
    // Firefox 需要 setData 才能触发 drag
    e.dataTransfer.setData('text/plain', `${chunkId}:${wordIndex}`);
  };

  const handleDropOnChunk = (e: React.DragEvent, targetChunkId: string) => {
    e.preventDefault();
    const raw = parseDataTransfer(e);
    if (!raw) return;
    if (raw.chunkId === targetChunkId) return; // 同块拖动忽略
    // 按鼠标 X 坐标计算插入位置:遍历目标块内的词元素,
    // 找到第一个「中点在鼠标右侧」的词,插入到它前面;否则插到末尾。
    const insertIndex = computeInsertIndex(e.currentTarget as HTMLElement, e.clientX);
    onMoveWord(raw.chunkId, raw.wordIndex, targetChunkId, insertIndex);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  return (
    <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'}`}>
      {/* 色带 */}
      <div className="flex flex-wrap items-stretch gap-2">
        {chunks.map((chunk) => {
          const colorClass = getRoleColorClass(chunk.role, darkMode);
          const isSelected = selectedId === chunk.id;
          const isPunct = chunk.role === 'punct';

          return (
            <div
              key={chunk.id}
              role={isEditing ? 'button' : undefined}
              draggable={false}
              onClick={() => {
                if (!isEditing && !isPunct) {
                  onSelectChunk(isSelected ? null : chunk.id);
                }
              }}
              onDragOver={isEditing ? handleDragOver : undefined}
              onDrop={isEditing ? (e) => handleDropOnChunk(e, chunk.id) : undefined}
              className={[
                'group relative rounded-xl border px-3 py-2 transition-all select-none',
                isPunct ? 'cursor-default' : 'cursor-pointer',
                colorClass,
                isEditing ? 'border-dashed' : '',
                isSelected ? 'ring-2 ring-offset-1 ring-blue-400 dark:ring-offset-slate-900 shadow-md -translate-y-0.5' : '',
                !isEditing && !isPunct ? 'hover:-translate-y-0.5 hover:shadow-md' : '',
              ].join(' ')}
              title={isPunct ? undefined : `${getRoleLabel(chunk.role)}:${getRoleDescription(chunk.role)}`}
            >
              {/* 词序列 */}
              <div className="flex flex-wrap items-center gap-x-1 gap-y-0.5">
                {chunk.words.map((word, wi) => (
                  <span
                    key={wi}
                    data-word-idx={wi}
                    draggable={isEditing && !isPunct}
                    onDragStart={isEditing && !isPunct ? (e) => handleDragStart(e, chunk.id, wi) : undefined}
                    className={[
                      'text-sm font-medium',
                      isEditing && !isPunct ? 'cursor-grab active:cursor-grabbing px-0.5 rounded hover:bg-black/10 dark:hover:bg-white/10' : '',
                    ].join(' ')}
                  >
                    {word}
                  </span>
                ))}
              </div>
              {/* 角色标签 */}
              {!isPunct && (
                <div className="mt-1 text-[10px] font-bold uppercase tracking-wider opacity-70">
                  {chunk.label}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 选中块的说明(展示态) */}
      {!isEditing && selectedId && (() => {
        const sel = chunks.find((c) => c.id === selectedId);
        if (!sel) return null;
        return (
          <div className={`mt-4 p-3 rounded-lg text-sm ${darkMode ? 'bg-slate-800/60 text-slate-300' : 'bg-slate-50 text-slate-600'}`}>
            <span className="font-bold">{sel.label}</span>
            <span className="mx-2 opacity-50">·</span>
            <span>{getRoleDescription(sel.role)}</span>
          </div>
        );
      })()}

      {/* 图例 */}
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5">
        {LEGEND_ROLES.map((role) => (
          <div key={role} className="flex items-center gap-1.5">
            <span className={`inline-block w-3 h-3 rounded ${getRoleSolidColor(role)}`} />
            <span className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              {getRoleLabel(role)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function parseDataTransfer(e: React.DragEvent): { chunkId: string; wordIndex: number } | null {
  try {
    const raw = e.dataTransfer.getData('text/plain');
    const [chunkId, idx] = raw.split(':');
    return { chunkId, wordIndex: Number(idx) };
  } catch {
    return null;
  }
}

/**
 * 按鼠标 X 坐标计算词应插入的位置。
 * 遍历目标块容器内所有带 data-word-idx 的词元素,找到第一个「中点 X 在��标右侧」
 * 的词,插入到它前面;若鼠标在所有词右侧,插到末尾。
 * 这样拖拽会落到鼠标实际位置,而非永远末尾。
 */
function computeInsertIndex(container: HTMLElement, clientX: number): number {
  const wordEls = container.querySelectorAll<HTMLElement>('[data-word-idx]');
  for (const el of Array.from(wordEls)) {
    const rect = el.getBoundingClientRect();
    const midX = rect.left + rect.width / 2;
    if (clientX < midX) {
      const idx = Number(el.getAttribute('data-word-idx'));
      return Number.isFinite(idx) ? idx : 0;
    }
  }
  // 鼠标在所有词的右侧 → 末尾
  return wordEls.length;
}
