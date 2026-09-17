import React, { useState, useEffect } from 'react';
import { Building2, ChevronDown, Check, ShieldAlert, Sparkles, Server } from 'lucide-react';

export interface CompanySummary {
  id: string;
  name: string;
  slug: string;
  lifecycle: string;
  company_type: string;
  industry: string;
  is_active: boolean;
}

interface CompanySwitcherProps {
  activeCompanyId: string;
  activeEnvironment: string;
  onSelectCompany: (companyId: string) => void;
  onSelectEnvironment: (env: 'PRODUCTION' | 'SIMULATION') => void;
}

export const CompanySwitcher: React.FC<CompanySwitcherProps> = ({
  activeCompanyId,
  activeEnvironment,
  onSelectCompany,
  onSelectEnvironment,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [companies, setCompanies] = useState<CompanySummary[]>([
    {
      id: 'comp-main-01',
      name: 'Autonomous AI Enterprise',
      slug: 'autonomous-ai-enterprise',
      lifecycle: 'ACTIVE',
      company_type: 'AUTONOMOUS',
      industry: 'ENTERPRISE_SOFTWARE',
      is_active: true,
    },
    {
      id: 'comp-starlight-01',
      name: 'Starlight Autonomous Robotics',
      slug: 'starlight-robotics',
      lifecycle: 'PROPOSED',
      company_type: 'AUTONOMOUS',
      industry: 'ROBOTICS',
      is_active: true,
    },
  ]);

  useEffect(() => {
    fetch('/api/v1/companies')
      .then((res) => {
        if (res.ok) return res.json();
        return [];
      })
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setCompanies(data);
        }
      })
      .catch((err) => console.warn('Using cached company list:', err));
  }, []);

  const activeCompany = companies.find((c) => c.id === activeCompanyId) || companies[0];

  return (
    <div className="relative inline-block text-left">
      <div className="flex items-center gap-2">
        {/* Company Dropdown Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg border border-white/10 text-xs font-medium text-gray-200 transition-all cursor-pointer"
        >
          <Building2 className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold">{activeCompany.name}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono">
            {activeCompany.slug}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-gray-400 ml-1" />
        </button>

        {/* Environment Badge & Toggle */}
        <button
          onClick={() =>
            onSelectEnvironment(activeEnvironment === 'PRODUCTION' ? 'SIMULATION' : 'PRODUCTION')
          }
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-bold transition-all ${
            activeEnvironment === 'PRODUCTION'
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
              : 'bg-amber-500/20 text-amber-300 border-amber-500/50 hover:bg-amber-500/30 animate-pulse'
          }`}
          title="Click to toggle between Production and What-If Simulation sandbox mode"
        >
          {activeEnvironment === 'PRODUCTION' ? (
            <>
              <Server className="w-3 h-3 text-emerald-400" />
              <span>PROD</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3 h-3 text-amber-300" />
              <span>SIMULATION</span>
            </>
          )}
        </button>
      </div>

      {/* Menu Overlay */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 rounded-xl bg-[#0f172a] border border-white/15 shadow-2xl z-50 overflow-hidden">
          <div className="p-3 border-b border-white/10 flex items-center justify-between text-[11px] text-gray-400 font-bold uppercase tracking-wider">
            <span>Select Tenant / Company</span>
            <span className="text-indigo-400">{companies.length} Companies</span>
          </div>

          <div className="max-h-64 overflow-y-auto p-1.5 space-y-1">
            {companies.map((comp) => {
              const isSelected = comp.id === activeCompany.id;
              return (
                <button
                  key={comp.id}
                  onClick={() => {
                    onSelectCompany(comp.id);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left text-xs transition-all ${
                    isSelected
                      ? 'bg-indigo-600/30 border border-indigo-500/40 text-white'
                      : 'hover:bg-white/5 text-gray-300'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-gray-200">{comp.name}</span>
                    <span className="text-[10px] text-gray-400 font-mono">{comp.slug}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                        comp.lifecycle === 'ACTIVE'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      }`}
                    >
                      {comp.lifecycle}
                    </span>
                    {isSelected && <Check className="w-4 h-4 text-indigo-400" />}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="p-2 border-t border-white/10 bg-white/5 text-center">
            <span className="text-[10px] text-gray-400 flex items-center justify-center gap-1">
              <ShieldAlert className="w-3 h-3 text-indigo-400" />
              Tenant Isolation Enforced by Kernel Middleware
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
