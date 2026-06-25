import { useState, useMemo } from 'react';
import { getZoneDotColor, getZoneBackgroundColor, SHAPE_ICONS } from '../../utils/zoneColor';
import type { TimelineNode } from '../../types';

interface TimelineChartProps {
  nodes: TimelineNode[];
  darkMode: boolean;
  onNodeClick: (nodeId: string) => void;
  selectedNodeId?: string;
}

export default function TimelineChart({ nodes, darkMode, onNodeClick, selectedNodeId }: TimelineChartProps) {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // 按垂直位置分组，避免重叠
  const groupedNodes = useMemo(() => {
    const groups: TimelineNode[][] = [];
    const xPositions: number[] = [];

    for (const node of nodes) {
      // 查找是否有重叠
      let groupIndex = 0;
      let found = false;

      for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        const lastInGroup = group[group.length - 1];

        // 检查是否与最后一个节点太近（阈值 5%）
        if (Math.abs(node.x_position - lastInGroup.x_position) > 0.05) {
          groupIndex = i;
          found = true;
          break;
        }
      }

      if (!found) {
        // 创建新组
        groups.push([node]);
        xPositions.push(node.x_position);
      } else {
        // 添加到现有组
        groups[groupIndex].push(node);
        xPositions[groupIndex] = node.x_position;
      }
    }

    return groups;
  }, [nodes]);

  return (
    <div className="relative w-full h-32 flex items-center">
      {/* 过去区 */}
      <div
        className={`h-24 ${getZoneBackgroundColor('past', darkMode)} transition-colors`}
        style={{ width: '33%' }}
      />
      {/* 现在区 */}
      <div
        className={`h-24 ${getZoneBackgroundColor('present', darkMode)} transition-colors`}
        style={{ width: '34%' }}
      />
      {/* 将来区 */}
      <div
        className={`h-24 ${getZoneBackgroundColor('future', darkMode)} transition-colors`}
        style={{ width: '33%' }}
      />

      {/* NOW 标记 */}
      <div
        className="absolute top-0 bottom-0 w-px bg-slate-400 z-10"
        style={{ left: '50%' }}
      >
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 ${darkMode ? 'border-white bg-slate-400' : 'border-slate-600 bg-white'}`} />
        <span className={`absolute top-4 left-1/2 -translate-x-1/2 text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>
          NOW
        </span>
      </div>

      {/* 节点 */}
      {groupedNodes.map((group, groupIndex) =>
        group.map((node) => {
          const isHovered = hoveredNodeId === node.verb_id;
          const isSelected = selectedNodeId === node.verb_id;
          const dotColor = getZoneDotColor(node.zone);
          const verticalOffset = groupIndex * 20; // 每组向下偏移 20px

          return (
            <button
              key={node.verb_id}
              data-testid="timeline-verb"
              onClick={() => onNodeClick(node.verb_id)}
              onMouseEnter={() => setHoveredNodeId(node.verb_id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              className="absolute transform -translate-x-1/2 cursor-pointer transition-all duration-200"
              style={{
                left: `${node.x_position * 100}%`,
                top: `calc(50% + ${verticalOffset - (group.length - 1) * 10}px)`,
                transform: 'translate(-50%, -50%)',
              }}
              title={`${node.label} (${node.zone})`}
            >
              {/* 节点形状 */}
              <svg
                className={`w-5 h-5 transition-all ${isHovered || isSelected ? 'scale-125' : 'scale-100'}`}
                viewBox="0 0 16 16"
                fill="currentColor"
              >
                <path d={SHAPE_ICONS[node.visual_shape] || SHAPE_ICONS.point} />
              </svg>

              {/* 脉冲环 */}
              {(isHovered || isSelected) && (
                <div
                  className={`absolute inset-0 rounded-full animate-ping opacity-75`}
                  style={{ backgroundColor: dotColor }}
                />
              )}

              {/* 选中指示器 */}
              {isSelected && (
                <div className={`absolute -bottom-6 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded text-xs font-semibold whitespace-nowrap ${darkMode ? 'bg-slate-800 text-white' : 'bg-white text-slate-800 border border-slate-300'}`}>
                  {node.label}
                </div>
              )}
            </button>
          );
        })
      )}

      {/* 区域标签 */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between px-4">
        <span className={`text-xs font-bold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>PAST</span>
        <span className={`text-xs font-bold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>PRESENT</span>
        <span className={`text-xs font-bold uppercase ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>FUTURE</span>
      </div>
    </div>
  );
}
