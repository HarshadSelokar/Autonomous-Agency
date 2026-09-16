import React, { useState } from 'react';
import {
  WorkstationProjection,
  DepartmentInfo,
  MeetingInfo,
} from '../../types/office';
import { EmployeeSprite } from './EmployeeSprite';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Building,
  Calendar,
  Users,
} from 'lucide-react';

interface OfficeCanvasProps {
  workstations: WorkstationProjection[];
  departments: DepartmentInfo[];
  meetings: MeetingInfo[];
  selectedWorkstation: WorkstationProjection | null;
  onSelectWorkstation: (ws: WorkstationProjection) => void;
  onSelectMeeting?: (meeting: MeetingInfo) => void;
}

export const OfficeCanvas: React.FC<OfficeCanvasProps> = ({
  workstations,
  departments,
  meetings,
  selectedWorkstation,
  onSelectWorkstation,
  onSelectMeeting,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [activeDeptFilter, setActiveDeptFilter] = useState<string>('ALL');

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 15, 150));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 15, 60));
  const handleResetZoom = () => {
    setZoomLevel(100);
    setActiveDeptFilter('ALL');
  };

  // Group workstations by department
  const deptMap: Record<string, WorkstationProjection[]> = {};
  workstations.forEach((ws) => {
    const dept = ws.department_id || 'ENGINEERING';
    if (!deptMap[dept]) deptMap[dept] = [];
    deptMap[dept].push(ws);
  });

  const availableDepts = Object.keys(deptMap);

  const filteredDepts =
    activeDeptFilter === 'ALL'
      ? availableDepts
      : availableDepts.filter((d) => d === activeDeptFilter);

  return (
    <div className="relative flex-1 bg-[#090d16] overflow-hidden flex flex-col">
      {/* Top Camera & Filter Controls */}
      <div className="h-12 bg-[#0f172a]/60 border-b border-white/10 px-4 flex items-center justify-between z-10 backdrop-blur-md">
        {/* Department Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto py-1">
          <button
            onClick={() => setActiveDeptFilter('ALL')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeDeptFilter === 'ALL'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            All Departments
          </button>
          {availableDepts.map((deptId) => (
            <button
              key={deptId}
              onClick={() => setActiveDeptFilter(deptId)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase transition-all ${
                activeDeptFilter === deptId
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
            >
              {deptId.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Camera Zoom Buttons */}
        <div className="flex items-center gap-1.5 bg-black/40 p-1 rounded-lg border border-white/10">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-mono font-bold text-indigo-300 w-10 text-center">
            {zoomLevel}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <div className="h-3 w-px bg-white/10 mx-1" />
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            title="Fit to Office"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Office Canvas Render Container */}
      <div className="flex-1 overflow-auto p-6 scrollbar-thin">
        <div
          style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top left' }}
          className="transition-transform duration-200 space-y-8"
        >
          {/* Active Meeting Rooms Section */}
          {meetings.length > 0 && (
            <div className="glass-panel p-4 border border-pink-500/30 bg-pink-950/10">
              <div className="flex items-center gap-2 text-pink-400 font-bold text-xs uppercase tracking-wider mb-3">
                <Calendar className="w-4 h-4" />
                <span>Active Executive Meeting Rooms</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {meetings.map((meeting) => (
                  <div
                    key={meeting.meeting_id}
                    onClick={() => onSelectMeeting && onSelectMeeting(meeting)}
                    className="bg-pink-500/10 border border-pink-500/30 p-3 rounded-xl hover:bg-pink-500/20 cursor-pointer transition-all space-y-1"
                  >
                    <div className="text-xs font-bold text-pink-300 truncate">{meeting.title}</div>
                    <div className="text-[10px] text-gray-400">{meeting.purpose}</div>
                    <div className="flex items-center justify-between text-[10px] text-pink-400 pt-1">
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {meeting.participant_ids.length} Participants
                      </span>
                      <span className="font-mono">{meeting.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Department Quadrants Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredDepts.map((deptId) => {
              const deptWorkstations = deptMap[deptId] || [];
              const deptInfo = departments.find(
                (d) => d.department_id === deptId || d.name.toUpperCase() === deptId.toUpperCase()
              );

              return (
                <div
                  key={deptId}
                  className="glass-panel p-5 space-y-4 border border-indigo-500/20 hover:border-indigo-500/40 transition-all"
                >
                  {/* Department Zone Header */}
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2.5">
                      <Building className="w-4 h-4 text-indigo-400" />
                      <div>
                        <h3 className="text-xs font-bold text-gray-200 tracking-wider uppercase">
                          {deptId.replace('_', ' ')}
                        </h3>
                        <p className="text-[10px] text-gray-400">
                          {deptWorkstations.length} Active Workstations
                        </p>
                      </div>
                    </div>
                    {deptInfo && (
                      <span className="text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full">
                        {deptInfo.workload_percentage || 50}% Load
                      </span>
                    )}
                  </div>

                  {/* Workstations Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {deptWorkstations.map((ws) => (
                      <EmployeeSprite
                        key={ws.employee_id}
                        workstation={ws}
                        onSelect={onSelectWorkstation}
                        isSelected={selectedWorkstation?.employee_id === ws.employee_id}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
