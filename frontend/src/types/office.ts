/* Pixel Office — Complete TypeScript Types matching Backend Schema Contracts */

export type EmployeeVisualState =
  | 'IDLE'
  | 'WORKING'
  | 'THINKING'
  | 'WAITING'
  | 'BLOCKED'
  | 'IN_MEETING'
  | 'REVIEWING'
  | 'AWAITING_APPROVAL'
  | 'FAILED'
  | 'RECOVERING'
  | 'COMPLETED'
  | 'PAUSED'
  | 'OFFLINE';

export type TeamStatus =
  | 'PROPOSED'
  | 'FORMING'
  | 'ACTIVE'
  | 'PAUSED'
  | 'DISSOLVING'
  | 'DISSOLVED';

export type TaskState =
  | 'CREATED'
  | 'PLANNED'
  | 'ASSIGNED'
  | 'READY'
  | 'IN_PROGRESS'
  | 'BLOCKED'
  | 'FAILED'
  | 'REVIEW'
  | 'REWORK'
  | 'APPROVED'
  | 'COMPLETED'
  | 'CANCELLED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AutonomyLevel = 'FULLY_AUTONOMOUS' | 'SUPERVISED' | 'APPROVAL_REQUIRED' | 'HUMAN_ONLY' | 'BLOCKED';

export interface WorkstationProjection {
  employee_id: string;
  employee_name: string;
  employee_title: string;
  role: string;
  department_id: string;
  manager_id?: string;
  desk_id: string;
  area_type: string;
  visual_state: EmployeeVisualState;
  current_task_id?: string;
  current_task_title?: string;
  current_project_id?: string;
  current_project_name?: string;
  current_activity_summary: string;
  active_agent_id?: string;
  active_tool_name?: string;
  active_model_id?: string;
  is_manager: boolean;
  updated_at: string;
}

export interface HumanAttentionItem {
  item_id: string;
  attention_type: string;
  title: string;
  description: string;
  entity_id: string;
  entity_type: string;
  severity: string;
  action_url: string;
  created_at: string;
}

export interface OfficeActivityItem {
  activity_id: string;
  title: string;
  description: string;
  category: string;
  actor_id: string;
  entity_id: string;
  timestamp: string;
}

export interface CompanyOverview {
  company_name: string;
  is_emergency_stopped: boolean;
  active_employees_count: number;
  working_employees_count: number;
  in_meeting_employees_count: number;
  blocked_tasks_count: number;
  pending_approvals_count: number;
  active_projects_count: number;
  failed_verifications_count: number;
  active_recoveries_count: number;
  candidate_knowledge_count: number;
  validated_knowledge_count: number;
  authoritative_knowledge_count: number;
  contested_knowledge_count: number;
  stale_knowledge_count: number;
  active_experiments_count: number;
  active_research_programs_count: number;
  pending_research_requests_count: number;
  research_discoveries_count: number;
  innovation_proposals_count: number;
  attention_items: HumanAttentionItem[];
  recent_activities: OfficeActivityItem[];
  updated_at: string;
}

export interface DepartmentInfo {
  department_id: string;
  name: string;
  code: string;
  manager_id?: string;
  employee_count: number;
  active_projects_count: number;
  workload_percentage: number;
  capacity_status: string;
}

export interface TeamInfo {
  team_id: string;
  name: string;
  purpose: string;
  status: TeamStatus;
  department_id: string;
  manager_id?: string;
  member_ids: string[];
  capabilities: string[];
}

export interface TaskInfo {
  task_id: string;
  title: string;
  description?: string;
  state: TaskState;
  priority: string;
  assignee_id?: string;
  project_id?: string;
  dependencies: string[];
  verification_status: string;
  recovery_status: string;
  created_at: string;
}

export interface ProjectInfo {
  project_id: string;
  name: string;
  status: string;
  objective: string;
  manager_id?: string;
  team_id?: string;
  progress_percentage: number;
  task_count: number;
  blocked_task_count: number;
  delivery_state: string;
}

export interface MeetingInfo {
  meeting_id: string;
  title: string;
  purpose: string;
  organizer_id: string;
  participant_ids: string[];
  status: string;
  start_time: string;
  duration_minutes: number;
  related_task_id?: string;
}

export interface GovernanceRequestInfo {
  request_id: string;
  title: string;
  action_type: string;
  requester_id: string;
  risk_level: RiskLevel;
  autonomy_level: AutonomyLevel;
  status: string;
  reason: string;
  created_at: string;
  expires_at?: string;
}

export interface InfrastructureHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  api_status: string;
  database_status: string;
  redis_status: string;
  storage_status: string;
  worker_count: number;
  outbox_backlog_depth: number;
  metrics: Record<string, any>;
}

export type ConnectionStatus = 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING' | 'STALE';

export interface OfficeWebSocketEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  payload: Record<string, any>;
}
