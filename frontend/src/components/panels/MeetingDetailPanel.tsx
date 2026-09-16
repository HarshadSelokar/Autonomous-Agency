import React from 'react';
import { MeetingInfo } from '../../types/office';
import { X, Calendar, Users, Clock, CheckCircle2 } from 'lucide-react';

interface MeetingDetailPanelProps {
  meeting: MeetingInfo | null;
  onClose: () => void;
}

export const MeetingDetailPanel: React.FC<MeetingDetailPanelProps> = ({ meeting, onClose }) => {
  if (!meeting) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 z-50 shadow-2xl flex flex-col p-6 overflow-y-auto animate-slide-left">
      <div className="flex items-start justify-between border-b border-white/10 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-pink-600/30 border border-pink-500/50 flex items-center justify-center text-pink-300">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-gray-400">{meeting.meeting_id}</span>
            <h2 className="text-sm font-bold text-gray-100">{meeting.title}</h2>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4 text-xs">
        {/* Purpose */}
        <div className="glass-panel p-3 space-y-1">
          <span className="text-[10px] text-gray-400 font-semibold uppercase">Meeting Purpose & Agenda</span>
          <p className="text-gray-200 text-[11px] leading-relaxed">{meeting.purpose}</p>
        </div>

        {/* Status & Duration */}
        <div className="grid grid-cols-2 gap-2">
          <div className="glass-panel p-3">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Status</span>
            <p className="font-bold text-pink-400 mt-1">{meeting.status}</p>
          </div>
          <div className="glass-panel p-3">
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Duration</span>
            <p className="font-bold text-gray-200 mt-1">{meeting.duration_minutes} min</p>
          </div>
        </div>

        {/* Participants */}
        <div className="glass-panel p-3 space-y-2">
          <div className="flex items-center gap-2 text-pink-400 font-bold">
            <Users className="w-3.5 h-3.5" />
            <span>Participants ({meeting.participant_ids.length})</span>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {meeting.participant_ids.map((id) => (
              <span key={id} className="bg-pink-500/20 text-pink-300 border border-pink-500/30 px-2 py-0.5 rounded text-[10px] font-mono">
                {id}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
