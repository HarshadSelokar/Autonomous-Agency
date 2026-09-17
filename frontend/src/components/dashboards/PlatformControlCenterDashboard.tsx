import React, { useState, useEffect } from 'react';
import {
  Globe,
  Activity,
  Layers,
  Users,
  CheckCircle2,
  AlertCircle,
  Play,
  CheckSquare,
  ShieldCheck,
  TrendingUp,
  Cpu,
  Lock,
  Workflow,
  Sparkles,
  RefreshCw,
} from 'lucide-react';

interface HealthDimension {
  name: string;
  score: number;
  status: 'EXCELLENT' | 'GOOD' | 'WARNING';
}

interface WorkflowItem {
  workflow_id: string;
  name: string;
  category: string;
  state: string;
  current_step: string;
  started_at: string;
}

export const PlatformControlCenterDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'executive' | 'manager' | 'employee' | 'workflows'>('executive');
  const [healthScore, setHealthScore] = useState<number>(96.2);
  const [lifecycleState, setLifecycleState] = useState<string>('ACTIVE');
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchPlatformData = async () => {
    setLoading(true);
    try {
      setWorkflows([
        {
          workflow_id: 'wf-901',
          name: 'Q4 Autonomous Venture Launch',
          category: 'VENTURE_LAUNCH',
          state: 'RUNNING',
          current_step: '4_CAPITAL_ALLOCATION',
          started_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          workflow_id: 'wf-902',
          name: 'Enterprise Shared Service SLA Provisioning',
          category: 'ENTERPRISE_COORDINATION',
          state: 'COMPLETED',
          current_step: 'COMPLETED',
          started_at: new Date(Date.now() - 7200000).toISOString(),
        },
        {
          workflow_id: 'wf-903',
          name: 'Software Delivery Pipeline & Verification',
          category: 'SOFTWARE_DELIVERY',
          state: 'VERIFYING',
          current_step: '3_EVIDENCE_COLLECTION',
          started_at: new Date(Date.now() - 1800000).toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlatformData();
  }, []);

  const healthDimensions: HealthDimension[] = [
    { name: 'Strategic Objectives Health', score: 95.0, status: 'EXCELLENT' },
    { name: 'Workforce & Agent Capacity', score: 92.0, status: 'EXCELLENT' },
    { name: 'Financial Ledger & Cash Flow', score: 98.0, status: 'EXCELLENT' },
    { name: 'Infrastructure & Model Router SLA', score: 99.5, status: 'EXCELLENT' },
    { name: 'Governance & Compliance Gate', score: 100.0, status: 'EXCELLENT' },
    { name: 'Verification Engine Pass Rate', score: 96.5, status: 'EXCELLENT' },
  ];

  return (
    <div className="p-6 space-y-6 bg-slate-950 text-slate-100 min-h-screen">
      {/* Platform Banner Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Globe className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Autonomous Company Platform 1.0 Control Center
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">
                v1.0.0 Production Release
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Unified Operating System across Strategy, Workforce, Agents, Models, Governance, Verification & Enterprise OS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 text-xs font-bold rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            LIFECYCLE: {lifecycleState}
          </span>
          <button
            onClick={fetchPlatformData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh Control Plane
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('executive')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'executive'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          Executive View
        </button>

        <button
          onClick={() => setActiveTab('manager')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'manager'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Users className="w-4 h-4 text-amber-400" />
          Manager View
        </button>

        <button
          onClick={() => setActiveTab('employee')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'employee'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Cpu className="w-4 h-4 text-cyan-400" />
          Employee & Agent View
        </button>

        <button
          onClick={() => setActiveTab('workflows')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'workflows'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Workflow className="w-4 h-4 text-indigo-400" />
          Canonical Workflows & Readiness
        </button>
      </div>

      {/* Tab 1: Executive View */}
      {activeTab === 'executive' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/70 p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Overall Company Health</span>
              <div className="text-2xl font-bold text-emerald-400">{healthScore}%</div>
              <span className="text-[10px] text-slate-500">6 Multi-Dimensional Scorecards</span>
            </div>

            <div className="bg-slate-900/70 p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Blocked Tasks</span>
              <div className="text-2xl font-bold text-slate-200">0</div>
              <span className="text-[10px] text-emerald-400">All Task DAGs Clear</span>
            </div>

            <div className="bg-slate-900/70 p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Pending Governance Approvals</span>
              <div className="text-2xl font-bold text-amber-400">1</div>
              <span className="text-[10px] text-slate-500">Q4 Venture Capital Spend</span>
            </div>

            <div className="bg-slate-900/70 p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Active Ventures</span>
              <div className="text-2xl font-bold text-indigo-400">2</div>
              <span className="text-[10px] text-slate-500">HealthTech & FinTech</span>
            </div>
          </div>

          <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Multi-Dimensional Executive Scorecard
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {healthDimensions.map((dim, idx) => (
                <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{dim.name}</span>
                    <span className="font-bold text-emerald-400">{dim.score}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${dim.score}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Manager View */}
      {activeTab === 'manager' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400">Active Projects Managed</span>
              <div className="text-2xl font-bold text-white">4</div>
              <p className="text-[11px] text-slate-400">Software Engine, GTM Expansion, R&D Pentest, Financial Audit</p>
            </div>

            <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400">Team Capacity Utilization</span>
              <div className="text-2xl font-bold text-emerald-400">74%</div>
              <p className="text-[11px] text-slate-400">Optimal allocation across 8 Employees & 12 Agents</p>
            </div>

            <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400">Verification Backlog</span>
              <div className="text-2xl font-bold text-slate-200">0</div>
              <p className="text-[11px] text-emerald-400">100% Verified Task Proofs</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Employee & Agent View */}
      {activeTab === 'employee' && (
        <div className="space-y-4">
          <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Role-Based Execution & Agent Runtime Isolation
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Active Agents</span>
                <div className="text-xl font-bold text-white">12 Agents</div>
                <span className="text-[10px] text-slate-500">Bound to specific employee roles</span>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Prompt Guard Security</span>
                <div className="text-xl font-bold text-emerald-400">ACTIVE_GUARDED</div>
                <span className="text-[10px] text-slate-500">Adversarial injection filter enabled</span>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Secret Redaction</span>
                <div className="text-xl font-bold text-emerald-400">ACTIVE_FILTERED</div>
                <span className="text-[10px] text-slate-500">API keys & credentials masked</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Canonical Workflows & Readiness */}
      {activeTab === 'workflows' && (
        <div className="space-y-4">
          <div className="bg-slate-900/70 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Workflow className="w-4 h-4 text-indigo-400" />
                Active Canonical Operating Workflows
              </h2>
              <span className="text-xs text-slate-400">Total Workflows: {workflows.length}</span>
            </div>

            <div className="divide-y divide-slate-800">
              {workflows.map((wf) => (
                <div key={wf.workflow_id} className="p-4 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-200">{wf.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                        {wf.category}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">Step: <span className="text-indigo-400 font-mono">{wf.current_step}</span></div>
                  </div>

                  <span
                    className={`px-3 py-1 text-xs font-bold rounded-full border ${
                      wf.state === 'COMPLETED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : wf.state === 'RUNNING' || wf.state === 'VERIFYING'
                        ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {wf.state}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
