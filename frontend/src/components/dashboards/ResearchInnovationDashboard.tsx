import React from 'react';
import { FlaskConical, Lightbulb, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';
import { CompanyOverview } from '../../types/office';

interface ResearchInnovationDashboardProps {
  overview: CompanyOverview | null;
}

export const ResearchInnovationDashboard: React.FC<ResearchInnovationDashboardProps> = ({ overview }) => {
  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-pink-400 font-bold text-lg">
          <FlaskConical className="w-6 h-6 text-pink-500" />
          <span>Phase 19 Autonomous Research, Discovery & Innovation Dashboard</span>
        </div>
        <span className="bg-pink-500/20 text-pink-300 border border-pink-500/40 px-3 py-1 rounded-full font-semibold">
          Source Independence & Evidence Hashing
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 border border-pink-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Research Programs</span>
            <FlaskConical className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-2xl font-bold text-pink-300">{overview?.active_research_programs_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Active strategic research questions</p>
        </div>

        <div className="glass-panel p-4 border border-amber-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Pending Requests</span>
            <FileText className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300">{overview?.pending_research_requests_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Unprocessed knowledge gaps</p>
        </div>

        <div className="glass-panel p-4 border border-indigo-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Discoveries</span>
            <CheckCircle2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-300">{overview?.research_discoveries_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Validated benchmark findings</p>
        </div>

        <div className="glass-panel p-4 border border-purple-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Innovation Proposals</span>
            <Lightbulb className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300">{overview?.innovation_proposals_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Governed initiative proposals</p>
        </div>
      </div>
    </div>
  );
};
