import React, { useState, useEffect } from 'react';
import { Search, X, User, CheckSquare, Building, Users, FolderKanban, Calendar } from 'lucide-react';
import { WorkstationProjection, TaskInfo, DepartmentInfo, TeamInfo } from '../../types/office';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  workstations: WorkstationProjection[];
  departments: DepartmentInfo[];
  teams: TeamInfo[];
  tasks: TaskInfo[];
  onSelectEmployee: (ws: WorkstationProjection) => void;
  onSelectTask: (t: TaskInfo) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  workstations,
  departments,
  teams,
  tasks,
  onSelectEmployee,
  onSelectTask,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else setQuery('');
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const q = query.toLowerCase().trim();

  const matchedEmployees = q
    ? workstations.filter(
        (w) =>
          w.employee_name.toLowerCase().includes(q) ||
          w.employee_title.toLowerCase().includes(q) ||
          w.role.toLowerCase().includes(q)
      )
    : [];

  const matchedTasks = q
    ? tasks.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          t.task_id.toLowerCase().includes(q) ||
          t.priority.toLowerCase().includes(q)
      )
    : [];

  const matchedDepts = q
    ? departments.filter((d) => d.name.toLowerCase().includes(q) || d.department_id.toLowerCase().includes(q))
    : [];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-start justify-center pt-20 p-4">
      <div className="bg-[#0f172a] border border-white/20 rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden animate-scale-up">
        {/* Search Bar Input */}
        <div className="p-4 border-b border-white/10 flex items-center gap-3">
          <Search className="w-5 h-5 text-indigo-400" />
          <input
            type="text"
            autoFocus
            placeholder="Search employees, tasks, departments, teams... (ESC to close)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-gray-100 placeholder-gray-500 focus:outline-none"
          />
          <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search Results */}
        <div className="max-h-96 overflow-y-auto p-4 space-y-4 text-xs">
          {!q ? (
            <div className="text-center py-8 text-gray-500">
              Type to search across employees, tasks, departments, and teams.
            </div>
          ) : (
            <>
              {/* Matched Employees */}
              {matchedEmployees.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <User className="w-3 h-3 text-indigo-400" /> Employees ({matchedEmployees.length})
                  </div>
                  {matchedEmployees.map((w) => (
                    <div
                      key={w.employee_id}
                      onClick={() => {
                        onSelectEmployee(w);
                        onClose();
                      }}
                      className="p-2.5 rounded-xl bg-white/5 hover:bg-indigo-600/20 border border-white/5 hover:border-indigo-500/40 cursor-pointer flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-gray-200">{w.employee_name}</span>
                        <span className="text-gray-400 text-[11px] ml-2">({w.employee_title})</span>
                      </div>
                      <span className="text-[10px] font-semibold text-indigo-300">{w.department_id}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Matched Tasks */}
              {matchedTasks.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <CheckSquare className="w-3 h-3 text-emerald-400" /> Tasks ({matchedTasks.length})
                  </div>
                  {matchedTasks.map((t) => (
                    <div
                      key={t.task_id}
                      onClick={() => {
                        onSelectTask(t);
                        onClose();
                      }}
                      className="p-2.5 rounded-xl bg-white/5 hover:bg-emerald-600/20 border border-white/5 hover:border-emerald-500/40 cursor-pointer flex items-center justify-between"
                    >
                      <div>
                        <span className="font-mono text-emerald-400 text-[10px] mr-2">{t.task_id}</span>
                        <span className="font-bold text-gray-200">{t.title}</span>
                      </div>
                      <span className="text-[10px] font-semibold text-gray-400">{t.state}</span>
                    </div>
                  ))}
                </div>
              )}

              {matchedEmployees.length === 0 && matchedTasks.length === 0 && matchedDepts.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No matching items found for &quot;{query}&quot;.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
