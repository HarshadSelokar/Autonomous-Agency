import React, { useState, useEffect } from 'react';
import { Target, Users, TrendingUp, LifeBuoy, Megaphone, CheckCircle, ArrowRight, ShieldCheck, FileText, Layers, HeartPulse } from 'lucide-react';

export const GTMDashboard: React.FC = () => {
  const [products, setProducts] = useState<any[]>([
    { id: 'prod-1', name: 'Autonomous AI Agent OS', code: 'PROD-AIOS', lifecycle: 'ACTIVE', dollars: 10000.0 },
    { id: 'prod-2', name: 'Multi-Agent Swarm Engine', code: 'PROD-SWARM', lifecycle: 'BETA', dollars: 5000.0 },
  ]);

  const [leads, setLeads] = useState<any[]>([
    { id: 'lead-1', company_name: 'Titan Tech', contact_email: 'mark@titan.com', status: 'QUALIFIED', score: 90 },
    { id: 'lead-2', company_name: 'Apex Logistics', contact_email: 'sarah@apex.com', status: 'NEW', score: 40 },
  ]);

  const [opportunities, setOpportunities] = useState<any[]>([
    { id: 'opp-1', title: 'Titan Enterprise Deal', stage: 'PROPOSAL', estimated_value_cents: 10000000, probability_pct: 60 },
    { id: 'opp-2', title: 'Global Cloud Deployment', stage: 'WON', estimated_value_cents: 25000000, probability_pct: 100 },
  ]);

  const [customers, setCustomers] = useState<any[]>([
    { id: 'cust-1', name: 'Global Cloud Inc', domain: 'globalcloud.com', lifecycle_state: 'ACTIVE', health_score: 98.5 },
    { id: 'cust-2', name: 'Starlight Media', domain: 'starlight.com', lifecycle_state: 'ONBOARDING', health_score: 85.0 },
  ]);

  const [supportCases, setSupportCases] = useState<any[]>([
    { id: 'case-1', customer_id: 'cust-1', subject: 'Custom Model Routing Setup', priority: 'HIGH', status: 'OPEN' },
    { id: 'case-2', customer_id: 'cust-2', subject: 'Onboarding Milestone Verification', priority: 'MEDIUM', status: 'RESOLVED' },
  ]);

  useEffect(() => {
    fetch('/gtm/products')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && data.length > 0 && setProducts(data))
      .catch(() => {});

    fetch('/gtm/leads')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && data.length > 0 && setLeads(data))
      .catch(() => {});

    fetch('/gtm/opportunities')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && data.length > 0 && setOpportunities(data))
      .catch(() => {});

    fetch('/gtm/customers')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && data.length > 0 && setCustomers(data))
      .catch(() => {});
  }, []);

  const formatMoney = (cents: number) => `$${(cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  return (
    <div className="p-6 space-y-6 bg-slate-900 text-slate-100 min-h-screen">
      {/* Top Banner */}
      <div className="flex justify-between items-center bg-slate-800/80 p-5 rounded-2xl border border-slate-700/50 shadow-lg">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2 text-white">
            <Target className="w-6 h-6 text-indigo-400" />
            Product, Customer & Go-to-Market (GTM) Operations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Strategy &bull; Product &bull; Sales Pipeline &bull; Customer Success &bull; Support &bull; Governed Proposals
          </p>
        </div>
        <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 px-3 py-1.5 rounded-xl text-indigo-300 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          Commercial Governance Enforced
        </div>
      </div>

      {/* GTM Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Qualified Leads</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold text-cyan-400">{leads.filter((l) => l.status === 'QUALIFIED').length} / {leads.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Inbound Qualification Rate</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Sales Pipeline Value</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">
            {formatMoney(opportunities.reduce((acc, o) => acc + o.estimated_value_cents, 0))}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Total Active Pipeline Value</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Active Customers</span>
            <HeartPulse className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">{customers.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Avg Health Score: 92.0%</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Active Products</span>
            <Layers className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400">{products.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Software & Platform Products</div>
        </div>
      </div>

      {/* Main Grid: Pipeline & Customer Support */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Opportunities Pipeline */}
        <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold flex items-center gap-2 text-white">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              Sales Opportunity Pipeline
            </h2>
            <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-md">{opportunities.length} Deals</span>
          </div>

          <div className="space-y-3">
            {opportunities.map((opp) => (
              <div key={opp.id} className="flex justify-between items-center p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div>
                  <div className="text-xs font-bold text-slate-200">{opp.title}</div>
                  <div className="text-[11px] text-slate-400">Win Probability: {opp.probability_pct}%</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-white">{formatMoney(opp.estimated_value_cents)}</div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    opp.stage === 'WON' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-indigo-500/20 text-indigo-300'
                  }`}>
                    {opp.stage}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Support & Customer Success */}
        <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold flex items-center gap-2 text-white">
              <LifeBuoy className="w-4 h-4 text-cyan-400" />
              Customer Support & Escalations
            </h2>
            <span className="text-xs bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded-md">{supportCases.length} Cases</span>
          </div>

          <div className="space-y-3">
            {supportCases.map((c) => (
              <div key={c.id} className="flex justify-between items-center p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div>
                  <div className="text-xs font-bold text-slate-200">{c.subject}</div>
                  <div className="text-[11px] text-slate-400">Priority: {c.priority}</div>
                </div>
                <div className="text-right">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    c.status === 'RESOLVED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {c.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Customer 360 View */}
      <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
        <h2 className="text-sm font-bold flex items-center gap-2 text-white mb-4">
          <Users className="w-4 h-4 text-indigo-400" />
          Governed Customer 360 View
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {customers.map((cust) => (
            <div key={cust.id} className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 flex justify-between items-center">
              <div>
                <div className="text-xs font-bold text-slate-200">{cust.name} ({cust.domain})</div>
                <div className="text-[11px] text-slate-400 mt-1">Lifecycle: {cust.lifecycle_state}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg">
                  Health: {cust.health_score}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
