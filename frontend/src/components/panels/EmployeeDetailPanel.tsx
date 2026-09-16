import React from 'react';
import { WorkstationProjection } from '../../types/office';
import {
  X,
  User,
  Building,
  CheckSquare,
  Cpu,
  Wrench,
  Activity,
  Layers,
} from 'lucide-react';

interface EmployeeDetailPanelProps {
  workstation: WorkstationProjection | null;
  onClose: () => void;
}

export const EmployeeDetailPanel: React.FC<EmployeeDetailPanelProps> = ({
  workstation,
  onClose,
}) => {
  if (!workstation) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 z-50 shadow-2xl flex flex-col p-6 overflow-y-auto animate-slide-left">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-white/10 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center text-indigo-300 font-bold text-sm">
            {workstation.employee_name.charAt(0)}
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-100">{workstation.employee_name}</h2>
            <p className="text-xs text-gray-400">{workstation.employee_title}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Details */}
      <div className="space-y-4 text-xs">
        {/* Status Badge */}
        <div className="glass-panel p-3 space-y-1">
          <div className="text-[10px] text-gray-400 font-semibold uppercase">Current Visual State</div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse" />
            <span className="font-bold text-blue-300">{workstation.visual_state}</span>
          </div>
        </div>

        {/* Organizational Assignment */}
        <div className="glass-panel p-3 space-y-2">
          <div className="flex items-center gap-2 text-indigo-400 font-bold border-b border-white/5 pb-1">
            <Building className="w-3.5 h-3.5" />
            <span>Organizational Context</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-gray-500">Department:</span>
              <p className="font-medium text-gray-200">{workstation.department_id}</p>
            </div>
            <div>
              <span className="text-gray-500">Role:</span>
              <p className="font-medium text-gray-200">{workstation.role}</p>
            </div>
            <div>
              <span className="text-gray-500">Desk ID:</span>
              <p className="font-mono text-gray-300">{workstation.desk_id}</p>
            </div>
            <div>
              <span className="text-gray-500">Manager:</span>
              <p className="font-medium text-gray-200">{workstation.is_manager ? 'Self (Manager)' : workstation.manager_id || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Current Active Task & Project */}
        <div className="glass-panel p-3 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-bold border-b border-white/5 pb-1">
            <CheckSquare className="w-3.5 h-3.5" />
            <span>Active Assignment</span>
          </div>
          {workstation.current_task_title ? (
            <div className="space-y-1 text-[11px]">
              <div className="text-gray-400 text-[10px]">Task ID: {workstation.current_task_id}</div>
              <div className="font-semibold text-gray-200">{workstation.current_task_title}</div>
              {workstation.current_project_name && (
                <div className="text-emerald-300 text-[10px]">Project: {workstation.current_project_name}</div>
              )}
            </div>
          ) : (
            <div className="text-gray-500 text-[11px] italic">No active task assigned</div>
          )}
        </div>

        {/* Execution & Model Engine Context */}
        <div className="glass-panel p-3 space-y-2">
          <div className="flex items-center gap-2 text-purple-400 font-bold border-b border-white/5 pb-1">
            <Cpu className="w-3.5 h-3.5" />
            <span>Agent & Model Engine</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div>
              <span className="text-gray-500">Active Agent ID:</span>
              <p className="font-mono text-purple-300">{workstation.active_agent_id || 'None'}</p>
            </div>
            <div>
              <span className="text-gray-500">Model Router Model:</span>
              <p className="font-mono text-purple-300">{workstation.active_model_id || 'groq/llama-3.3-70b-versatile'}</p>
            </div>
            {workstation.active_tool_name && (
              <div>
                <span className="text-gray-500">Active Tool Execution:</span>
                <p className="font-mono text-cyan-300 flex items-center gap-1">
                  <Wrench className="w-3 h-3" />
                  {workstation.active_tool_name}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Current Activity Summary */}
        <div className="glass-panel p-3 space-y-1">
          <div className="flex items-center gap-2 text-gray-400 font-bold">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span>Live Activity Summary</span>
          </div>
          <p className="text-[11px] text-gray-300">{workstation.current_activity_summary}</p>
        </div>
      </div>
    </div>
  );
};
