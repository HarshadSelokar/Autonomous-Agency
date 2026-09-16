import React, { useEffect, useState } from 'react';
import { SwarmInfo } from '../../types/office';
import { fetchSwarmDetails, pauseSwarm, resumeSwarm, cancelSwarm } from '../../services/apiClient';

interface SwarmDetailPanelProps {
  swarmId: string | null;
  onClose: () => void;
}

export const SwarmDetailPanel: React.FC<SwarmDetailPanelProps> = ({ swarmId, onClose }) => {
  const [swarm, setSwarm] = useState<SwarmInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!swarmId) return;
    setLoading(true);
    setError(null);
    fetchSwarmDetails(swarmId)
      .then((data: SwarmInfo) => {
        setSwarm(data);
        setLoading(false);
      })
      .catch((err: any) => {
        setError(err.message || 'Failed to load swarm details');
        setLoading(false);
      });

  }, [swarmId]);

  if (!swarmId) return null;

  const handlePause = async () => {
    if (!swarm) return;
    await pauseSwarm(swarm.id);
    const updated = await fetchSwarmDetails(swarm.id);
    setSwarm(updated);
  };

  const handleResume = async () => {
    if (!swarm) return;
    await resumeSwarm(swarm.id);
    const updated = await fetchSwarmDetails(swarm.id);
    setSwarm(updated);
  };

  const handleCancel = async () => {
    if (!swarm) return;
    await cancelSwarm(swarm.id);
    const updated = await fetchSwarmDetails(swarm.id);
    setSwarm(updated);
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-slate-900/95 border-l border-cyan-500/30 p-6 overflow-y-auto backdrop-blur-md shadow-2xl z-50 transition-all">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono text-cyan-400 uppercase tracking-widest">Multi-Agent Swarm</span>
          <h2 className="text-xl font-bold text-slate-100">{swarm?.name || 'Loading...'}</h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
        >
          ✕
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-lg text-red-400 text-sm mb-4">
          {error}
        </div>
      )}

      {swarm && (
        <div className="space-y-6 text-sm text-slate-300">
          <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50 space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Swarm Code:</span>
              <span className="font-mono text-cyan-300">{swarm.code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Topology Mode:</span>
              <span className="font-mono text-cyan-400">{swarm.coordination_mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Status:</span>
              <span className={`font-mono px-2 py-0.5 text-xs rounded-md ${
                swarm.status === 'RUNNING' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' :
                swarm.status === 'PAUSED' ? 'bg-amber-950 text-amber-400 border border-amber-500/30' :
                swarm.status === 'COMPLETED' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/30' :
                'bg-slate-800 text-slate-400'
              }`}>
                {swarm.status}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Parent Task ID:</span>
              <span className="font-mono text-slate-300">{swarm.parent_task_id}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex space-x-2">
            {swarm.status === 'RUNNING' && (
              <button
                onClick={handlePause}
                className="flex-1 py-2 bg-amber-600/30 hover:bg-amber-600/50 border border-amber-500/50 text-amber-200 rounded-lg font-medium text-xs transition-colors"
              >
                Pause Swarm
              </button>
            )}
            {swarm.status === 'PAUSED' && (
              <button
                onClick={handleResume}
                className="flex-1 py-2 bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-emerald-200 rounded-lg font-medium text-xs transition-colors"
              >
                Resume Swarm
              </button>
            )}
            {['RUNNING', 'PAUSED', 'READY'].includes(swarm.status) && (
              <button
                onClick={handleCancel}
                className="flex-1 py-2 bg-red-600/30 hover:bg-red-600/50 border border-red-500/50 text-red-200 rounded-lg font-medium text-xs transition-colors"
              >
                Cancel Swarm
              </button>
            )}
          </div>

          {/* Members */}
          <div>
            <h3 className="text-xs font-mono text-slate-400 uppercase mb-3">Swarm Members ({swarm.members.length})</h3>
            <div className="space-y-2">
              {swarm.members.map((member) => (
                <div key={member.id} className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/40 flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-200">{member.role}</div>
                    <div className="text-xs font-mono text-cyan-400">{member.capability}</div>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                    {member.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Budget */}
          {swarm.budget && (
            <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40 space-y-3">
              <h3 className="text-xs font-mono text-slate-400 uppercase">Resource Budget Consumption</h3>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Execution Time</span>
                  <span className="text-slate-300 font-mono">
                    {swarm.budget.current_execution_time_seconds}s / {swarm.budget.max_execution_time_seconds}s
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-1.5">
                  <div
                    className="bg-cyan-500 h-1.5 rounded-full"
                    style={{
                      width: `${Math.min(100, (swarm.budget.current_execution_time_seconds / swarm.budget.max_execution_time_seconds) * 100)}%`,
                    }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Model Cost</span>
                  <span className="text-slate-300 font-mono">
                    ${swarm.budget.current_model_cost.toFixed(2)} / ${swarm.budget.max_model_cost.toFixed(2)}
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-1.5">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full"
                    style={{
                      width: `${Math.min(100, (swarm.budget.current_model_cost / swarm.budget.max_model_cost) * 100)}%`,
                    }}
                  ></div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
