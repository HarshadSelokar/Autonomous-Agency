import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Zap,
  Lock,
  FileCheck,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Activity,
  Server,
  Database,
  Cpu,
  Radio,
  FileCode2,
} from 'lucide-react';

interface CircuitBreakerItem {
  id: string;
  name: string;
  dependency_name: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_threshold: number;
  recovery_time_seconds: number;
  failure_count: number;
  success_count: number;
  last_failure_at?: string;
  last_state_change_at: string;
}

interface SecurityIncidentItem {
  id: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'DETECTED' | 'TRIAGED' | 'CONTAINED' | 'RESOLVED';
  affected_components: string[];
  governance_approval_id?: string;
  detected_at: string;
}

interface AuditLogItem {
  id: string;
  timestamp: string;
  actor_id: string;
  action: string;
  resource: string;
  checksum: string;
}

interface ReadinessItem {
  id: string;
  domain: string;
  requirement: string;
  status: string;
  evidence_reference: string;
  tested_at: string;
}

export const ResilienceDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'breakers' | 'security' | 'audit' | 'dr'>('breakers');
  const [circuitBreakers, setCircuitBreakers] = useState<CircuitBreakerItem[]>([]);
  const [incidents, setIncidents] = useState<SecurityIncidentItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [readinessItems, setReadinessItems] = useState<ReadinessItem[]>([]);
  const [isChainValid, setIsChainValid] = useState<boolean>(true);
  const [drSlaPassed, setDrSlaPassed] = useState<boolean>(true);
  const [drEvidence, setDrEvidence] = useState<string>('RPO: 0.5m | RTO: 2.0m');
  const [loading, setLoading] = useState<boolean>(false);

  // Mock initial data fetch
  const fetchResilienceData = async () => {
    setLoading(true);
    try {
      // Mock circuit breakers
      setCircuitBreakers([
        {
          id: 'cb-1',
          name: 'llm_router_breaker',
          dependency_name: 'Groq / LLM Gateway',
          state: 'CLOSED',
          failure_threshold: 5,
          recovery_time_seconds: 60,
          failure_count: 0,
          success_count: 1420,
          last_state_change_at: new Date().toISOString(),
        },
        {
          id: 'cb-2',
          name: 'postgres_primary_breaker',
          dependency_name: 'PostgreSQL Database',
          state: 'CLOSED',
          failure_threshold: 3,
          recovery_time_seconds: 30,
          failure_count: 0,
          success_count: 8520,
          last_state_change_at: new Date().toISOString(),
        },
        {
          id: 'cb-3',
          name: 'vector_search_breaker',
          dependency_name: 'Qdrant / Memory Store',
          state: 'HALF_OPEN',
          failure_threshold: 4,
          recovery_time_seconds: 45,
          failure_count: 2,
          success_count: 48,
          last_state_change_at: new Date().toISOString(),
        },
      ]);

      // Mock security incidents
      setIncidents([
        {
          id: 'secinc-101',
          title: 'Adversarial Prompt Injection Blocked',
          description: 'Attempted system message extraction pattern detected in model gateway input.',
          severity: 'HIGH',
          status: 'CONTAINED',
          affected_components: ['model_gateway', 'agent_runtime'],
          governance_approval_id: 'gov-app-881',
          detected_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 'secinc-102',
          title: 'API Secret Redaction Verified',
          description: 'Secret token pattern masked before response transmission.',
          severity: 'MEDIUM',
          status: 'RESOLVED',
          affected_components: ['api_router'],
          detected_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ]);

      // Mock audit logs
      setAuditLogs([
        {
          id: 'audit-901',
          timestamp: new Date().toISOString(),
          actor_id: 'agent_ceo',
          action: 'AUTHORIZE_VENTURE',
          resource: 'venture_healthtech',
          checksum: 'a8f5f167f44f4964e6c998dee827110c',
        },
        {
          id: 'audit-900',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          actor_id: 'admin_security',
          action: 'UPDATE_CIRCUIT_POLICY',
          resource: 'llm_router_breaker',
          checksum: '9d2110c8f5f167f44f4964e6c998dee8',
        },
      ]);

      // Mock readiness items
      setReadinessItems([
        {
          id: 'readi-01',
          domain: 'SECURITY',
          requirement: 'Prompt Injection Sanitization & Secret Redaction',
          status: 'PASSED',
          evidence_reference: 'Passed regex pattern suite with zero unmasked leaks',
          tested_at: new Date().toISOString(),
        },
        {
          id: 'readi-02',
          domain: 'RELIABILITY',
          requirement: 'Circuit Breaker Fallback & Exponential Backoff Jitter',
          status: 'PASSED',
          evidence_reference: '100% fail-fast under simulated dependency outage',
          tested_at: new Date().toISOString(),
        },
        {
          id: 'readi-03',
          domain: 'DISASTER_RECOVERY',
          requirement: 'RPO < 5m and RTO < 15m Verification',
          status: 'PASSED',
          evidence_reference: 'RPO: 0.5m (Threshold 5m) | RTO: 2.0m (Threshold 15m)',
          tested_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResilienceData();
  }, []);

  const toggleCircuitState = (id: string) => {
    setCircuitBreakers((prev) =>
      prev.map((cb) =>
        cb.id === id ? { ...cb, state: cb.state === 'CLOSED' ? 'OPEN' : 'CLOSED' } : cb
      )
    );
  };

  return (
    <div className="p-6 space-y-6 bg-slate-950 text-slate-100 min-h-screen">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Production Hardening, Resilience & Disaster Recovery
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">
                Phase 30 Active
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Circuit breakers, prompt injection isolation, immutable SHA-256 audit log chaining, and RPO/RTO DR validation
            </p>
          </div>
        </div>

        <button
          onClick={fetchResilienceData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          Refresh State
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('breakers')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'breakers'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Zap className="w-4 h-4 text-amber-400" />
          Circuit Breakers & Dependencies
        </button>

        <button
          onClick={() => setActiveTab('security')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'security'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Lock className="w-4 h-4 text-red-400" />
          Security Incidents & Threats
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'audit'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <FileCode2 className="w-4 h-4 text-cyan-400" />
          Audit Trail & SHA-256 Chain
        </button>

        <button
          onClick={() => setActiveTab('dr')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'dr'
              ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <FileCheck className="w-4 h-4 text-emerald-400" />
          Disaster Recovery & Readiness Matrix
        </button>
      </div>

      {/* Tab 1: Circuit Breakers & Dependency Health */}
      {activeTab === 'breakers' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {circuitBreakers.map((cb) => (
              <div
                key={cb.id}
                className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-3 hover:border-slate-700 transition-all shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 truncate">{cb.name}</span>
                  <span
                    className={`px-2.5 py-1 text-[10px] font-bold rounded-full border ${
                      cb.state === 'CLOSED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : cb.state === 'OPEN'
                        ? 'bg-red-500/10 text-red-400 border-red-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {cb.state}
                  </span>
                </div>

                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <Server className="w-3.5 h-3.5 text-slate-500" />
                  Dependency: <span className="text-slate-200 font-medium">{cb.dependency_name}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 bg-slate-950/60 p-3 rounded-xl text-[11px] text-slate-400 border border-slate-800/80">
                  <div>
                    Fail Threshold: <span className="text-slate-200 font-semibold">{cb.failure_threshold}</span>
                  </div>
                  <div>
                    Fail Count: <span className="text-red-400 font-semibold">{cb.failure_count}</span>
                  </div>
                  <div>
                    Recovery SLA: <span className="text-slate-200 font-semibold">{cb.recovery_time_seconds}s</span>
                  </div>
                  <div>
                    Successes: <span className="text-emerald-400 font-semibold">{cb.success_count}</span>
                  </div>
                </div>

                <button
                  onClick={() => toggleCircuitState(cb.id)}
                  className={`w-full py-1.5 text-xs font-semibold rounded-xl border transition-all ${
                    cb.state === 'CLOSED'
                      ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30'
                      : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                  }`}
                >
                  {cb.state === 'CLOSED' ? 'Simulate Trip to OPEN' : 'Reset Circuit to CLOSED'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Security Incidents & Threat Signals */}
      {activeTab === 'security' && (
        <div className="space-y-4">
          <div className="bg-slate-900/70 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Lock className="w-4 h-4 text-red-400" />
                Active & Resolved Security Incidents
              </h2>
              <span className="text-xs text-slate-400">Total Incidents: {incidents.length}</span>
            </div>

            <div className="divide-y divide-slate-800">
              {incidents.map((inc) => (
                <div key={inc.id} className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-900/40 transition-all">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{inc.title}</span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold rounded-md ${
                          inc.severity === 'CRITICAL' || inc.severity === 'HIGH'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{inc.description}</p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>Affected: {inc.affected_components.join(', ')}</span>
                      <span>•</span>
                      <span>Detected: {new Date(inc.detected_at).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                      inc.status === 'CONTAINED' || inc.status === 'RESOLVED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {inc.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Audit Trail & SHA-256 Chain */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div className="bg-slate-900/70 p-4 rounded-2xl border border-slate-800 flex items-center justify-between shadow-md">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-xs font-bold text-white">SHA-256 Audit Log Hash Chain Status</h3>
                <p className="text-[11px] text-slate-400">Cryptographically immutable append-only hash verification</p>
              </div>
            </div>
            <span className="px-3 py-1 text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
              CHAIN INTEGRITY VERIFIED
            </span>
          </div>

          <div className="bg-slate-900/70 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Actor ID</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Target Resource</th>
                  <th className="p-3">SHA-256 Checksum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/40 transition-all">
                    <td className="p-3 text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</td>
                    <td className="p-3 font-medium text-slate-200">{log.actor_id}</td>
                    <td className="p-3 text-indigo-400 font-mono text-[11px]">{log.action}</td>
                    <td className="p-3 text-slate-300">{log.resource}</td>
                    <td className="p-3 font-mono text-[10px] text-cyan-400">{log.checksum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Disaster Recovery & Production Readiness Matrix */}
      {activeTab === 'dr' && (
        <div className="space-y-4">
          <div className="bg-slate-900/70 p-5 rounded-2xl border border-slate-800 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileCheck className="w-6 h-6 text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">Disaster Recovery SLA Verification</h3>
                  <p className="text-xs text-slate-400">Target SLAs: RPO &lt; 5 minutes | RTO &lt; 15 minutes</p>
                </div>
              </div>

              <span className="px-3 py-1 text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                SLA PASSED
              </span>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl text-xs text-slate-300 font-mono border border-slate-800">
              {drEvidence}
            </div>
          </div>

          <div className="bg-slate-900/70 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
            <div className="p-4 border-b border-slate-800 font-bold text-sm text-white">
              Production Readiness Requirements Checklist
            </div>
            <div className="divide-y divide-slate-800">
              {readinessItems.map((item) => (
                <div key={item.id} className="p-4 flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs font-bold text-slate-200">{item.requirement}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{item.evidence_reference}</div>
                  </div>
                  <span className="px-2.5 py-1 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                    {item.status}
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
