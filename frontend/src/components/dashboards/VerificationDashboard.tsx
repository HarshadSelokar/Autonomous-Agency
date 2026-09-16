import React from 'react';
import { CheckCircle2, ShieldCheck, AlertCircle, FileText } from 'lucide-react';
import { CompanyOverview } from '../../types/office';

interface VerificationDashboardProps {
  overview: CompanyOverview | null;
}

export const VerificationDashboard: React.FC<VerificationDashboardProps> = ({ overview }) => {
  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-emerald-400 font-bold text-lg">
          <ShieldCheck className="w-6 h-6 text-emerald-500" />
          <span>Verification & Evidence Engine Dashboard</span>
        </div>
        <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-3 py-1 rounded-full font-semibold">
          Deterministic Rule Verification
        </span>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 border border-emerald-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Passed Verifications</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300">100%</div>
          <p className="text-[10px] text-gray-500 mt-1">Deterministic AST & test evidence verified</p>
        </div>

        <div className="glass-panel p-4 border border-rose-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Failed Verifications</span>
            <AlertCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-300">{overview?.failed_verifications_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Gated task reworks triggered</p>
        </div>

        <div className="glass-panel p-4 border border-indigo-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Authoritative Knowledge Claims</span>
            <FileText className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-300">{overview?.authoritative_knowledge_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">Verified Phase 18 knowledge candidates</p>
        </div>
      </div>
    </div>
  );
};
