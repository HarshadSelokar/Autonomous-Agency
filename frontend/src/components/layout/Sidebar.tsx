import React from 'react';
import {
  LayoutDashboard,
  Grid,
  Building,
  Users,
  FolderKanban,
  CheckSquare,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  UserPlus,
  FlaskConical,
  Server,
  DollarSign,
  Target,
  Brain,
  GraduationCap,
} from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onSelectView: (view: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onSelectView }) => {
  const navItems = [
    { id: 'overview', label: 'Company Overview', icon: LayoutDashboard },
    { id: 'intelligence', label: 'Company Intelligence', icon: Brain },
    { id: 'learning', label: 'Organizational Learning', icon: GraduationCap },
    { id: 'companies', label: 'Companies & Tenants', icon: Building },
    { id: 'simulations', label: 'What-If Simulations', icon: FlaskConical },
    { id: 'canvas', label: 'Pixel Office Canvas', icon: Grid },
    { id: 'business', label: 'Business & Finance', icon: DollarSign },
    { id: 'gtm', label: 'Product & GTM', icon: Target },
    { id: 'departments', label: 'Departments', icon: Building },
    { id: 'teams', label: 'Dynamic Teams', icon: Users },
    { id: 'projects', label: 'Software Projects', icon: FolderKanban },
    { id: 'tasks', label: 'Tasks & DAG', icon: CheckSquare },
    { id: 'meetings', label: 'Active Meetings', icon: Calendar },
    { id: 'governance', label: 'Governance Control', icon: ShieldCheck },
    { id: 'verification', label: 'Verification Engine', icon: CheckCircle2 },
    { id: 'recovery', label: 'Failure Recovery', icon: RefreshCw },
    { id: 'workforce', label: 'Workforce Allocation', icon: UserPlus },
    { id: 'research', label: 'Research & Innovation', icon: FlaskConical },
    { id: 'infrastructure', label: 'Infrastructure Health', icon: Server },
  ];

  return (
    <aside className="w-64 bg-[#0f172a]/60 backdrop-blur-md border-r border-white/10 p-4 flex flex-col gap-2 select-none overflow-y-auto">
      <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider px-3 mb-1">
        Navigation
      </div>
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeView === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelectView(item.id)}
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
              isActive
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
            }`}
          >
            <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-gray-500'}`} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </aside>
  );
};
