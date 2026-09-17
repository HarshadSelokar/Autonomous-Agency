import React, { useState } from 'react';
import {
  Building2,
  GitMerge,
  Network,
  Target,
  ShieldCheck,
  Activity,
  AlertTriangle,
  TrendingUp,
  Layers,
  Cpu,
  Lock,
  Zap,
  CheckCircle2,
  Users,
  Briefcase,
  HelpCircle,
} from 'lucide-react';

export const EnterpriseDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'topology' | 'strategy' | 'governance' | 'health'>('topology');

  // Simulated live data state
  const [nodes, setNodes] = useState([
    { id: 'node-ent', name: 'Apex Global Enterprise', type: 'ENTERPRISE', region: 'GLOBAL', classification: 'RESTRICTED' },
    { id: 'node-comp-a', name: 'CyberGuard Security Systems', type: 'COMPANY', region: 'NORTH_AMERICA', classification: 'CONFIDENTIAL' },
    { id: 'node-comp-b', name: 'CloudScale Infrastructure', type: 'COMPANY', region: 'EUROPE', classification: 'CONFIDENTIAL' },
    { id: 'node-shared-fin', name: 'Central Finance Shared Service', type: 'SHARED_SERVICE', region: 'GLOBAL', classification: 'INTERNAL' },
  ]);

  const [companyIdInput, setCompanyIdInput] = useState('');
  const [companyNameInput, setCompanyNameInput] = useState('');

  const [objectives] = useState([
    { id: 'eobj-001', title: 'Achieve $100M ARR Across Portfolio', metric: 'ARR_USD', target: 100000000, current: 42500000, scope: 'ENTERPRISE' },
    { id: 'eobj-002', title: 'Maintain 99.99% Global Infrastructure Uptime', metric: 'UPTIME_PCT', target: 99.99, current: 99.95, scope: 'SHARED_SERVICE' },
  ]);

  const [policySpend, setPolicySpend] = useState(50000);
  const [simulatedNodeSpend, setSimulatedNodeSpend] = useState(75000);

  const [interCompanyReqs, setInterCompanyReqs] = useState([
    { id: 'icreq-101', source: 'CyberGuard Security Systems', dest: 'CloudScale Infrastructure', capability: 'HIGH_PERFORMANCE_GPU_CLUSTER', status: 'PENDING', approval: 'gov-appr-9821' },
  ]);

  const handleAttachCompany = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyNameInput) return;
    const newNode = {
      id: `node-${Date.now()}`,
      name: companyNameInput,
      type: 'COMPANY',
      region: 'NORTH_AMERICA',
      classification: 'CONFIDENTIAL',
    };
    setNodes([...nodes, newNode]);
    setCompanyNameInput('');
    setCompanyIdInput('');
  };

  const handleAuthorizeRequest = (id: string) => {
    setInterCompanyReqs(
      interCompanyReqs.map((r) => (r.id === id ? { ...r, status: 'AUTHORIZED' } : r))
    );
  };


  // Effective policy math simulation: Child spend cannot exceed Root enterprise spend ($50,000)
  const effectiveMaxSpend = Math.min(policySpend, simulatedNodeSpend);

  return (
    <div className="p-6 bg-slate-950 text-slate-100 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Building2 className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Enterprise OS & Multi-Company Federation
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Phase 29 Active
                </span>
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Enterprise Organizational Topology, Strategy Cascading, Shared Services & Governed Inter-Company Federation
              </p>
            </div>
          </div>
        </div>

        {/* Global Key Statistics */}
        <div className="flex items-center gap-4 text-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-right">
            <span className="text-slate-400 block text-xs">Total Enterprise Entities</span>
            <span className="text-lg font-bold text-indigo-400">{nodes.length} Nodes</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-right">
            <span className="text-slate-400 block text-xs">Enterprise Health</span>
            <span className="text-lg font-bold text-emerald-400">93.8% Overall</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800 mb-6 gap-2">
        <button
          onClick={() => setActiveTab('topology')}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'topology'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Network className="w-4 h-4" />
          Topology & Federation
        </button>
        <button
          onClick={() => setActiveTab('strategy')}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'strategy'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Target className="w-4 h-4" />
          Strategy & Objectives
        </button>
        <button
          onClick={() => setActiveTab('governance')}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'governance'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Governance & Authority
        </button>
        <button
          onClick={() => setActiveTab('health')}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'health'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          Health, Risk & Intelligence
        </button>
      </div>

      {/* Tab 1: Topology & Federation */}
      {activeTab === 'topology' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Organization Tree */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Network className="w-5 h-5 text-indigo-400" />
              Enterprise Organizational Hierarchy Graph
            </h2>
            <div className="space-y-3">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  className="flex items-center justify-between p-4 bg-slate-950 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {node.type === 'ENTERPRISE' && <Building2 className="w-5 h-5 text-indigo-400" />}
                    {node.type === 'COMPANY' && <Briefcase className="w-5 h-5 text-cyan-400" />}
                    {node.type === 'SHARED_SERVICE' && <Cpu className="w-5 h-5 text-emerald-400" />}
                    <div>
                      <span className="font-medium text-white block">{node.name}</span>
                      <span className="text-xs text-slate-500">ID: {node.id} | Region: {node.region}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-slate-800 text-slate-300">
                      {node.type}
                    </span>
                    <span className="px-2 py-1 rounded text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {node.classification}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Company Attachment Manager */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <GitMerge className="w-5 h-5 text-emerald-400" />
              Attach Subsidiary / Company
            </h2>
            <form onSubmit={handleAttachCompany} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Company Name</label>
                <input
                  type="text"
                  placeholder="e.g. CyberGuard Swarm Systems"
                  value={companyNameInput}
                  onChange={(e) => setCompanyNameInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Company Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. comp-cyber-001"
                  value={companyIdInput}
                  onChange={(e) => setCompanyIdInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
              >
                <GitMerge className="w-4 h-4" />
                Attach Company to Enterprise Topology
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Tab 2: Strategy & Objectives */}
      {activeTab === 'strategy' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Enterprise Strategic Cascading */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-400" />
              Strategic Objective Cascading
            </h2>
            <div className="space-y-4">
              {objectives.map((obj) => (
                <div key={obj.id} className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-sm">{obj.title}</span>
                    <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/20 text-indigo-300 font-mono">
                      {obj.scope}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-2">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, (obj.current / obj.target) * 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Progress: {((obj.current / obj.target) * 100).toFixed(1)}%</span>
                    <span>Target: {obj.target.toLocaleString()} {obj.metric}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Enterprise Resource Capacity Allocation Heatmap */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-400" />
              Shared Capacity Allocation & Heatmap
            </h2>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-4">
              <div>
                <div className="flex justify-between text-sm font-medium text-white mb-1">
                  <span>GPU Compute Swarm Cluster</span>
                  <span className="text-emerald-400">45% Allocated</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full w-5/12" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm font-medium text-white mb-1">
                  <span>Central AI Security Review Engine</span>
                  <span className="text-indigo-400">70% Allocated</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-indigo-500 h-full w-7/12" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Governance & Authority */}
      {activeTab === 'governance' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Policy Resolver Simulator */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              Deterministic Policy Resolution Engine (`resolve_effective_policy`)
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Rule: Child node policy can NEVER weaken mandatory root Enterprise safety or spend caps.
            </p>
            <div className="space-y-4 bg-slate-950 p-4 border border-slate-800 rounded-lg">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Root Enterprise Max Spend Cap ($)</label>
                <input
                  type="number"
                  value={policySpend}
                  onChange={(e) => setPolicySpend(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Subsidiary Requested Spend Cap ($)</label>
                <input
                  type="number"
                  value={simulatedNodeSpend}
                  onChange={(e) => setSimulatedNodeSpend(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <div className="p-3 bg-indigo-950/40 border border-indigo-800/50 rounded-lg">
                <span className="text-xs text-indigo-300 block font-semibold mb-1">Effective Resolved Policy Cap:</span>
                <span className="text-xl font-bold text-white">${effectiveMaxSpend.toLocaleString()} USD</span>
                <span className="text-xs text-slate-400 block mt-1">
                  {simulatedNodeSpend > policySpend ? '⚠️ Child request capped by Root Enterprise limit.' : '✅ Child limit compliant with Root limit.'}
                </span>
              </div>
            </div>
          </div>

          {/* Inter-Company Requests Monitor */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-emerald-400" />
              Inter-Company Governed Requests
            </h2>
            <div className="space-y-3">
              {interCompanyReqs.map((req) => (
                <div key={req.id} className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-white text-sm">{req.capability}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-mono ${
                        req.status === 'AUTHORIZED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {req.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mb-3">
                    From: {req.source} → To: {req.dest}
                  </p>
                  {req.status === 'PENDING' && (
                    <button
                      onClick={() => handleAuthorizeRequest(req.id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-colors"
                    >
                      Grant Governance Authorization
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Health, Risk & Intelligence */}
      {activeTab === 'health' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Health Scorecards */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 lg:col-span-2">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-400" />
              Multi-Dimensional Enterprise Health Gauges
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Objectives Health</span>
                <span className="text-2xl font-bold text-indigo-400">95.0%</span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Workforce Capacity</span>
                <span className="text-2xl font-bold text-emerald-400">90.0%</span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Financial Health</span>
                <span className="text-2xl font-bold text-cyan-400">95.0%</span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Infrastructure SLA</span>
                <span className="text-2xl font-bold text-emerald-400">99.0%</span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Governance Compliance</span>
                <span className="text-2xl font-bold text-purple-400">100.0%</span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-center">
                <span className="text-xs text-slate-400 block mb-1">Overall Composite</span>
                <span className="text-2xl font-bold text-emerald-300">93.8%</span>
              </div>
            </div>
          </div>

          {/* Enterprise Risk Register */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Enterprise Risk Register
            </h2>
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
              <div className="flex justify-between items-center text-sm font-semibold text-white">
                <span>Inter-company GPU Contention</span>
                <span className="text-xs text-amber-400 font-mono">Prob: 0.25</span>
              </div>
              <p className="text-xs text-slate-400">Potential Impact: $500,000 USD</p>
              <div className="text-xs text-emerald-400 pt-2 border-t border-slate-800">
                Mitigation: Capacity pool expansion queued.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
