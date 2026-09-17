import React from 'react';
import {
  Building2,
  Radio,
  Search,
  AlertTriangle,
  Bell,
  Activity,
  Layers,
  ShieldAlert,
} from 'lucide-react';
import { ConnectionStatus, CompanyOverview } from '../../types/office';
import { CompanySwitcher } from './CompanySwitcher';

interface AppShellProps {
  overview: CompanyOverview | null;
  connectionStatus: ConnectionStatus;
  activeView: string;
  activeCompanyId: string;
  activeEnvironment: string;
  onSelectCompany: (companyId: string) => void;
  onSelectEnvironment: (env: 'PRODUCTION' | 'SIMULATION') => void;
  onSelectView: (view: string) => void;
  onOpenSearch: () => void;
  onOpenEmergencyStop: () => void;
  onToggleActivityFeed: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  overview,
  connectionStatus,
  activeView,
  activeCompanyId,
  activeEnvironment,
  onSelectCompany,
  onSelectEnvironment,
  onSelectView,
  onOpenSearch,
  onOpenEmergencyStop,
  onToggleActivityFeed,
  children,
}) => {
  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case 'CONNECTED':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'RECONNECTING':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'STALE':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-gray-100 font-sans">
      {/* Top Navbar Header */}
      <header className="h-16 border-b border-white/10 bg-[#0f172a]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
        {/* Left: Brand & Company Switcher */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-lg cursor-pointer" onClick={() => onSelectView('canvas')}>
            <Building2 className="w-6 h-6 text-indigo-500" />
            <span className="tracking-wide bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              PIXEL OFFICE
            </span>
          </div>

          <div className="h-4 w-px bg-white/10" />

          {/* Interactive Multi-Company & Environment Switcher */}
          <CompanySwitcher
            activeCompanyId={activeCompanyId}
            activeEnvironment={activeEnvironment}
            onSelectCompany={onSelectCompany}
            onSelectEnvironment={onSelectEnvironment}
          />

          {/* Connection Status Badge */}
          <div className={`px-2.5 py-1 rounded-full border text-xs font-semibold flex items-center gap-1.5 ${getStatusColor(connectionStatus)}`}>
            <Radio className="w-3 h-3 animate-pulse" />
            <span>{connectionStatus}</span>
          </div>

          {overview?.is_emergency_stopped && (
            <div className="bg-rose-500/20 text-rose-300 border border-rose-500/50 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 animate-bounce">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>EMERGENCY STOP ACTIVE</span>
            </div>
          )}
        </div>

        {/* Center: Quick Search Trigger */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-3 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 px-4 py-1.5 rounded-xl border border-white/10 text-xs transition-all w-72 justify-between"
        >
          <span className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5" />
            <span>Search employees, tasks, teams...</span>
          </span>
          <kbd className="bg-white/10 text-gray-400 px-1.5 py-0.5 rounded text-[10px] font-mono">⌘K</kbd>
        </button>

        {/* Right: Actions & Governance Emergency Stop */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleActivityFeed}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-all relative border border-white/10"
            title="Activity Log Stream"
          >
            <Activity className="w-4 h-4 text-indigo-400" />
            {overview && overview.recent_activities.length > 0 && (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-indigo-500 rounded-full" />
            )}
          </button>

          {/* Pending Approvals Queue Badge */}
          {overview && overview.pending_approvals_count > 0 && (
            <button
              onClick={() => onSelectView('governance')}
              className="flex items-center gap-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
            >
              <Bell className="w-3.5 h-3.5" />
              <span>{overview.pending_approvals_count} Approvals</span>
            </button>
          )}

          {/* Emergency Stop Button */}
          <button
            onClick={onOpenEmergencyStop}
            className="flex items-center gap-1.5 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/60 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all shadow-lg hover:shadow-rose-900/30"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>EMERGENCY STOP</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">{children}</div>
    </div>
  );
};
