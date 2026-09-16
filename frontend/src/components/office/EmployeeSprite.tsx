import React from 'react';
import { WorkstationProjection, EmployeeVisualState } from '../../types/office';
import {
  User,
  Monitor,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Users,
  RefreshCw,
  Lock,
} from 'lucide-react';

interface EmployeeSpriteProps {
  workstation: WorkstationProjection;
  onSelect: (ws: WorkstationProjection) => void;
  isSelected: boolean;
}

export const EmployeeSprite: React.FC<EmployeeSpriteProps> = ({
  workstation,
  onSelect,
  isSelected,
}) => {
  const getStateConfig = (state: EmployeeVisualState) => {
    switch (state) {
      case 'WORKING':
        return {
          bg: 'bg-blue-500/20 border-blue-500/60 text-blue-300',
          dot: 'bg-blue-400 animate-pulse',
          icon: Monitor,
          label: 'Working',
        };
      case 'THINKING':
        return {
          bg: 'bg-purple-500/20 border-purple-500/60 text-purple-300',
          dot: 'bg-purple-400 animate-pulse',
          icon: Sparkles,
          label: 'Thinking',
        };
      case 'IN_MEETING':
        return {
          bg: 'bg-pink-500/20 border-pink-500/60 text-pink-300',
          dot: 'bg-pink-400 animate-pulse',
          icon: Users,
          label: 'In Meeting',
        };
      case 'BLOCKED':
        return {
          bg: 'bg-rose-500/20 border-rose-500/60 text-rose-300',
          dot: 'bg-rose-400 animate-ping',
          icon: AlertTriangle,
          label: 'Blocked',
        };
      case 'AWAITING_APPROVAL':
        return {
          bg: 'bg-amber-500/20 border-amber-500/60 text-amber-300',
          dot: 'bg-amber-400 animate-bounce',
          icon: Lock,
          label: 'Awaiting Approval',
        };
      case 'RECOVERING':
        return {
          bg: 'bg-orange-500/20 border-orange-500/60 text-orange-300',
          dot: 'bg-orange-400 animate-spin',
          icon: RefreshCw,
          label: 'Recovering',
        };
      case 'COMPLETED':
        return {
          bg: 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300',
          dot: 'bg-emerald-400',
          icon: CheckCircle2,
          label: 'Completed',
        };
      case 'WAITING':
        return {
          bg: 'bg-yellow-500/20 border-yellow-500/60 text-yellow-300',
          dot: 'bg-yellow-400',
          icon: Clock,
          label: 'Waiting',
        };
      default:
        return {
          bg: 'bg-gray-500/20 border-gray-500/40 text-gray-400',
          dot: 'bg-gray-400',
          icon: User,
          label: 'Idle',
        };
    }
  };

  const config = getStateConfig(workstation.visual_state);
  const Icon = config.icon;

  return (
    <div
      onClick={() => onSelect(workstation)}
      className={`group relative p-3 rounded-xl border transition-all cursor-pointer select-none ${config.bg} ${
        isSelected ? 'ring-2 ring-indigo-400 scale-105 shadow-xl z-20' : 'hover:scale-102 hover:shadow-lg'
      }`}
    >
      {/* Top Bar: Role & Status */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 text-[11px] font-bold tracking-wide truncate">
          <span className={`w-2 h-2 rounded-full ${config.dot}`} />
          <span className="truncate">{workstation.employee_name}</span>
        </div>
        {workstation.is_manager && (
          <span className="bg-purple-500/30 text-purple-300 text-[9px] font-bold px-1.5 py-0.5 rounded border border-purple-500/40">
            MGR
          </span>
        )}
      </div>

      {/* Title */}
      <div className="text-[10px] text-gray-400 truncate mb-2">{workstation.employee_title}</div>

      {/* Active Workstation Activity */}
      <div className="bg-black/30 rounded-lg p-2 border border-white/5 space-y-1">
        <div className="flex items-center justify-between text-[10px] text-gray-300 font-medium">
          <span className="flex items-center gap-1">
            <Icon className="w-3 h-3 text-indigo-400" />
            <span>{config.label}</span>
          </span>
          {workstation.desk_id && (
            <span className="text-[9px] text-gray-500 font-mono">{workstation.desk_id}</span>
          )}
        </div>
        {workstation.current_task_title && (
          <div className="text-[10px] text-gray-200 font-semibold truncate">
            {workstation.current_task_title}
          </div>
        )}
        {workstation.active_tool_name && (
          <div className="text-[9px] text-cyan-300 font-mono truncate">
            Tool: {workstation.active_tool_name}
          </div>
        )}
      </div>

      {/* Tooltip on Hover */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-[#0f172a] text-gray-200 text-[10px] px-2.5 py-1.5 rounded-lg border border-white/20 whitespace-nowrap z-30 shadow-xl">
        Click to inspect {workstation.employee_name} ({workstation.role})
      </div>
    </div>
  );
};
