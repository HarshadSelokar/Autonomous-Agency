import React from 'react';
import { ProjectInfo } from '../../types/office';
import { X, FolderKanban, CheckCircle2, AlertTriangle, Users } from 'lucide-react';

interface ProjectDetailPanelProps {
  project: ProjectInfo | null;
  onClose: () => void;
}

export const ProjectDetailPanel: React.FC<ProjectDetailPanelProps> = ({ project, onClose }) => {
  if (!project) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 z-50 shadow-2xl flex flex-col p-6 overflow-y-auto animate-slide-left">
      <div className="flex items-start justify-between border-b border-white/10 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-600/30 border border-purple-500/50 flex items-center justify-center text-purple-300">
            <FolderKanban className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-gray-400">{project.project_id}</span>
            <h2 className="text-sm font-bold text-gray-100">{project.name}</h2>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4 text-xs">
        {/* Progress Bar */}
        <div className="glass-panel p-3 space-y-2">
          <div className="flex justify-between text-[11px]">
            <span className="text-gray-400 font-semibold">Delivery Progress</span>
            <span className="font-bold text-indigo-300">{project.progress_percentage}%</span>
          </div>
          <div className="w-full bg-black/40 h-2 rounded-full overflow-hidden border border-white/10">
            <div
              className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full transition-all duration-500"
              style={{ width: `${project.progress_percentage}%` }}
            />
          </div>
        </div>

        {/* Objective */}
        <div className="glass-panel p-3 space-y-1">
          <span className="text-[10px] text-gray-400 font-semibold uppercase">Project Objective</span>
          <p className="text-gray-200 text-[11px] leading-relaxed">{project.objective}</p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-2">
          <div className="glass-panel p-3">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Total Tasks</span>
            <p className="font-bold text-gray-200 mt-1">{project.task_count}</p>
          </div>
          <div className="glass-panel p-3 border border-rose-500/30">
            <span className="text-[10px] text-rose-400 font-semibold uppercase">Blocked Tasks</span>
            <p className="font-bold text-rose-300 mt-1">{project.blocked_task_count}</p>
          </div>
        </div>

        {/* Manager & Team */}
        <div className="glass-panel p-3 space-y-1">
          <div className="flex items-center gap-2 text-indigo-400 font-bold">
            <Users className="w-3.5 h-3.5" />
            <span>Assigned Team & Manager</span>
          </div>
          <div className="text-[11px] space-y-1 pt-1">
            <div><span className="text-gray-500">Manager:</span> <span className="font-medium text-gray-200">{project.manager_id || 'N/A'}</span></div>
            <div><span className="text-gray-500">Team:</span> <span className="font-medium text-gray-200">{project.team_id || 'N/A'}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
