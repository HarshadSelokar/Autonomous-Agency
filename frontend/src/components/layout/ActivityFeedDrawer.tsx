import React from 'react';
import { X, Activity, Filter, Clock } from 'lucide-react';
import { OfficeActivityItem } from '../../types/office';

interface ActivityFeedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activities: OfficeActivityItem[];
}

export const ActivityFeedDrawer: React.FC<ActivityFeedDrawerProps> = ({
  isOpen,
  onClose,
  activities,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 z-50 shadow-2xl flex flex-col animate-slide-left">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
          <Activity className="w-4 h-4" />
          <span>Real-time Activity Stream</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Feed List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activities.length === 0 ? (
          <div className="text-center py-12 text-gray-500 text-xs">
            No recent activity items recorded.
          </div>
        ) : (
          activities.map((act) => (
            <div
              key={act.activity_id}
              className="bg-white/5 border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-all text-xs space-y-1"
            >
              <div className="flex items-center justify-between text-gray-400">
                <span className="font-semibold text-indigo-300">{act.category}</span>
                <span className="flex items-center gap-1 text-[10px] text-gray-500">
                  <Clock className="w-3 h-3" />
                  {act.timestamp ? new Date(act.timestamp).toLocaleTimeString() : 'Just now'}
                </span>
              </div>
              <div className="font-medium text-gray-200">{act.title}</div>
              {act.description && <div className="text-gray-400 text-[11px]">{act.description}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
