import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  Sliders,
  CheckCircle,
  HelpCircle,
  BarChart3,
  Layers,
  Sparkles,
  Lock,
  ArrowRight,
  RefreshCw,
  GitBranch,
  BookOpen,
} from 'lucide-react';

interface CompanyIntelligenceDashboardProps {
  companyId?: string;
}

export const CompanyIntelligenceDashboard: React.FC<CompanyIntelligenceDashboardProps> = ({ companyId = 'comp-main-01' }) => {
  const [activeTab, setActiveTab] = useState<'health' | 'bottlenecks' | 'evaluator' | 'outcomes'>('health');
  const [selectedQuestion, setSelectedQuestion] = useState('Should we expand Engineering team capacity by 25%?');
  const [governanceApprovalId, setGovernanceApprovalId] = useState('gov-appr-888');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<string | null>(null);

  const [healthAssessment] = useState({
    overall_health_status: 'BALANCED',
    dimension_scores: {
      strategic: 0.88,
      financial: 0.90,
      product: 0.85,
      customer: 0.82,
      gtm: 0.78,
      workforce: 0.72,
      engineering: 0.75,
      operations: 0.85,
      reliability: 0.95,
      governance: 0.98,
    },
    top_risks: ['Workforce burnout in Engineering', 'Sales cycle slowdown in Mid-Market'],
    top_opportunities: ['Automated QA Pipeline Integration', 'Tiered Enterprise Pricing Adjustment'],
  });

  const [bottlenecks] = useState([
    {
      id: 'bn-101',
      name: 'Engineering Capacity Shortage',
      scope: 'SOFTWARE_DEVELOPMENT',
      severity: 'HIGH',
      evidence: 'Overdue task backlog expanded by +35% in last sprint.',
      suspected_causes: ['Insufficient Senior Frontend Engineering capacity', 'Task dependency bottlenecks'],
    },
    {
      id: 'bn-102',
      name: 'CRM Sales Cycle Friction',
      scope: 'GTM_SALES',
      severity: 'MEDIUM',
      evidence: 'Deal velocity delayed by +14 days during proposal approval phase.',
      suspected_causes: ['Commercial proposal discount approval delay'],
    },
  ]);

  const [decisionOptions] = useState([
    {
      id: 'opt-0',
      name: 'Option 0: No Action (Maintain Status Quo)',
      is_baseline: true,
      score: 0.48,
      cost: '$0',
      benefit: 'Zero financial expenditure',
      risk: 'Backlog expansion & release delays',
    },
    {
      id: 'opt-1',
      name: 'Option 1: Add 5 Senior Engineers (+25% Capacity)',
      is_baseline: false,
      score: 0.84,
      cost: '$50,000 / mo',
      benefit: 'Accelerates release velocity by +35%',
      risk: 'Increases monthly operational burn',
    },
    {
      id: 'opt-2',
      name: 'Option 2: Reallocate 3 Internal Workforce Engineers',
      is_baseline: false,
      score: 0.72,
      cost: '$10,000 / mo',
      benefit: 'Moderate throughput increase (+15%)',
      risk: 'Temporarily pauses secondary R&D projects',
    },
  ]);

  const handleExecuteInsight = () => {
    if (!governanceApprovalId) return;
    setIsExecuting(true);
    setTimeout(() => {
      setExecutionResult(`Governed Execution Initiated! Approval ID: ${governanceApprovalId}. Workflow bridged to Task Engine.`);
      setIsExecuting(false);
    }, 1000);
  };

  return (
    <div className="flex-1 bg-[#090d16] p-6 text-gray-100 overflow-y-auto space-y-6">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-indigo-300 to-pink-400 bg-clip-text text-transparent flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-400" />
            Company Decision Support & Strategic Intelligence Engine
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Structured decision questions, multi-dimensional option evaluations, trade-off analysis, and human governance execution bridge.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/40 px-3 py-1.5 rounded-xl text-xs font-semibold text-purple-300">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <span>GOVERNANCE BOUNDARY ACTIVE — RECOMMENDATIONS REQUIRE APPROVAL</span>
        </div>
      </div>

      {/* Nav Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2 text-xs">
        <button
          onClick={() => setActiveTab('health')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all ${
            activeTab === 'health'
              ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" /> Company Health & Risks
        </button>
        <button
          onClick={() => setActiveTab('bottlenecks')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all ${
            activeTab === 'bottlenecks'
              ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <AlertTriangle className="w-4 h-4" /> Bottlenecks & Opportunities
        </button>
        <button
          onClick={() => setActiveTab('evaluator')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all ${
            activeTab === 'evaluator'
              ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Sliders className="w-4 h-4" /> Decision Options Evaluator
        </button>
        <button
          onClick={() => setActiveTab('outcomes')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all ${
            activeTab === 'outcomes'
              ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <BookOpen className="w-4 h-4" /> Decision Outcome Feedback
        </button>
      </div>

      {/* Tab 1: Company Health & Risks */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" /> Multi-Dimensional Health Matrix
              </h2>
              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-full font-bold border border-emerald-500/40">
                OVERALL STATUS: {healthAssessment.overall_health_status}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(healthAssessment.dimension_scores).map(([dim, score]) => (
                <div key={dim} className="bg-white/5 border border-white/5 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-bold">{dim}</span>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-purple-300">{(score * 100).toFixed(0)}%</span>
                    <div className="w-12 bg-white/10 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-purple-400 h-full" style={{ width: `${score * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[#0f172a]/70 border border-rose-500/30 rounded-2xl p-5 space-y-3 shadow-xl">
              <h3 className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" /> Emerging Operational Risks
              </h3>
              <ul className="space-y-2 text-xs text-gray-300">
                {healthAssessment.top_risks.map((risk, idx) => (
                  <li key={idx} className="flex items-center gap-2 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-[#0f172a]/70 border border-emerald-500/30 rounded-2xl p-5 space-y-3 shadow-xl">
              <h3 className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" /> Identified Strategic Opportunities
              </h3>
              <ul className="space-y-2 text-xs text-gray-300">
                {healthAssessment.top_opportunities.map((opp, idx) => (
                  <li key={idx} className="flex items-center gap-2 bg-emerald-500/10 p-2.5 rounded-lg border border-emerald-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{opp}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Bottlenecks Stream */}
      {activeTab === 'bottlenecks' && (
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Detected Operational Bottlenecks
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {bottlenecks.map((bn) => (
              <div key={bn.id} className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-5 space-y-3 shadow-xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                  <div>
                    <h3 className="text-sm font-bold text-white">{bn.name}</h3>
                    <span className="text-[10px] text-gray-400 font-mono">{bn.scope}</span>
                  </div>
                  <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] px-2.5 py-0.5 rounded font-bold uppercase">
                    {bn.severity}
                  </span>
                </div>
                <p className="text-xs text-gray-300">{bn.evidence}</p>
                <div className="bg-white/5 p-2.5 rounded-xl text-[11px] text-gray-400 space-y-1">
                  <span className="font-bold text-gray-300 block">Suspected Root Causes:</span>
                  {bn.suspected_causes.map((cause, idx) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      <ArrowRight className="w-3 h-3 text-indigo-400" />
                      <span>{cause}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Decision Options Evaluator */}
      {activeTab === 'evaluator' && (
        <div className="space-y-6">
          <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-purple-400" /> Active Decision Question
              </h2>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2.5 py-1 rounded-full font-mono">
                URGENCY: HIGH
              </span>
            </div>
            <p className="text-base font-bold text-white bg-white/5 p-3 rounded-xl border border-white/10">
              "{selectedQuestion}"
            </p>
          </div>

          {/* Options Comparison Table */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {decisionOptions.map((opt) => (
              <div
                key={opt.id}
                className={`bg-[#0f172a]/80 border rounded-2xl p-5 space-y-4 shadow-xl flex flex-col justify-between transition-all ${
                  opt.score > 0.8
                    ? 'border-indigo-500/60 ring-1 ring-indigo-500/30'
                    : 'border-white/10'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <h3 className="text-xs font-bold text-white">{opt.name}</h3>
                    {opt.is_baseline && (
                      <span className="text-[9px] bg-gray-500/20 text-gray-300 px-1.5 py-0.5 rounded font-mono">
                        BASELINE
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Evaluation Score</span>
                    <span className="text-base font-bold text-purple-300">{(opt.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between text-gray-400">
                      <span>Est Cost:</span>
                      <span className="text-gray-200 font-semibold">{opt.cost}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Benefit:</span>
                      <span className="text-emerald-400 font-semibold">{opt.benefit}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Risk Factor:</span>
                      <span className="text-rose-400 font-semibold">{opt.risk}</span>
                    </div>
                  </div>
                </div>

                {opt.score > 0.8 && (
                  <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 p-1.5 rounded-lg text-center font-bold">
                    RECOMMENDED OPTION
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Governance Execution Bridge Panel */}
          <div className="bg-[#0f172a]/90 border border-purple-500/40 rounded-2xl p-5 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-purple-300 uppercase tracking-wider flex items-center gap-2">
              <Lock className="w-4 h-4 text-purple-400" /> Human Governance Approval Bridge
            </h3>
            <p className="text-xs text-gray-300">
              Recommendations CANNOT execute directly. Enter a valid Human Governance Approval ID to authorize execution.
            </p>

            <div className="flex items-center gap-3">
              <input
                type="text"
                value={governanceApprovalId}
                onChange={(e) => setGovernanceApprovalId(e.target.value)}
                placeholder="Enter Governance Approval ID..."
                className="bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-purple-500 w-72 font-mono"
              />
              <button
                onClick={handleExecuteInsight}
                disabled={isExecuting || !governanceApprovalId}
                className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold px-5 py-2 rounded-xl transition-all shadow-lg cursor-pointer"
              >
                {isExecuting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Executing Bridge...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" /> Authorize & Execute Recommendation
                  </>
                )}
              </button>
            </div>

            {executionResult && (
              <div className="bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl text-xs text-emerald-300 font-medium">
                {executionResult}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Decision Outcome Feedback */}
      {activeTab === 'outcomes' && (
        <div className="bg-[#0f172a]/70 border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
          <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-400" /> Post-Execution Outcome Feedback Loop
          </h2>

          <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3 text-xs">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="font-bold text-white">Historical Decision: Q3 Engineering Expansion</span>
              <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-bold text-[10px]">
                OUTCOME: SUCCESS (+8.0% ARR Variance)
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-gray-400 block text-[10px]">Expected Outcome</span>
                <span className="font-semibold text-gray-200">$100,000.00 ARR / mo</span>
              </div>
              <div>
                <span className="text-gray-400 block text-[10px]">Actual Observed Outcome</span>
                <span className="font-semibold text-emerald-300">$108,000.00 ARR / mo</span>
              </div>
            </div>
            <p className="text-gray-300 bg-black/30 p-2.5 rounded-lg border border-white/5 font-sans">
              Validated Learning: Adding 5 senior frontend engineers successfully cleared task backlog and accelerated feature delivery by 35%. Learning candidate persisted to Phase 18 Institutional Knowledge repository.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
