import React, { useState } from 'react';
import {
  GraduationCap,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Sliders,
  RefreshCw,
  Layers,
  ShieldCheck,
  Zap,
  RotateCcw,
  BookOpen,
  ArrowRight,
  BarChart3,
  FlaskConical,
} from 'lucide-react';

interface Props {
  companyId?: string;
}

export const LearningAdaptationDashboard: React.FC<Props> = ({ companyId = 'comp-main-01' }) => {
  const [activeTab, setActiveTab] = useState<'cycles' | 'lessons' | 'proposals' | 'experiments'>('cycles');
  const [governanceApprovalId, setGovernanceApprovalId] = useState('gov-appr-learning-999');
  const [isDispatching, setIsDispatching] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const [learningCycles] = useState([
    {
      id: 'cycle-101',
      purpose: 'Q3 Operational Efficiency & Task Latency Audit',
      scope: 'COMPANY',
      status: 'PATTERN_DETECTION',
      observations_count: 14,
      patterns_count: 2,
      created_at: '2026-09-17 14:00',
    },
    {
      id: 'cycle-102',
      purpose: 'Customer Support SLA & Resolution Variance Study',
      scope: 'DEPARTMENT',
      status: 'COMPLETED',
      observations_count: 28,
      patterns_count: 4,
      created_at: '2026-09-16 11:30',
    },
  ]);

  const [observations] = useState([
    {
      id: 'obs-01',
      source: 'TASK_ENGINE',
      entity: 'task-backlog-queue',
      observed: 'Queue delay 14.5 mins',
      expected: 'Queue delay < 5.0 mins',
      variance: '+190.0% variance',
    },
    {
      id: 'obs-02',
      source: 'MODEL_ROUTER',
      entity: 'model-groq-llama-3',
      observed: 'Latency 340ms',
      expected: 'Latency 200ms',
      variance: '+70.0% variance',
    },
  ]);

  const [patterns] = useState([
    {
      id: 'pat-01',
      name: 'High Dependency Rework in Backend Engineering',
      type: 'RECURRING_FAILURE',
      frequency: 6,
      confidence: 0.88,
      scope: 'ENGINEERING',
    },
    {
      id: 'pat-02',
      name: 'Parallel Static Check CI Throughput Acceleration',
      type: 'RECURRING_SUCCESS',
      frequency: 12,
      confidence: 0.94,
      scope: 'COMPANY',
    },
  ]);

  const [lessons] = useState([
    {
      id: 'les-01',
      statement: 'Task execution latency increases by +35% when queue depth exceeds 5 items.',
      scope: 'COMPANY',
      confidence: 0.92,
      status: 'VALIDATED',
    },
    {
      id: 'les-02',
      statement: 'Automated pre-flight schema dry-runs reduce DB migration rollback rate to 0%.',
      scope: 'ENGINEERING',
      confidence: 0.95,
      status: 'VALIDATED',
    },
  ]);

  const [proposals] = useState([
    {
      id: 'prop-101',
      title: 'Automate Pre-flight Migration Checks',
      type: 'VERIFICATION_RULE_CHANGE',
      risk_level: 'MEDIUM',
      rationale: 'Add automated schema dry-run verification rule to prevent pipeline blockages.',
      status: 'PROPOSED',
      governance_required: true,
    },
    {
      id: 'prop-102',
      title: 'Increase Queue Worker Concurrency for Task Engine',
      type: 'WORKFLOW_CHANGE',
      risk_level: 'LOW',
      rationale: 'Expand parallel queue processing worker threads from 4 to 8.',
      status: 'APPROVED',
      governance_required: true,
    },
  ]);

  const [experiments] = useState([
    {
      id: 'exp-01',
      proposal_id: 'prop-102',
      target_subsystem: 'TASK_ENGINE',
      execution_type: 'CONTROLLED_EXPERIMENT',
      governance_approval_id: 'gov-appr-learning-999',
      status: 'EXPERIMENTING',
      expected_metrics: 'Latency < 400ms',
      actual_metrics: 'Latency = 380ms',
      has_regression: false,
    },
  ]);

  const handleDispatchExperiment = () => {
    if (!governanceApprovalId) return;
    setIsDispatching(true);
    setTimeout(() => {
      setActionMessage(`Governed Experiment Dispatched! Governance Approval ID: ${governanceApprovalId}. Subsystem: TASK_ENGINE.`);
      setIsDispatching(false);
    }, 800);
  };

  const handleRollback = () => {
    setIsDispatching(true);
    setTimeout(() => {
      setActionMessage(`Safety Rollback Triggered! Reverted proposal 'prop-102' state cleanly.`);
      setIsDispatching(false);
    }, 800);
  };

  return (
    <div className="flex-1 bg-[#090d16] text-gray-100 flex flex-col overflow-hidden">
      {/* Top Header */}
      <header className="px-8 py-5 border-b border-white/10 bg-[#0f172a]/40 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide">Continuous Organizational Learning</h1>
            <p className="text-xs text-gray-400">
              Governed Adaptation, Outcome Measurement & Institutional Self-Improvement Loop
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-1.5 font-mono">
            <ShieldCheck className="w-3.5 h-3.5" /> Governance Boundary Enforced
          </span>
          <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono">
            Tenant: {companyId}
          </span>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="px-8 py-3 border-b border-white/5 bg-black/20 flex gap-4">
        {[
          { id: 'cycles', label: '1. Learning Cycles & Observations', icon: Layers },
          { id: 'lessons', label: '2. Patterns & Validated Lessons', icon: BookOpen },
          { id: 'proposals', label: '3. Improvement Proposals', icon: Sliders },
          { id: 'experiments', label: '4. Controlled Experiments & Rollbacks', icon: FlaskConical },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Action Notification Banner */}
      {actionMessage && (
        <div className="mx-8 mt-4 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* TAB 1: CYCLES & OBSERVATIONS */}
        {activeTab === 'cycles' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Active Learning Cycles */}
              <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" /> Active Learning Cycles
                </h2>
                <div className="space-y-3">
                  {learningCycles.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-2 hover:border-indigo-500/30 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-300 font-mono">{c.id}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono uppercase">
                          {c.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-200 font-medium">{c.purpose}</p>
                      <div className="flex items-center justify-between text-[11px] text-gray-400 pt-1">
                        <span>Observations: {c.observations_count}</span>
                        <span>Patterns: {c.patterns_count}</span>
                        <span>Scope: {c.scope}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ingested Operational Observations */}
              <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-amber-400" /> Ingested Variance & Telemetry
                </h2>
                <div className="space-y-3">
                  {observations.map((o) => (
                    <div key={o.id} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-gray-300">{o.source} — {o.entity}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold">
                          {o.variance}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400">
                        Observed: <span className="text-gray-200">{o.observed}</span> | Expected:{' '}
                        <span className="text-gray-200">{o.expected}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LESSONS & PATTERNS */}
        {activeTab === 'lessons' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Detected Patterns */}
              <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" /> Detected Operational Patterns
                </h2>
                <div className="space-y-3">
                  {patterns.map((p) => (
                    <div key={p.id} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{p.name}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                            p.type === 'RECURRING_FAILURE'
                              ? 'bg-rose-500/20 text-rose-300'
                              : 'bg-emerald-500/20 text-emerald-300'
                          }`}
                        >
                          {p.type}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>Frequency: {p.frequency} occurrences</span>
                        <span>Confidence: {(p.confidence * 100).toFixed(0)}%</span>
                        <span>Scope: {p.scope}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Validated Lessons */}
              <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" /> Validated Institutional Lessons
                </h2>
                <div className="space-y-3">
                  {lessons.map((l) => (
                    <div key={l.id} className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono text-indigo-400">{l.id}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                          {l.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-200 font-medium leading-relaxed">"{l.statement}"</p>
                      <div className="text-[11px] text-gray-400 flex justify-between pt-1">
                        <span>Confidence Score: {(l.confidence * 100).toFixed(0)}%</span>
                        <span>Scope: {l.scope}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: PROPOSALS */}
        {activeTab === 'proposals' && (
          <div className="space-y-6">
            <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" /> Adaptation Proposals & Governance Queue
              </h2>
              <div className="space-y-4">
                {proposals.map((p) => (
                  <div key={p.id} className="p-5 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-indigo-300 font-mono">{p.id}</span>
                        <h3 className="text-xs font-bold text-white">{p.title}</h3>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                          Risk: {p.risk_level}
                        </span>
                        <span className="text-[10px] px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono font-bold">
                          {p.status}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-300 leading-relaxed">{p.rationale}</p>

                    <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <span>Governance Required: Yes</span>
                      </div>
                      {p.status === 'PROPOSED' && (
                        <button
                          onClick={handleDispatchExperiment}
                          disabled={isDispatching}
                          className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-md"
                        >
                          <Zap className="w-3.5 h-3.5" /> Approve & Dispatch Experiment
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: EXPERIMENTS & ROLLBACKS */}
        {activeTab === 'experiments' && (
          <div className="space-y-6">
            <div className="bg-[#0f172a]/60 border border-white/10 rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-emerald-400" /> Governed Controlled Experiments
              </h2>
              <div className="space-y-4">
                {experiments.map((e) => (
                  <div key={e.id} className="p-5 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-emerald-300 font-mono">{e.id}</span>
                        <span className="text-xs text-gray-300">Target Subsystem: <strong className="text-white">{e.target_subsystem}</strong></span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                        {e.status}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-black/40 text-xs text-gray-300 font-mono flex items-center justify-between">
                      <span>Governance Approval ID: {e.governance_approval_id}</span>
                      <span>Execution Type: {e.execution_type}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                        <span className="text-gray-400 block text-[10px]">Expected Metrics:</span>
                        <span className="font-semibold text-gray-200">{e.expected_metrics}</span>
                      </div>
                      <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                        <span className="text-gray-400 block text-[10px]">Actual Measured Outcome:</span>
                        <span className="font-semibold text-emerald-400">{e.actual_metrics}</span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                      <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
                        <CheckCircle className="w-4 h-4" /> Zero Regression Detected
                      </span>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={handleRollback}
                          disabled={isDispatching}
                          className="px-4 py-1.5 rounded-xl bg-rose-600/30 hover:bg-rose-600/50 border border-rose-500/40 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
                        >
                          <RotateCcw className="w-3.5 h-3.5" /> Trigger Safety Rollback
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
