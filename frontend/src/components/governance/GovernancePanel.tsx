import React, { useState } from 'react';
import { GovernanceRequestInfo, RiskLevel, AutonomyLevel } from '../../types/office';
import { ShieldCheck, AlertTriangle, Check, X, Lock, Clock, HelpCircle } from 'lucide-react';
import { apiClient } from '../../services/apiClient';

interface GovernancePanelProps {
  requests: GovernanceRequestInfo[];
  onRefresh: () => void;
}

export const GovernancePanel: React.FC<GovernancePanelProps> = ({ requests, onRefresh }) => {
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const getRiskBadge = (risk: RiskLevel) => {
    switch (risk) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/50 animate-pulse';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/50';
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50';
    }
  };

  const handleApprove = async (requestId: string) => {
    setIsSubmitting(true);
    try {
      await apiClient.approveGovernanceRequest(requestId);
      onRefresh();
    } catch (err) {
      alert(`Approval failed: ${err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async (requestId: string) => {
    if (!rejectReason.trim()) {
      alert('Please provide a reason for rejection.');
      return;
    }
    setIsSubmitting(true);
    try {
      await apiClient.rejectGovernanceRequest(requestId, rejectReason);
      setRejectingId(null);
      setRejectReason('');
      onRefresh();
    } catch (err) {
      alert(`Rejection failed: ${err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6">
      {/* Title Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-indigo-400 font-bold text-lg">
          <ShieldCheck className="w-6 h-6 text-indigo-500" />
          <span>Human Governance Control Center</span>
        </div>
        <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 px-3 py-1 rounded-full font-semibold">
          {requests.length} Pending Approval Actions
        </span>
      </div>

      {/* Approvals List */}
      {requests.length === 0 ? (
        <div className="glass-panel p-12 text-center text-gray-500 text-xs space-y-2">
          <ShieldCheck className="w-8 h-8 mx-auto text-emerald-500/50" />
          <p className="font-semibold text-gray-300">No Pending Governance Approval Requests</p>
          <p className="text-gray-500">Autonomous organization is operating within authorized risk constraints.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <div
              key={req.request_id}
              className="glass-panel p-5 border-l-4 border-l-amber-500 space-y-4 hover:border-white/20 transition-all"
            >
              {/* Header Info */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${getRiskBadge(req.risk_level)}`}>
                      {req.risk_level} RISK
                    </span>
                    <span className="text-xs font-mono text-gray-400">{req.action_type}</span>
                  </div>
                  <h3 className="text-sm font-bold text-gray-100 mt-1">{req.title}</h3>
                </div>

                <div className="text-right text-[11px] text-gray-400">
                  <span>Requester: </span>
                  <span className="font-mono text-indigo-300">{req.requester_id}</span>
                </div>
              </div>

              {/* Action Description */}
              <p className="text-xs text-gray-300 bg-black/30 p-3 rounded-lg border border-white/5">
                {req.reason || 'Consequential action requiring human authorization before execution.'}
              </p>

              {/* Rejecting Form or Action Buttons */}
              {rejectingId === req.request_id ? (
                <div className="space-y-2 bg-rose-950/20 p-3 rounded-xl border border-rose-500/30">
                  <input
                    type="text"
                    placeholder="Enter reason for rejection..."
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-rose-500"
                  />
                  <div className="flex items-center gap-2 justify-end">
                    <button
                      onClick={() => setRejectingId(null)}
                      className="px-3 py-1 rounded-lg bg-white/10 text-gray-300 text-xs hover:bg-white/20"
                    >
                      Cancel
                    </button>
                    <button
                      disabled={isSubmitting}
                      onClick={() => handleReject(req.request_id)}
                      className="px-3 py-1 rounded-lg bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700"
                    >
                      Confirm Reject
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    disabled={isSubmitting}
                    onClick={() => setRejectingId(req.request_id)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-semibold hover:bg-rose-500/30 transition-all"
                  >
                    <X className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleApprove(req.request_id)}
                    className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-lg shadow-emerald-900/40"
                  >
                    <Check className="w-4 h-4" />
                    <span>Approve Execution</span>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
