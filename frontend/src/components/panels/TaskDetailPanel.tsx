import React from 'react';
import { TaskInfo } from '../../types/office';
import { X, CheckSquare, Clock, User, ShieldCheck, RefreshCw, AlertCircle } from 'lucide-react';

interface TaskDetailPanelProps {
  task: TaskInfo | null;
  onClose: () => void;
}

export const TaskDetailPanel: React.FC<TaskDetailPanelProps> = ({ task, onClose }) => {
  if (!task) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 z-50 shadow-2xl flex flex-col p-6 overflow-y-auto animate-slide-left">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-white/10 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/30 border border-blue-500/50 flex items-center justify-center text-blue-300">
            <CheckSquare className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-gray-400">{task.task_id}</span>
            <h2 className="text-sm font-bold text-gray-100">{task.title}</h2>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4 text-xs">
        {/* State & Priority */}
        <div className="grid grid-cols-2 gap-2">
          <div className="glass-panel p-3">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">State</span>
            <p className="font-bold text-blue-400 mt-1">{task.state}</p>
          </div>
          <div className="glass-panel p-3">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Priority</span>
            <p className="font-bold text-amber-400 mt-1">{task.priority}</p>
          </div>
        </div>

        {/* Description */}
        {task.description && (
          <div className="glass-panel p-3 space-y-1">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Description</span>
            <p className="text-gray-300 text-[11px] leading-relaxed">{task.description}</p>
          </div>
        )}

        {/* Assignee */}
        <div className="glass-panel p-3 space-y-1">
          <div className="flex items-center gap-2 text-indigo-400 font-bold">
            <User className="w-3.5 h-3.5" />
            <span>Assigned Employee</span>
          </div>
          <p className="font-mono text-gray-200">{task.assignee_id || 'Unassigned'}</p>
        </div>

        {/* Verification Status */}
        <div className="glass-panel p-3 space-y-1 border border-emerald-500/30">
          <div className="flex items-center gap-2 text-emerald-400 font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verification Status</span>
          </div>
          <p className="font-semibold text-emerald-300">{task.verification_status || 'VERIFIED'}</p>
        </div>

        {/* Recovery History */}
        <div className="glass-panel p-3 space-y-1 border border-amber-500/30">
          <div className="flex items-center gap-2 text-amber-400 font-bold">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Recovery Status</span>
          </div>
          <p className="font-semibold text-amber-300">{task.recovery_status || 'NOMINAL'}</p>
        </div>

        {/* Dependencies */}
        {task.dependencies && task.dependencies.length > 0 && (
          <div className="glass-panel p-3 space-y-1">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">DAG Dependencies</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {task.dependencies.map((dep) => (
                <span key={dep} className="bg-white/10 text-gray-300 font-mono text-[10px] px-2 py-0.5 rounded">
                  {dep}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
