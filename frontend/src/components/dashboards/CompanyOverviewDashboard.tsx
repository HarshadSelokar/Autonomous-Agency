import React from 'react';
import { CompanyOverview } from '../../types/office';
import {
  Building2,
  Users,
  CheckSquare,
  AlertTriangle,
  FolderKanban,
  Bell,
  ShieldCheck,
  RefreshCw,
  FileText,
  Lightbulb,
  FlaskConical,
  Activity,
  ArrowRight,
} from 'lucide-react';

interface CompanyOverviewDashboardProps {
  overview: CompanyOverview | null;
  onNavigateView: (view: string) => void;
}

export const CompanyOverviewDashboard: React.FC<CompanyOverviewDashboardProps> = ({
  overview,
  onNavigateView,
}) => {
  if (!overview) {
    return (
      <div className="flex-1 bg-[#090d16] p-8 flex items-center justify-center text-gray-500 text-xs">
        Loading Company Operating Overview...
      </div>
    );
  }

  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      {/* Top Banner Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h1 className="text-lg font-bold text-gray-100 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-400" />
            <span>{overview.company_name} — Executive Command Dashboard</span>
          </h1>
          <p className="text-xs text-gray-400">
            Real-time visual observability & governance projection layer for Autonomous AI Operations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {overview.is_emergency_stopped ? (
            <span className="bg-rose-500/20 text-rose-300 border border-rose-500/50 px-3 py-1 rounded-full font-bold animate-pulse">
              EMERGENCY STOPPED
            </span>
          ) : (
            <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-3 py-1 rounded-full font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              OPERATIONAL
            </span>
          )}
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Employees */}
        <div
          onClick={() => onNavigateView('canvas')}
          className="glass-panel p-4 space-y-2 cursor-pointer hover:border-indigo-500/50 transition-all group"
        >
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>Active Employees</span>
            <Users className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-indigo-300">
            {overview.active_employees_count}
          </div>
          <div className="text-[10px] text-gray-400 flex items-center justify-between">
            <span>{overview.working_employees_count} Working | {overview.in_meeting_employees_count} Meeting</span>
            <ArrowRight className="w-3 h-3 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Active Projects */}
        <div
          onClick={() => onNavigateView('projects')}
          className="glass-panel p-4 space-y-2 cursor-pointer hover:border-purple-500/50 transition-all group"
        >
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>Active Projects</span>
            <FolderKanban className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-purple-300">
            {overview.active_projects_count}
          </div>
          <div className="text-[10px] text-gray-400 flex items-center justify-between">
            <span>{overview.blocked_tasks_count} Blocked Tasks</span>
            <ArrowRight className="w-3 h-3 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Pending Governance Approvals */}
        <div
          onClick={() => onNavigateView('governance')}
          className="glass-panel p-4 space-y-2 cursor-pointer hover:border-amber-500/50 transition-all group"
        >
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>Pending Approvals</span>
            <Bell className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-amber-300">
            {overview.pending_approvals_count}
          </div>
          <div className="text-[10px] text-amber-400 flex items-center justify-between font-semibold">
            <span>Action Required</span>
            <ArrowRight className="w-3 h-3 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Active Recoveries & Failures */}
        <div
          onClick={() => onNavigateView('recovery')}
          className="glass-panel p-4 space-y-2 cursor-pointer hover:border-rose-500/50 transition-all group"
        >
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>Active Recoveries</span>
            <RefreshCw className="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-rose-300">
            {overview.active_recoveries_count}
          </div>
          <div className="text-[10px] text-gray-400 flex items-center justify-between">
            <span>{overview.failed_verifications_count} Verification Failures</span>
            <ArrowRight className="w-3 h-3 text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>

      {/* Middle Section: Human Attention Queue & Knowledge / Innovation Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Human Attention Queue */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2 font-bold text-amber-400">
              <Bell className="w-4 h-4" />
              <span>Human Attention Queue ({overview.attention_items.length})</span>
            </div>
            <button
              onClick={() => onNavigateView('governance')}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              <span>View Governance Center</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {overview.attention_items.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-xs">
                No items currently require human attention.
              </div>
            ) : (
              overview.attention_items.map((item) => (
                <div
                  key={item.item_id}
                  className="bg-white/5 border border-amber-500/30 rounded-xl p-3 flex items-start justify-between hover:bg-white/10 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="bg-amber-500/20 text-amber-300 text-[9px] font-bold px-2 py-0.5 rounded border border-amber-500/40">
                        {item.severity}
                      </span>
                      <span className="font-bold text-gray-200">{item.title}</span>
                    </div>
                    <p className="text-gray-400 text-[11px]">{item.description}</p>
                  </div>
                  <button
                    onClick={() => onNavigateView('governance')}
                    className="bg-amber-600 hover:bg-amber-700 text-white font-bold text-[10px] px-3 py-1.5 rounded-lg transition-all"
                  >
                    Action
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Col: Knowledge & Innovation Projection */}
        <div className="glass-panel p-5 space-y-4">
          <div className="flex items-center gap-2 font-bold text-purple-400 border-b border-white/10 pb-3">
            <FlaskConical className="w-4 h-4" />
            <span>Knowledge & Research Engine</span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5 border border-white/5">
              <span className="text-gray-400 flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                Validated Knowledge
              </span>
              <span className="font-bold text-indigo-300">{overview.validated_knowledge_count}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5 border border-white/5">
              <span className="text-gray-400 flex items-center gap-2">
                <FlaskConical className="w-3.5 h-3.5 text-pink-400" />
                Research Programs
              </span>
              <span className="font-bold text-pink-300">{overview.active_research_programs_count}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5 border border-white/5">
              <span className="text-gray-400 flex items-center gap-2">
                <Lightbulb className="w-3.5 h-3.5 text-purple-400" />
                Innovation Proposals
              </span>
              <span className="font-bold text-purple-300">{overview.innovation_proposals_count}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
