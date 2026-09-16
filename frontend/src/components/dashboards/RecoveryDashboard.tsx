import React from 'react';
import { RefreshCw, AlertTriangle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { CompanyOverview } from '../../types/office';

interface RecoveryDashboardProps {
  overview: CompanyOverview | null;
}

export const RecoveryDashboard: React.FC<RecoveryDashboardProps> = ({ overview }) => {
  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-amber-400 font-bold text-lg">
          <RefreshCw className="w-6 h-6 text-amber-500" />
          <span>Failure Recovery & Resilience Dashboard</span>
        </div>
        <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 px-3 py-1 rounded-full font-semibold">
          Autonomous Fault Isolation
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-panel p-4 border border-amber-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Active Recovery Incidents</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300">{overview?.active_recoveries_count || 0}</div>
          <p className="text-[10px] text-gray-500 mt-1">In-flight retry and reassignment workflows</p>
        </div>

        <div className="glass-panel p-4 border border-emerald-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold mb-1">
            <span>Self-Healed System Tasks</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300">100%</div>
          <p className="text-[10px] text-gray-500 mt-1">Automatic retry isolation & task reassignment</p>
        </div>
      </div>
    </div>
  );
};
