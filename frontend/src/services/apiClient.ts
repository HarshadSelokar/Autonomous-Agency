/* Pixel Office — Typed API Client */

import {
  CompanyOverview,
  WorkstationProjection,
  HumanAttentionItem,
  DepartmentInfo,
  TeamInfo,
  TaskInfo,
  ProjectInfo,
  MeetingInfo,
  GovernanceRequestInfo,
  InfrastructureHealth,
} from '../types/office';

const API_BASE = '/office';

export class OfficeApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = endpoint.startsWith('/') ? endpoint : `${API_BASE}/${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Request failed [${response.status}]: ${errorText || response.statusText}`);
    }

    return response.json();
  }

  async getCompanyOverview(): Promise<CompanyOverview> {
    return this.request<CompanyOverview>('/office/overview');
  }

  async getWorkstations(): Promise<WorkstationProjection[]> {
    return this.request<WorkstationProjection[]>('/office/employees');
  }

  async getAttentionQueue(): Promise<HumanAttentionItem[]> {
    return this.request<HumanAttentionItem[]>('/office/attention');
  }

  async reconcileState(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/office/reconcile');
  }

  async getDepartments(): Promise<DepartmentInfo[]> {
    try {
      return await this.request<DepartmentInfo[]>('/departments');
    } catch {
      // Fallback empty list if endpoint unpopulated
      return [];
    }
  }

  async getTeams(): Promise<TeamInfo[]> {
    try {
      return await this.request<TeamInfo[]>('/teams');
    } catch {
      return [];
    }
  }

  async getTasks(): Promise<TaskInfo[]> {
    try {
      return await this.request<TaskInfo[]>('/tasks');
    } catch {
      return [];
    }
  }

  async getProjects(): Promise<ProjectInfo[]> {
    try {
      return await this.request<ProjectInfo[]>('/software/projects');
    } catch {
      return [];
    }
  }

  async getMeetings(): Promise<MeetingInfo[]> {
    try {
      return await this.request<MeetingInfo[]>('/meetings');
    } catch {
      return [];
    }
  }

  async getGovernanceRequests(): Promise<GovernanceRequestInfo[]> {
    try {
      return await this.request<GovernanceRequestInfo[]>('/governance/approvals/pending');
    } catch {
      return [];
    }
  }

  async approveGovernanceRequest(requestId: string, actorId: string = 'human-admin'): Promise<boolean> {
    await this.request(`/governance/approvals/${requestId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_by_actor_id: actorId }),
    });
    return true;
  }

  async rejectGovernanceRequest(requestId: string, reason: string, actorId: string = 'human-admin'): Promise<boolean> {
    await this.request(`/governance/approvals/${requestId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejected_by_actor_id: actorId, reason }),
    });
    return true;
  }

  async triggerEmergencyStop(reason: string, actorId: string = 'human-admin'): Promise<boolean> {
    await this.request('/governance/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({
        scope: 'GLOBAL',
        scope_id: 'GLOBAL',
        activated_by_actor_id: actorId,
        reason,
      }),
    });
    return true;
  }

  async getInfrastructureHealth(): Promise<InfrastructureHealth> {
    try {
      const data = await this.request<any>('/health/ready');
      return {
        status: data.status === 'ready' ? 'healthy' : 'degraded',
        api_status: 'healthy',
        database_status: data.dependencies?.database?.status || 'unknown',
        redis_status: data.dependencies?.redis?.status || 'unknown',
        storage_status: 'healthy',
        worker_count: 1,
        outbox_backlog_depth: data.dependencies?.outbox_backlog_depth || 0,
        metrics: data.metrics_summary || {},
      };
    } catch (err) {
      return {
        status: 'unhealthy',
        api_status: 'degraded',
        database_status: 'unhealthy',
        redis_status: 'unhealthy',
        storage_status: 'unknown',
        worker_count: 0,
        outbox_backlog_depth: 0,
        metrics: {},
      };
    }
  }
}

export const apiClient = new OfficeApiClient();
