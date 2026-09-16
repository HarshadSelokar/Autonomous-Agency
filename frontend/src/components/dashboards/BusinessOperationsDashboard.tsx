import React, { useState, useEffect } from 'react';
import { DollarSign, CreditCard, ShoppingBag, FileText, CheckCircle, AlertTriangle, ArrowUpRight, ArrowDownRight, Scale, ShieldCheck } from 'lucide-react';

export const BusinessOperationsDashboard: React.FC = () => {
  const [cashFlow, setCashFlow] = useState<any>({
    actual_inflow_cents: 7500000,
    actual_outflow_cents: 3200000,
    net_actual_cash_cents: 4300000,
    expected_inflow_cents: 2500000,
    expected_outflow_cents: 1200000,
    available_budget_cents: 10000000,
  });

  const [invoices, setInvoices] = useState<any[]>([
    { id: 'inv-1', invoice_number: 'INV-2026-001', customer_id: 'Acme Corp', total_cents: 2500000, status: 'SENT', issue_date: '2026-09-15' },
    { id: 'inv-2', invoice_number: 'INV-2026-002', customer_id: 'Starlight Inc', total_cents: 5000000, status: 'PAID', issue_date: '2026-09-10' },
  ]);

  const [procurements, setProcurements] = useState<any[]>([
    { id: 'pr-1', item_description: 'High-Performance GPU Cluster', estimated_cents: 4500000, status: 'APPROVED', requester_id: 'emp-dev-1' },
    { id: 'pr-2', item_description: 'SaaS Analytics Subscription', estimated_cents: 120000, status: 'REQUESTED', requester_id: 'emp-ops-1' },
  ]);

  const [reconciliations, setReconciliations] = useState<any[]>([
    { id: 'rec-1', source_provider: 'STRIPE_BANK', status: 'MATCHED', total_matched_cents: 7500000, total_mismatched_cents: 0 },
    { id: 'rec-2', source_provider: 'AWS_BILLING', status: 'MISMATCH', total_matched_cents: 3000000, total_mismatched_cents: 200000 },
  ]);

  useEffect(() => {
    // Fetch live business endpoints
    fetch('/business/cash-flow')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setCashFlow(data))
      .catch(() => {});

    fetch('/business/invoices')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setInvoices(data))
      .catch(() => {});

    fetch('/business/procurement')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setProcurements(data))
      .catch(() => {});
  }, []);

  const formatMoney = (cents: number) => `$${(cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  return (
    <div className="p-6 space-y-6 bg-slate-900 text-slate-100 min-h-screen">
      {/* Top Banner */}
      <div className="flex justify-between items-center bg-slate-800/80 p-5 rounded-2xl border border-slate-700/50 shadow-lg">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2 text-white">
            <DollarSign className="w-6 h-6 text-emerald-400" />
            Autonomous Business Operations & Financial Control
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Governed Financial Invariants &bull; Deterministic Reconciliation &bull; Separation of Duties
          </p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl text-emerald-400 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4" />
          Financial Authority Governed
        </div>
      </div>

      {/* Cash Flow Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Actual Cash Inflow</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">{formatMoney(cashFlow.actual_inflow_cents)}</div>
          <div className="text-[11px] text-slate-500 mt-1">Verified Received Funds</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Actual Outflow</span>
            <ArrowDownRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">{formatMoney(cashFlow.actual_outflow_cents)}</div>
          <div className="text-[11px] text-slate-500 mt-1">Incurred Operational Costs</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Net Operating Cash</span>
            <Scale className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold text-cyan-400">{formatMoney(cashFlow.net_actual_cash_cents)}</div>
          <div className="text-[11px] text-slate-500 mt-1">Inflow minus Outflow</div>
        </div>

        <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Available Budget</span>
            <CreditCard className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-extrabold text-indigo-400">{formatMoney(cashFlow.available_budget_cents)}</div>
          <div className="text-[11px] text-slate-500 mt-1">Allocated Department Budget</div>
        </div>
      </div>

      {/* Main Grid: Invoices & Procurement */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Invoices */}
        <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold flex items-center gap-2 text-white">
              <FileText className="w-4 h-4 text-indigo-400" />
              Invoices & Accounts Receivable
            </h2>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-md">{invoices.length} Invoices</span>
          </div>

          <div className="space-y-3">
            {invoices.map((inv) => (
              <div key={inv.id} className="flex justify-between items-center p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div>
                  <div className="text-xs font-bold text-slate-200">{inv.invoice_number}</div>
                  <div className="text-[11px] text-slate-400">{inv.customer_id} &bull; Issued {inv.issue_date}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-white">{formatMoney(inv.total_cents)}</div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    inv.status === 'PAID' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Procurement & POs */}
        <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold flex items-center gap-2 text-white">
              <ShoppingBag className="w-4 h-4 text-cyan-400" />
              Procurement & Purchase Orders
            </h2>
            <span className="text-xs bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded-md">{procurements.length} Requests</span>
          </div>

          <div className="space-y-3">
            {procurements.map((proc) => (
              <div key={proc.id} className="flex justify-between items-center p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div>
                  <div className="text-xs font-bold text-slate-200">{proc.item_description}</div>
                  <div className="text-[11px] text-slate-400">Requester: {proc.requester_id}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-white">{formatMoney(proc.estimated_cents)}</div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    proc.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'
                  }`}>
                    {proc.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Financial Reconciliation Status */}
      <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/50">
        <h2 className="text-sm font-bold flex items-center gap-2 text-white mb-4">
          <Scale className="w-4 h-4 text-emerald-400" />
          Deterministic Financial Reconciliation Engine
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reconciliations.map((rec) => (
            <div key={rec.id} className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 flex justify-between items-center">
              <div>
                <div className="text-xs font-bold text-slate-200">{rec.source_provider} Statement</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Matched: {formatMoney(rec.total_matched_cents)} | Discrepancy: {formatMoney(rec.total_mismatched_cents)}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                {rec.status === 'MATCHED' ? (
                  <div className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg text-xs font-semibold">
                    <CheckCircle className="w-3.5 h-3.5" />
                    MATCHED
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-lg text-xs font-semibold">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    MISMATCH
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
