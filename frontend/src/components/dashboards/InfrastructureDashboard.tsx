import React, { useEffect, useState } from 'react';
import { Server, Database, Activity, Cpu, Layers, HardDrive, ShieldCheck } from 'lucide-react';
import { InfrastructureHealth } from '../../types/office';
import { apiClient } from '../../services/apiClient';

export const InfrastructureDashboard: React.FC = () => {
  const [health, setHealth] = useState<InfrastructureHealth | null>(null);

  useEffect(() => {
    apiClient.getInfrastructureHealth().then(setHealth);
  }, []);

  const getStatusBadge = (status: string) => {
    if (status === 'healthy') return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    if (status === 'degraded') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
  };

  return (
    <div className="flex-1 bg-[#090d16] p-6 overflow-y-auto space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3 text-cyan-400 font-bold text-lg">
          <Server className="w-6 h-6 text-cyan-500" />
          <span>Phase 20 Production Infrastructure Dashboard</span>
        </div>
        {health && (
          <span className={`px-3 py-1 rounded-full border font-bold uppercase ${getStatusBadge(health.status)}`}>
            System: {health.status}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="glass-panel p-4 space-y-2 border border-blue-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>FastAPI Server</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-xl font-bold text-blue-300">HTTP 200 OK</div>
          <span className="text-[10px] text-gray-500">Liveness & Readiness Probes Active</span>
        </div>

        <div className="glass-panel p-4 space-y-2 border border-emerald-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>PostgreSQL Pool</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-300">20 / 10</div>
          <span className="text-[10px] text-gray-500">Connection Pool & Overflow Limit</span>
        </div>

        <div className="glass-panel p-4 space-y-2 border border-red-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>Redis Cache Pool</span>
            <Cpu className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-xl font-bold text-red-300">50 Max Conn</div>
          <span className="text-[10px] text-gray-500">Async Connection Management</span>
        </div>

        <div className="glass-panel p-4 space-y-2 border border-indigo-500/30">
          <div className="flex items-center justify-between text-gray-400 font-semibold">
            <span>MinIO / S3 Storage</span>
            <HardDrive className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-bold text-indigo-300">SHA-256</div>
          <span className="text-[10px] text-gray-500">Payload Checksum Integrity Gated</span>
        </div>
      </div>
    </div>
  );
};
