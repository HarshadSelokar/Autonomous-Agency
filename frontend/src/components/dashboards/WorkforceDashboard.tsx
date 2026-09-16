import React from 'react';
import { UserPlus, Users, Cpu, ShieldCheck } from 'lucide-react';
import { CompanyOverview } from '../../types/office';

interface WorkforceDashboardProps {
  overview: CompanyOverview | null;
}

export const WorkforceDashboard: React.FC<WorkforceDashboardProps> = ({ overview }) => {
  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-purple-400 font-bold text-lg">
          <UserPlus className="w-6 h-6 text-purple-500" />
          <span>Dynamic Workforce Allocation Dashboard</span>
        </div>
        <span className="bg-purple-500/20 text-purple-300 border border-purple-500/40 px-3 py-1 rounded-full font-semibold">
          Capability Matching Engine
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 border border-purple-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Active Employee Workforce</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300">{overview?.active_employees_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Cross-department organizational employees</p>
        </div>

        <div className="glass-panel p-4 border border-blue-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Working Employees</span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-300">{overview?.working_employees_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Currently executing active work items</p>
        </div>

        <div className="glass-panel p-4 border border-pink-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>In Executive Meetings</span>
            <Users className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-2xl font-bold text-pink-300">{overview?.in_meeting_employees_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Participating in strategy discussions</p>
        </div>
      </div>
    </div>
  );
};
