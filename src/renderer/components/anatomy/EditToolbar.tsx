import type { ChunkRole } from '../../types';
import { getRoleSolidColor, getRoleLabel, LEGEND_ROLES } from '../../utils/roleColor';

export interface EditToolbarProps {
  darkMode: boolean;
  /** 当前选中块的角色(无选中则禁用改角色) */
  selectedRole: ChunkRole | null;
  onSetRole: (role: ChunkRole) => void;
  canUndo: boolean;
  onUndo: () => void;
  onReset: () => void;
  onFinish: () => void;
}

export default function EditToolbar({
  darkMode,
  selectedRole,
  onSetRole,
  canUndo,
  onUndo,
  onReset,
  onFinish,
}: EditToolbarProps) {
  const btnBase =
    'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed';
  const btnOutline = darkMode
    ? 'border border-slate-600 text-slate-200 hover:bg-slate-700'
    : 'border border-slate-300 text-slate-700 hover:bg-slate-100';
  const btnPrimary = 'bg-blue-500 text-white hover:bg-blue-600';

  return (
    <div
      className={`flex flex-wrap items-center gap-3 p-3 rounded-2xl border ${
        darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
      }`}
    >
      <span className={`text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
        编辑模式
      </span>

      {/* 角色选择 */}
      <div className="flex items-center gap-1.5">
        <span className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
          {selectedRole ? '将选中块改为:' : '先选中一个块:'}
        </span>
        {LEGEND_ROLES.map((role) => (
          <button
            key={role}
            disabled={!selectedRole}
            onClick={() => onSetRole(role)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium disabled:opacity-40 hover:bg-black/5 dark:hover:bg-white/10"
            title={`设为${getRoleLabel(role)}`}
          >
            <span className={`inline-block w-2.5 h-2.5 rounded ${getRoleSolidColor(role)}`} />
            <span className={darkMode ? 'text-slate-200' : 'text-slate-700'}>{getRoleLabel(role)}</span>
          </button>
        ))}
      </div>

      <div className="flex-1" />

      {/* 操作按钮 */}
      <button onClick={onUndo} disabled={!canUndo} className={`${btnBase} ${btnOutline}`}>
        ↶ 撤销
      </button>
      <button onClick={onReset} className={`${btnBase} ${btnOutline}`}>
        重置为自动
      </button>
      <button onClick={onFinish} className={`${btnBase} ${btnPrimary}`}>
        ✓ 完成
      </button>
    </div>
  );
}
