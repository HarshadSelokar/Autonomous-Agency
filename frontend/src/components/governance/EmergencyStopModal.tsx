import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, X } from 'lucide-react';
import { apiClient } from '../../services/apiClient';

interface EmergencyStopModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const EmergencyStopModal: React.FC<EmergencyStopModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [confirmInput, setConfirmInput] = useState<string>('');
  const [reasonInput, setReasonInput] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleActivateStop = async () => {
    if (confirmInput.toUpperCase() !== 'CONFIRM') {
      alert('Please type CONFIRM to authorize global emergency stop.');
      return;
    }
    if (!reasonInput.trim()) {
      alert('Please provide a reason for activating emergency stop.');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.triggerEmergencyStop(reasonInput);
      onSuccess();
      onClose();
    } catch (err) {
      alert(`Emergency Stop Trigger Failed: ${err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-[#0f172a] border border-rose-500/50 rounded-2xl p-6 max-w-lg w-full space-y-5 shadow-2xl animate-scale-up">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-rose-500/20 pb-4">
          <div className="flex items-center gap-3 text-rose-400 font-bold text-lg">
            <div className="p-2 bg-rose-500/20 rounded-xl border border-rose-500/40">
              <ShieldAlert className="w-6 h-6 text-rose-400 animate-bounce" />
            </div>
            <div>
              <h3>GLOBAL EMERGENCY STOP</h3>
              <p className="text-xs text-rose-300 font-normal">Halt Autonomous AI Agent Execution</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Warning Text */}
        <div className="bg-rose-950/30 border border-rose-500/30 p-3.5 rounded-xl text-xs text-rose-200 leading-relaxed space-y-1">
          <p className="font-bold flex items-center gap-1.5 text-rose-300">
            <AlertTriangle className="w-4 h-4" />
            CRITICAL GOVERNANCE ACTION:
          </p>
          <p>
            Activating Emergency Stop halts all active agent execution runs, worker job processing, and dynamic task scheduling globally across all departments.
          </p>
        </div>

        {/* Inputs */}
        <div className="space-y-3 text-xs">
          <div>
            <label className="block text-gray-400 mb-1 font-medium">Reason for Intervening</label>
            <input
              type="text"
              placeholder="e.g. Safety audit requirement / Unexpected agent behavior"
              value={reasonInput}
              onChange={(e) => setReasonInput(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-rose-500"
            />
          </div>

          <div>
            <label className="block text-gray-400 mb-1 font-medium">
              Type <span className="font-mono text-rose-400 font-bold">CONFIRM</span> to proceed:
            </label>
            <input
              type="text"
              placeholder="CONFIRM"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 font-mono text-rose-300 focus:outline-none focus:border-rose-500 uppercase"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 border-t border-white/10 pt-4">
          <button onClick={onClose} className="px-4 py-2 rounded-xl bg-white/5 text-gray-300 text-xs font-semibold hover:bg-white/10">
            Cancel
          </button>
          <button
            disabled={isSubmitting || confirmInput.toUpperCase() !== 'CONFIRM'}
            onClick={handleActivateStop}
            className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-rose-900/50 flex items-center gap-2"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>ACTIVATE EMERGENCY STOP</span>
          </button>
        </div>
      </div>
    </div>
  );
};
