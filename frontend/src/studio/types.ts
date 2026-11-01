/* Software Studio — API types (mirror src/api/routes/studio.py) */

export type Role = 'MANAGER' | 'DEVELOPER' | 'QA' | 'REVIEWER';

export type TicketStatus =
  | 'TODO'
  | 'IN_PROGRESS'
  | 'TESTING'
  | 'IN_REVIEW'
  | 'AWAITING_APPROVAL'
  | 'DONE'
  | 'BLOCKED';

export interface Project {
  id: string;
  name: string;
  goal: string;
  status: string;
  is_running: boolean;
  repo_url: string | null;
  branch: string;
  workspace_path: string;
  test_command: string | null;
  engine: string;
  provider: string;
  model: string;
  require_approval: boolean;
  summary: string;
  failure_reason: string | null;
  usage: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  name: string;
  role: Role;
  state: string;
  activity: string;
  ticket_id: string | null;
  ticket_title: string | null;
}

export interface Ticket {
  id: string;
  sequence: number;
  title: string;
  description: string;
  acceptance_criteria: string;
  status: TicketStatus;
  depends_on: string[];
  assignee_id: string | null;
  attempts: number;
  feedback: string;
  commit_sha: string | null;
  result_summary: string;
  approval: string;
  approval_feedback: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  team: TeamMember[];
  tickets: Ticket[];
}

export interface ActivityEvent {
  sequence: number;
  kind: string;
  summary: string;
  actor_id: string;
  actor_name: string;
  actor_role: string;
  ticket_id: string | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface Changes {
  branch: string;
  commits: { sha: string; subject: string }[];
  diff: string;
}

export interface NewProject {
  name: string;
  goal: string;
  repo_url?: string;
  local_path?: string;
  test_command?: string;
  engine: string;
  developers: number;
  require_approval: boolean;
}
