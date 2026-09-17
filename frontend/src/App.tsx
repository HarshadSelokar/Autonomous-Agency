import React, { useState, useEffect, useCallback } from 'react';
import {
  CompanyOverview,
  WorkstationProjection,
  DepartmentInfo,
  TeamInfo,
  TaskInfo,
  ProjectInfo,
  MeetingInfo,
  GovernanceRequestInfo,
  ConnectionStatus,
  OfficeWebSocketEvent,
} from './types/office';
import { apiClient } from './services/apiClient';
import { wsClient } from './services/websocketClient';

import { AppShell } from './components/layout/AppShell';
import { Sidebar } from './components/layout/Sidebar';
import { ActivityFeedDrawer } from './components/layout/ActivityFeedDrawer';
import { OfficeCanvas } from './components/office/OfficeCanvas';
import { EmployeeDetailPanel } from './components/panels/EmployeeDetailPanel';
import { TaskDetailPanel } from './components/panels/TaskDetailPanel';
import { ProjectDetailPanel } from './components/panels/ProjectDetailPanel';
import { MeetingDetailPanel } from './components/panels/MeetingDetailPanel';
import { GovernancePanel } from './components/governance/GovernancePanel';
import { EmergencyStopModal } from './components/governance/EmergencyStopModal';

import { CompanyOverviewDashboard } from './components/dashboards/CompanyOverviewDashboard';
import { VerificationDashboard } from './components/dashboards/VerificationDashboard';
import { RecoveryDashboard } from './components/dashboards/RecoveryDashboard';
import { WorkforceDashboard } from './components/dashboards/WorkforceDashboard';
import { InfrastructureDashboard } from './components/dashboards/InfrastructureDashboard';
import { ResearchInnovationDashboard } from './components/dashboards/ResearchInnovationDashboard';
import { BusinessOperationsDashboard } from './components/dashboards/BusinessOperationsDashboard';
import { GTMDashboard } from './components/dashboards/GTMDashboard';
import { CompanyDashboard } from './components/dashboards/CompanyDashboard';
import { SimulationDashboard } from './components/dashboards/SimulationDashboard';
import { CompanyIntelligenceDashboard } from './components/dashboards/CompanyIntelligenceDashboard';
import { LearningAdaptationDashboard } from './components/dashboards/LearningAdaptationDashboard';
import { GlobalSearchModal } from './components/search/GlobalSearchModal';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<string>('canvas');
  const [activeCompanyId, setActiveCompanyId] = useState<string>('comp-main-01');
  const [activeEnvironment, setActiveEnvironment] = useState<'PRODUCTION' | 'SIMULATION'>('PRODUCTION');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('DISCONNECTED');

  const [overview, setOverview] = useState<CompanyOverview | null>(null);
  const [workstations, setWorkstations] = useState<WorkstationProjection[]>([]);
  const [departments, setDepartments] = useState<DepartmentInfo[]>([]);
  const [teams, setTeams] = useState<TeamInfo[]>([]);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [meetings, setMeetings] = useState<MeetingInfo[]>([]);
  const [governanceRequests, setGovernanceRequests] = useState<GovernanceRequestInfo[]>([]);

  // Drawers & Modals
  const [selectedWorkstation, setSelectedWorkstation] = useState<WorkstationProjection | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskInfo | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectInfo | null>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingInfo | null>(null);

  const [isActivityDrawerOpen, setIsActivityDrawerOpen] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isEmergencyStopOpen, setIsEmergencyStopOpen] = useState<boolean>(false);

  // Load Initial REST Snapshot
  const loadInitialData = useCallback(async () => {
    try {
      const [ov, ws, dept, tm, tk, prj, mt, gov] = await Promise.all([
        apiClient.getCompanyOverview(),
        apiClient.getWorkstations(),
        apiClient.getDepartments(),
        apiClient.getTeams(),
        apiClient.getTasks(),
        apiClient.getProjects(),
        apiClient.getMeetings(),
        apiClient.getGovernanceRequests(),
      ]);

      setOverview(ov);
      setWorkstations(ws);
      setDepartments(dept);
      setTeams(tm);
      setTasks(tk);
      setProjects(prj);
      setMeetings(mt);
      setGovernanceRequests(gov);
    } catch (err) {
      console.error('Error fetching initial REST snapshot:', err);
    }
  }, []);

  useEffect(() => {
    loadInitialData();

    // Connect WebSocket Client
    wsClient.connect();

    const unsubStatus = wsClient.onStatusChange((status) => {
      setConnectionStatus(status);
      if (status === 'CONNECTED') {
        // Reconcile snapshot on reconnect
        apiClient.reconcileState().then(() => loadInitialData());
      }
    });

    const unsubEvents = wsClient.onEvent((evt: OfficeWebSocketEvent) => {
      // Live event application to frontend state
      if (evt.event_type.startsWith('employee.') || evt.event_type.startsWith('agent.')) {
        loadInitialData();
      } else if (evt.event_type.startsWith('governance.')) {
        apiClient.getGovernanceRequests().then(setGovernanceRequests);
        apiClient.getCompanyOverview().then(setOverview);
      } else if (evt.event_type.startsWith('task.')) {
        apiClient.getTasks().then(setTasks);
        apiClient.getCompanyOverview().then(setOverview);
      }
    });

    // Periodic polling backup (every 30s)
    const timer = setInterval(() => {
      loadInitialData();
    }, 30000);

    return () => {
      unsubStatus();
      unsubEvents();
      clearInterval(timer);
      wsClient.disconnect();
    };
  }, [loadInitialData]);

  return (
    <AppShell
      overview={overview}
      connectionStatus={connectionStatus}
      activeView={activeView}
      activeCompanyId={activeCompanyId}
      activeEnvironment={activeEnvironment}
      onSelectCompany={setActiveCompanyId}
      onSelectEnvironment={setActiveEnvironment}
      onSelectView={setActiveView}
      onOpenSearch={() => setIsSearchOpen(true)}
      onOpenEmergencyStop={() => setIsEmergencyStopOpen(true)}
      onToggleActivityFeed={() => setIsActivityDrawerOpen((prev) => !prev)}
    >
      <Sidebar activeView={activeView} onSelectView={setActiveView} />

      {/* Main View Router */}
      <main className="flex-1 relative flex flex-col overflow-hidden">
        {activeView === 'overview' && (
          <CompanyOverviewDashboard overview={overview} onNavigateView={setActiveView} />
        )}

        {activeView === 'intelligence' && <CompanyIntelligenceDashboard companyId={activeCompanyId} />}
        {activeView === 'learning' && <LearningAdaptationDashboard companyId={activeCompanyId} />}
        {activeView === 'companies' && <CompanyDashboard />}
        {activeView === 'simulations' && <SimulationDashboard />}

        {activeView === 'canvas' && (
          <OfficeCanvas
            workstations={workstations}
            departments={departments}
            meetings={meetings}
            selectedWorkstation={selectedWorkstation}
            onSelectWorkstation={setSelectedWorkstation}
            onSelectMeeting={setSelectedMeeting}
          />
        )}

        {activeView === 'governance' && (
          <GovernancePanel requests={governanceRequests} onRefresh={loadInitialData} />
        )}

        {activeView === 'verification' && <VerificationDashboard overview={overview} />}
        {activeView === 'recovery' && <RecoveryDashboard overview={overview} />}
        {activeView === 'workforce' && <WorkforceDashboard overview={overview} />}
        {activeView === 'infrastructure' && <InfrastructureDashboard />}
        {activeView === 'research' && <ResearchInnovationDashboard overview={overview} />}
        {activeView === 'business' && <BusinessOperationsDashboard />}
        {activeView === 'gtm' && <GTMDashboard />}

        {/* Fallback for other view tabs */}
        {!['overview', 'intelligence', 'learning', 'companies', 'simulations', 'canvas', 'governance', 'verification', 'recovery', 'workforce', 'infrastructure', 'research', 'business', 'gtm'].includes(activeView) && (
          <div className="flex-1 bg-[#090d16] p-8 flex items-center justify-center text-gray-500 text-xs">
            Viewing Operational Domain: <span className="font-bold text-indigo-400 ml-1 uppercase">{activeView}</span>
          </div>
        )}
      </main>

      {/* Drawers & Detail Panels */}
      <EmployeeDetailPanel
        workstation={selectedWorkstation}
        onClose={() => setSelectedWorkstation(null)}
      />

      <TaskDetailPanel task={selectedTask} onClose={() => setSelectedTask(null)} />

      <ProjectDetailPanel project={selectedProject} onClose={() => setSelectedProject(null)} />

      <MeetingDetailPanel meeting={selectedMeeting} onClose={() => setSelectedMeeting(null)} />

      <ActivityFeedDrawer
        isOpen={isActivityDrawerOpen}
        onClose={() => setIsActivityDrawerOpen(false)}
        activities={overview?.recent_activities || []}
      />

      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        workstations={workstations}
        departments={departments}
        teams={teams}
        tasks={tasks}
        onSelectEmployee={setSelectedWorkstation}
        onSelectTask={setSelectedTask}
      />

      <EmergencyStopModal
        isOpen={isEmergencyStopOpen}
        onClose={() => setIsEmergencyStopOpen(false)}
        onSuccess={loadInitialData}
      />
    </AppShell>
  );
};

export default App;
