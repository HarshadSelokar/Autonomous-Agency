import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  Cpu,
  Database,
  DollarSign,
  Plus,
  ShieldCheck,
  Share2,
  Lock,
  Layers,
  Activity,
  CheckCircle,
  AlertCircle,
  BarChart3,
} from 'lucide-react';

interface CompanyQuota {
  max_agents: number;
  max_employees: number;
  monthly_budget_cents: number;
  max_storage_gb: number;
  current_agents: number;
  current_employees: number;
  current_monthly_spend_cents: number;
  current_storage_gb: number;
}

interface CompanyItem {
  id: string;
  name: string;
  slug: string;
  lifecycle: string;
  company_type: string;
  industry: string;
  quota: CompanyQuota;
}

export const CompanyDashboard: React.FC = () => {
  const [companies, setCompanies] = useState<CompanyItem[]>([
    {
      id: 'comp-main-01',
      name: 'Autonomous AI Enterprise',
      slug: 'autonomous-ai-enterprise',
      lifecycle: 'ACTIVE',
      company_type: 'AUTONOMOUS',
      industry: 'ENTERPRISE_SOFTWARE',
      quota: {
        max_agents: 50,
        max_employees: 30,
        monthly_budget_cents: 5000000,
        max_storage_gb: 500,
        current_agents: 18,
        current_employees: 12,
        current_monthly_spend_cents: 1850000,
        current_storage_gb: 120,
      },
    },
    {
      id: 'comp-starlight-01',
      name: 'Starlight Autonomous Robotics',
      slug: 'starlight-robotics',
      lifecycle: 'PROPOSED',
      company_type: 'AUTONOMOUS',
      industry: 'ROBOTICS',
      quota: {
        max_agents: 20,
        max_employees: 10,
        monthly_budget_cents: 2000000,
        max_storage_gb: 200,
        current_agents: 4,
        current_employees: 2,
        current_monthly_spend_cents: 350000,
        current_storage_gb: 15,
      },
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCompany, setNewCompany] = useState({
    name: '',
    slug: '',
    description: '',
    industry: 'TECHNOLOGY',
    company_type: 'AUTONOMOUS',
  });

  const [crossCompanyShareRequests] = useState([
    {
      id: 'req-share-101',
      source_company: 'Autonomous AI Enterprise',
      target_company: 'Starlight Autonomous Robotics',
      resource_type: 'PRODUCT_CATALOG',
      status: 'APPROVED',
      governance_approval_id: 'gov-appr-888',
    },
    {
      id: 'req-share-102',
      source_company: 'Starlight Autonomous Robotics',
      target_company: 'Autonomous AI Enterprise',
      resource_type: 'FINANCIAL_RECORDS',
      status: 'PENDING_HUMAN_GOVERNANCE',
      governance_approval_id: 'gov-appr-889',
    },
  ]);

  const handleCreateCompany = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany.name || !newCompany.slug) return;
    const createdItem: CompanyItem = {
      id: `comp-${Date.now().toString(36)}`,
      name: newCompany.name,
      slug: newCompany.slug,
      lifecycle: 'PROPOSED',
      company_type: newCompany.company_type,
      industry: newCompany.industry,
      quota: {
        max_agents: 20,
        max_employees: 10,
        monthly_budget_cents: 1000000,
        max_storage_gb: 100,
        current_agents: 0,
        current_employees: 0,
        current_monthly_spend_cents: 0,
        current_storage_gb: 0,
      },
    };
    setCompanies([...companies, createdItem]);
    setIsModalOpen(false);
    setNewCompany({ name: '', slug: '', description: '', industry: 'TECHNOLOGY', company_type: 'AUTONOMOUS' });
  };

  return (
    <div className="flex-1 bg-[#090d16] p-6 text-gray-100 overflow-y-auto space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent flex items-center gap-2">
            <Building2 className="w-6 h-6 text-indigo-400" />
            Multi-Company Multi-Tenant Platform & Quota Operations
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Isolated tenant boundaries, autonomous company lifecycles, and cross-company governance governance.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-lg transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Provision New Autonomous Company</span>
        </button>
      </div>

      {/* Security & Tenant Boundary Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-emerald-400" />
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400">Tenant Isolation</span>
            <h3 className="text-sm font-semibold text-emerald-300">Strict Boundary Active</h3>
          </div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
          <Layers className="w-8 h-8 text-indigo-400" />
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400">Total Companies</span>
            <h3 className="text-sm font-semibold text-indigo-300">{companies.length} Tenants Provisioned</h3>
          </div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
          <Share2 className="w-8 h-8 text-purple-400" />
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400">Cross-Company Sharing</span>
            <h3 className="text-sm font-semibold text-purple-300">Denied by Default</h3>
          </div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
          <Lock className="w-8 h-8 text-amber-400" />
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400">Governance Gateway</span>
            <h3 className="text-sm font-semibold text-amber-300">Human Approval Enforced</h3>
          </div>
        </div>
      </div>

      {/* Provisioned Companies & Quota Utilization */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-400" />
          Managed Companies & Resource Quotas
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {companies.map((comp) => (
            <div
              key={comp.id}
              className="bg-[#0f172a]/70 border border-white/10 rounded-xl p-5 hover:border-indigo-500/40 transition-all space-y-4 shadow-xl"
            >
              <div className="flex items-start justify-between border-b border-white/10 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">{comp.name}</h3>
                    <span className="text-[10px] bg-indigo-500/20 text-indigo-300 font-mono px-2 py-0.5 rounded border border-indigo-500/30">
                      {comp.slug}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {comp.industry} • {comp.company_type}
                  </p>
                </div>
                <span
                  className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase ${
                    comp.lifecycle === 'ACTIVE'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  }`}
                >
                  {comp.lifecycle}
                </span>
              </div>

              {/* Quotas & Capacity Usage Bars */}
              <div className="grid grid-cols-2 gap-4">
                {/* Agents Quota */}
                <div className="bg-white/5 p-3 rounded-lg border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Agents
                    </span>
                    <span className="font-semibold text-gray-200">
                      {comp.quota.current_agents} / {comp.quota.max_agents}
                    </span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (comp.quota.current_agents / comp.quota.max_agents) * 100)}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Employees Quota */}
                <div className="bg-white/5 p-3 rounded-lg border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-purple-400" /> Employees
                    </span>
                    <span className="font-semibold text-gray-200">
                      {comp.quota.current_employees} / {comp.quota.max_employees}
                    </span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-purple-500 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (comp.quota.current_employees / comp.quota.max_employees) * 100)}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Budget Quota */}
                <div className="bg-white/5 p-3 rounded-lg border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-emerald-400" /> Budget Spend
                    </span>
                    <span className="font-semibold text-gray-200">
                      ${(comp.quota.current_monthly_spend_cents / 100).toLocaleString()} / ${ (comp.quota.monthly_budget_cents / 100).toLocaleString() }
                    </span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (comp.quota.current_monthly_spend_cents / comp.quota.monthly_budget_cents) * 100)}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Storage Quota */}
                <div className="bg-white/5 p-3 rounded-lg border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-amber-400" /> Storage
                    </span>
                    <span className="font-semibold text-gray-200">
                      {comp.quota.current_storage_gb} GB / {comp.quota.max_storage_gb} GB
                    </span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-amber-500 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (comp.quota.current_storage_gb / comp.quota.max_storage_gb) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-Company Data Sharing & Governance Log */}
      <div className="bg-[#0f172a]/70 border border-white/10 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
          <Share2 className="w-4 h-4 text-purple-400" />
          Cross-Company Data Sharing Requests
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-white/5 uppercase text-[10px] text-gray-400 font-bold border-b border-white/10">
              <tr>
                <th className="p-3">Request ID</th>
                <th className="p-3">Source Company</th>
                <th className="p-3">Target Company</th>
                <th className="p-3">Resource Type</th>
                <th className="p-3">Governance Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {crossCompanyShareRequests.map((req) => (
                <tr key={req.id} className="hover:bg-white/5">
                  <td className="p-3 font-mono text-indigo-300">{req.id}</td>
                  <td className="p-3 font-medium">{req.source_company}</td>
                  <td className="p-3 font-medium">{req.target_company}</td>
                  <td className="p-3">
                    <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded font-mono text-[10px]">
                      {req.resource_type}
                    </span>
                  </td>
                  <td className="p-3">
                    {req.status === 'APPROVED' ? (
                      <span className="flex items-center gap-1 text-emerald-400 font-bold">
                        <CheckCircle className="w-3.5 h-3.5" /> Approved
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-300 font-bold animate-pulse">
                        <AlertCircle className="w-3.5 h-3.5" /> Pending Governance
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Company Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0f172a] border border-white/15 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-indigo-400" />
              Provision New Autonomous Company
            </h3>

            <form onSubmit={handleCreateCompany} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-400 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                  placeholder="e.g., Nova Robotics Inc"
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-1">Company Slug</label>
                <input
                  type="text"
                  required
                  value={newCompany.slug}
                  onChange={(e) => setNewCompany({ ...newCompany, slug: e.target.value })}
                  placeholder="e.g., nova-robotics"
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-1">Industry Sector</label>
                <select
                  value={newCompany.industry}
                  onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                  className="w-full bg-[#1e293b] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="ENTERPRISE_SOFTWARE">Enterprise Software</option>
                  <option value="ROBOTICS">Robotics & Hardware</option>
                  <option value="FINTECH">Fintech & Finance</option>
                  <option value="BIOTECH">Biotech & Health</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Provision Company
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
