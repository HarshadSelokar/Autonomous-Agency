import React, { useState, useEffect } from 'react';
import {
  Rocket,
  Lightbulb,
  TrendingUp,
  ShieldCheck,
  Building,
  CheckCircle2,
  AlertTriangle,
  Play,
  FileText,
  DollarSign,
  Users,
  Layers,
  Sparkles,
  Search,
} from 'lucide-react';

interface VentureCreationDashboardProps {
  companyId: string;
}

export const VentureCreationDashboard: React.FC<VentureCreationDashboardProps> = ({ companyId }) => {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'proposals' | 'governance' | 'portfolio'>('pipeline');
  const [loading, setLoading] = useState<boolean>(false);

  // Mock initial state data
  const [opportunities, setOpportunities] = useState<any[]>([
    {
      id: 'opp-001',
      title: 'Autonomous Supply Chain Routing Engine',
      source: 'RESEARCH_SIGNAL',
      confidence: 0.88,
      status: 'VALIDATED',
      problem: 'Enterprise logistics providers lose $4.2B annually to manual rerouting delays.',
      customer_need: 'Sub-second real-time adaptive AI dispatch.',
    },
    {
      id: 'opp-002',
      title: 'Automated Financial Audit & Compliance AI',
      source: 'BUSINESS_OPERATIONS',
      confidence: 0.65,
      status: 'ANALYZING',
      problem: 'Regulatory compliance checks take 45 days per quarter.',
      customer_need: 'Continuous real-time ledger audit and verification.',
    },
  ]);

  const [proposals, setProposals] = useState<any[]>([
    {
      id: 'prop-101',
      opportunity_id: 'opp-001',
      title: 'PortPulse AI Inc. (New Venture)',
      venture_type: 'NEW_COMPANY',
      required_budget_usd: 15000000,
      required_workforce_count: 4,
      risk_level: 'MEDIUM',
      status: 'GOVERNANCE_PENDING',
      governance_approval_id: null,
      expected_roi: 0.42,
    },
    {
      id: 'prop-102',
      opportunity_id: 'opp-002',
      title: 'LedgerGuard BU (Internal Business Unit)',
      venture_type: 'NEW_BUSINESS_UNIT',
      required_budget_usd: 8000000,
      required_workforce_count: 2,
      risk_level: 'LOW',
      status: 'APPROVED',
      governance_approval_id: 'gov-appr-ledger-909',
      expected_roi: 0.35,
    },
  ]);

  const [approvalInput, setApprovalInput] = useState<string>('gov-appr-venture-2026-pass');

  const handleAttachApproval = (proposalId: string) => {
    if (!approvalInput) return;
    setProposals((prev) =>
      prev.map((p) =>
        p.id === proposalId
          ? { ...p, governance_approval_id: approvalInput, status: 'APPROVED' }
          : p
      )
    );
  };

  return (
    <div className="flex-1 bg-[#090d16] text-white p-6 overflow-y-auto select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
            <Rocket className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Autonomous Innovation & New Venture Creation</h1>
            <p className="text-xs text-gray-400">
              Phase 28 — Discovers market signals, designs business models, simulates scenarios & initializes governed ventures.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-semibold">
            Governance Boundary Active
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-white/10 pb-2">
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'pipeline'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Lightbulb className="w-4 h-4" />
          Innovation & Opportunities ({opportunities.length})
        </button>
        <button
          onClick={() => setActiveTab('proposals')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'proposals'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <FileText className="w-4 h-4" />
          Business Cases & Proposals ({proposals.length})
        </button>
        <button
          onClick={() => setActiveTab('governance')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'governance'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Governance & Venture Initialization
        </button>
        <button
          onClick={() => setActiveTab('portfolio')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'portfolio'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Building className="w-4 h-4" />
          Venture Portfolio & Health
        </button>
      </div>

      {/* Tab 1: Innovation & Opportunities */}
      {activeTab === 'pipeline' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((opp) => (
              <div
                key={opp.id}
                className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-5 hover:border-indigo-500/40 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md text-[10px] font-bold uppercase">
                    {opp.source}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">
                    Confidence: {(opp.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mb-1">{opp.title}</h3>
                <p className="text-xs text-gray-400 mb-3">{opp.problem}</p>
                <div className="p-3 bg-black/30 rounded-xl border border-white/5 mb-4 text-xs text-gray-300">
                  <span className="font-semibold text-indigo-300">Customer Need: </span>
                  {opp.customer_need}
                </div>
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[11px] font-medium rounded-md">
                    {opp.status}
                  </span>
                  <button className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/20 border border-indigo-500/30 hover:bg-indigo-600/40 text-indigo-300 text-xs font-semibold rounded-lg transition-all">
                    <Sparkles className="w-3.5 h-3.5" />
                    Formulate Idea & Business Case
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Proposals & Business Cases */}
      {activeTab === 'proposals' && (
        <div className="space-y-4">
          {proposals.map((prop) => (
            <div
              key={prop.id}
              className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[10px] font-bold rounded-md">
                    {prop.venture_type}
                  </span>
                  <span className="text-xs text-gray-400">ID: {prop.id}</span>
                </div>
                <h3 className="text-base font-bold text-white">{prop.title}</h3>
                <p className="text-xs text-gray-400">
                  Budget: <span className="text-emerald-400 font-semibold">${(prop.required_budget_usd / 100).toLocaleString()}</span> | 
                  Workforce: <span className="text-indigo-400 font-semibold">{prop.required_workforce_count} Agents</span> | 
                  Expected ROI: <span className="text-emerald-400 font-semibold">{(prop.expected_roi * 100).toFixed(0)}%</span>
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[11px] block text-gray-400">Governance Status</span>
                  <span
                    className={`text-xs font-bold ${
                      prop.governance_approval_id ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    {prop.governance_approval_id ? 'APPROVED BY GOVERNOR' : 'GOVERNANCE PENDING'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Governance & Initialization */}
      {activeTab === 'governance' && (
        <div className="space-y-6">
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-200">
              <strong className="block font-bold mb-0.5 text-amber-300">Governance Safety Requirement</strong>
              No venture proposal may initialize a new company or allocate capital without a valid Human Governance Approval ID. Direct execution attempts without approval will raise a 403 Forbidden exception.
            </div>
          </div>

          <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Human Governance Authorization Bridge
            </h3>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={approvalInput}
                onChange={(e) => setApprovalInput(e.target.value)}
                placeholder="Enter Governance Approval ID..."
                className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => handleAttachApproval('prop-101')}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-emerald-600/30 transition-all"
              >
                Attach Approval & Authorize
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Portfolio */}
      {activeTab === 'portfolio' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-5 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <Building className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs text-gray-400">Active Ventures</span>
              <h4 className="text-xl font-bold text-white">2 Active</h4>
            </div>
          </div>

          <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-5 flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <DollarSign className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs text-gray-400">Allocated Budget</span>
              <h4 className="text-xl font-bold text-emerald-400">$230,000</h4>
            </div>
          </div>

          <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-5 flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-xl">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs text-gray-400">Avg Venture ROI</span>
              <h4 className="text-xl font-bold text-white">+38.5%</h4>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
