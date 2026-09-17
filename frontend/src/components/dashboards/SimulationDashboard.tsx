import React, { useState } from 'react';
import {
  Sparkles,
  Play,
  TrendingUp,
  AlertOctagon,
  ShieldCheck,
  Zap,
  Users,
  DollarSign,
  BarChart2,
  RefreshCw,
  Sliders,
  Database,
  ArrowRight,
} from 'lucide-react';

export const SimulationDashboard: React.FC = () => {
  const [snapshotName, setSnapshotName] = useState('Q3 Enterprise Baseline');
  const [headcountMultiplier, setHeadcountMultiplier] = useState(2.5);
  const [marketingBoostPct, setMarketingBoostPct] = useState(40);
  const [priceAdjustmentPct, setPriceAdjustmentPct] = useState(15);
  const [isSimulating, setIsSimulating] = useState(false);

  const [simulationResult, setSimulationResult] = useState<{
    scenario_name: string;
    baseline: { revenue_cents: number; headcount: number; monthly_burn_cents: number; runway_months: number };
    simulated: { revenue_cents: number; headcount: number; monthly_burn_cents: number; runway_months: number };
    deliberation_summary: string;
  }>({
    scenario_name: '2.5x Staffing & 40% Marketing Expansion',
    baseline: {
      revenue_cents: 2000000,
      headcount: 10,
      monthly_burn_cents: 800000,
      runway_months: 24,
    },
    simulated: {
      revenue_cents: 4200000,
      headcount: 25,
      monthly_burn_cents: 1800000,
      runway_months: 18,
    },
    deliberation_summary:
      'Simulated aggressive growth scenario: Doubling engineering and GTM capacity accelerates ARR growth by +110%, maintaining a safe 18-month runway reserve.',
  });

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setSimulationResult({
        scenario_name: `Staffing x${headcountMultiplier} + Mktg ${marketingBoostPct}% + Price ${priceAdjustmentPct}%`,
        baseline: {
          revenue_cents: 2000000,
          headcount: 10,
          monthly_burn_cents: 800000,
          runway_months: 24,
        },
        simulated: {
          revenue_cents: Math.round(2000000 * (1 + (marketingBoostPct * 0.02) + (priceAdjustmentPct * 0.01))),
          headcount: Math.round(10 * headcountMultiplier),
          monthly_burn_cents: Math.round(800000 * headcountMultiplier),
          runway_months: Math.max(6, Math.round(24 / (headcountMultiplier * 0.7))),
        },
        deliberation_summary: `Engine output evaluated for scenario: ${headcountMultiplier}x staffing multiplier with ${marketingBoostPct}% marketing boost and ${priceAdjustmentPct}% price adjustment. Zero production mutation committed.`,
      });
      setIsSimulating(false);
    }, 1000);
  };

  return (
    <div className="flex-1 bg-[#090d16] p-6 text-gray-100 overflow-y-auto space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-amber-400 via-orange-300 to-pink-400 bg-clip-text text-transparent flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-400" />
            What-If Company Simulation Sandbox Engine
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Simulate strategic organizational shifts, headcount growth, pricing changes, and market shocks without altering production state.
          </p>
        </div>

        {/* Safety Guardrail Pill */}
        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/40 px-3 py-1.5 rounded-xl text-xs font-semibold text-amber-300">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
          <span>SIMULATION MODE ACTIVE — PRODUCTION MUTATION BLOCKED</span>
        </div>
      </div>

      {/* Safety Isolation Boundaries Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0f172a]/70 border border-emerald-500/30 rounded-xl p-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Database className="w-5 h-5 text-emerald-400" />
            <div>
              <span className="text-[10px] uppercase font-bold text-gray-400">Production DB</span>
              <p className="text-xs font-semibold text-emerald-300">Read-Only Isolation</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        <div className="bg-[#0f172a]/70 border border-rose-500/30 rounded-xl p-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <DollarSign className="w-5 h-5 text-rose-400" />
            <div>
              <span className="text-[10px] uppercase font-bold text-gray-400">Payment Gateways</span>
              <p className="text-xs font-semibold text-rose-300">Real Execution Blocked</p>
            </div>
          </div>
          <AlertOctagon className="w-4 h-4 text-rose-400" />
        </div>

        <div className="bg-[#0f172a]/70 border border-amber-500/30 rounded-xl p-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Zap className="w-5 h-5 text-amber-400" />
            <div>
              <span className="text-[10px] uppercase font-bold text-gray-400">External Webhooks</span>
              <p className="text-xs font-semibold text-amber-300">Mock Sandbox Active</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
        </div>

        <div className="bg-[#0f172a]/70 border border-indigo-500/30 rounded-xl p-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <div>
              <span className="text-[10px] uppercase font-bold text-gray-400">Scenario Engine</span>
              <p className="text-xs font-semibold text-indigo-300">Deterministic Engine</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
        </div>
      </div>

      {/* Main Simulation Builder & Results Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Scenario Configuration Panel */}
        <div className="bg-[#0f172a]/80 border border-white/10 rounded-2xl p-5 space-y-5 shadow-xl">
          <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-amber-400" />
            Scenario Variable Builder
          </h2>

          <div className="space-y-4 text-xs">
            {/* Snapshot Selector */}
            <div>
              <label className="block text-gray-400 font-semibold mb-1">Baseline Snapshot</label>
              <input
                type="text"
                value={snapshotName}
                onChange={(e) => setSnapshotName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-2.5 text-white font-medium focus:outline-none focus:border-amber-500"
              />
            </div>

            {/* Slider 1: Staffing Multiplier */}
            <div className="space-y-1">
              <div className="flex justify-between text-gray-300 font-medium">
                <span>Staffing & Headcount Multiplier</span>
                <span className="text-amber-400 font-bold">{headcountMultiplier}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.1"
                value={headcountMultiplier}
                onChange={(e) => setHeadcountMultiplier(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>

            {/* Slider 2: Marketing Expansion */}
            <div className="space-y-1">
              <div className="flex justify-between text-gray-300 font-medium">
                <span>Marketing & GTM Budget Boost</span>
                <span className="text-amber-400 font-bold">+{marketingBoostPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="200"
                step="5"
                value={marketingBoostPct}
                onChange={(e) => setMarketingBoostPct(parseInt(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>

            {/* Slider 3: Price Adjustment */}
            <div className="space-y-1">
              <div className="flex justify-between text-gray-300 font-medium">
                <span>Product Price Adjustment</span>
                <span className="text-amber-400 font-bold">+{priceAdjustmentPct}%</span>
              </div>
              <input
                type="range"
                min="-50"
                max="100"
                step="5"
                value={priceAdjustmentPct}
                onChange={(e) => setPriceAdjustmentPct(parseInt(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-bold py-3 rounded-xl shadow-lg transition-all cursor-pointer"
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Executing Scenario Simulation...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run What-If Scenario</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Comparative Simulation Results Panel */}
        <div className="lg:col-span-2 bg-[#0f172a]/80 border border-white/10 rounded-2xl p-5 space-y-5 shadow-xl">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h2 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-indigo-400" />
                Simulation Outcome Projection
              </h2>
              <p className="text-xs text-amber-300 font-medium mt-0.5">{simulationResult.scenario_name}</p>
            </div>
            <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-mono border border-indigo-500/40">
              SAFE SANDBOX RUN
            </span>
          </div>

          {/* Metric Comparison Cards */}
          <div className="grid grid-cols-2 gap-4">
            {/* Metric 1: Monthly Revenue */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
              <span className="text-[11px] text-gray-400 uppercase font-bold flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Projected ARR / Monthly Revenue
              </span>
              <div className="flex items-center justify-between pt-1">
                <div>
                  <span className="text-[10px] text-gray-500 block">Baseline</span>
                  <span className="text-sm font-semibold text-gray-400">
                    ${(simulationResult.baseline.revenue_cents / 100).toLocaleString()}
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-500" />
                <div className="text-right">
                  <span className="text-[10px] text-emerald-400 block font-bold">Simulated</span>
                  <span className="text-base font-bold text-emerald-300">
                    ${(simulationResult.simulated.revenue_cents / 100).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Metric 2: Headcount */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
              <span className="text-[11px] text-gray-400 uppercase font-bold flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-indigo-400" /> Staffing Headcount
              </span>
              <div className="flex items-center justify-between pt-1">
                <div>
                  <span className="text-[10px] text-gray-500 block">Baseline</span>
                  <span className="text-sm font-semibold text-gray-400">
                    {simulationResult.baseline.headcount} employees
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-500" />
                <div className="text-right">
                  <span className="text-[10px] text-indigo-400 block font-bold">Simulated</span>
                  <span className="text-base font-bold text-indigo-300">
                    {simulationResult.simulated.headcount} employees
                  </span>
                </div>
              </div>
            </div>

            {/* Metric 3: Monthly Burn */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
              <span className="text-[11px] text-gray-400 uppercase font-bold flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-rose-400" /> Monthly Operational Burn
              </span>
              <div className="flex items-center justify-between pt-1">
                <div>
                  <span className="text-[10px] text-gray-500 block">Baseline</span>
                  <span className="text-sm font-semibold text-gray-400">
                    ${(simulationResult.baseline.monthly_burn_cents / 100).toLocaleString()}
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-500" />
                <div className="text-right">
                  <span className="text-[10px] text-rose-400 block font-bold">Simulated</span>
                  <span className="text-base font-bold text-rose-300">
                    ${(simulationResult.simulated.monthly_burn_cents / 100).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Metric 4: Runway Months */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
              <span className="text-[11px] text-gray-400 uppercase font-bold flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" /> Financial Runway
              </span>
              <div className="flex items-center justify-between pt-1">
                <div>
                  <span className="text-[10px] text-gray-500 block">Baseline</span>
                  <span className="text-sm font-semibold text-gray-400">
                    {simulationResult.baseline.runway_months} months
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-500" />
                <div className="text-right">
                  <span className="text-[10px] text-amber-400 block font-bold">Simulated</span>
                  <span className="text-base font-bold text-amber-300">
                    {simulationResult.simulated.runway_months} months
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Deliberation Summary */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 space-y-1">
            <span className="text-[10px] uppercase font-bold text-amber-300">
              Scenario Analysis & Deliberation Synthesis
            </span>
            <p className="text-xs text-gray-300 leading-relaxed font-sans">
              {simulationResult.deliberation_summary}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
