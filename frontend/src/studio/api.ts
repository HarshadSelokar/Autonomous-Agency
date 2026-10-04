/* Software Studio — API client. No mock fallbacks: a failed request is shown as a failure. */

import { ActivityEvent, Changes, NewProject, Project, ProjectDetail, Role } from './types';

const TOKEN_KEY = 'studio.token';
const API_KEY_KEY = 'studio.apiKey';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const credentials = {
  get token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  get apiKey() {
    return localStorage.getItem(API_KEY_KEY);
  },
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.removeItem(API_KEY_KEY);
  },
  setApiKey(key: string) {
    localStorage.setItem(API_KEY_KEY, key);
    localStorage.removeItem(TOKEN_KEY);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(API_KEY_KEY);
  },
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (credentials.token) headers.Authorization = `Bearer ${credentials.token}`;
  if (credentials.apiKey) headers['X-API-Key'] = credentials.apiKey;

  let response: Response;
  try {
    response = await fetch(path, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the API running on port 8000?');
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join('; ');
    } catch {
      /* not JSON */
    }
    throw new ApiError(response.status, detail);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  async login(email: string, password: string): Promise<void> {
    const result = await post<{ access_token: string }>('/auth/login', { email, password });
    credentials.setToken(result.access_token);
  },

  listProjects: () => request<Project[]>('/studio/projects'),
  getProject: (id: string) => request<ProjectDetail>(`/studio/projects/${id}`),
  createProject: (project: NewProject) => post<Project>('/studio/projects', { ...project, auto_start: true }),
  start: (id: string) => post<Project>(`/studio/projects/${id}/start`),
  deleteProject: (id: string, removeWorkspace: boolean) =>
    request<void>(`/studio/projects/${id}?remove_workspace=${removeWorkspace}`, { method: 'DELETE' }),
  cancel: (id: string) => post<{ cancel_requested: boolean }>(`/studio/projects/${id}/cancel`),

  events: (id: string, after: number) =>
    request<ActivityEvent[]>(`/studio/projects/${id}/events?after=${after}&limit=500`),
  changes: (id: string) => request<Changes>(`/studio/projects/${id}/diff`),

  tell: (id: string, text: string) => post<void>(`/studio/projects/${id}/messages`, { text }),
  ask: (id: string, text: string) => post<{ answer: string }>(`/studio/projects/${id}/ask`, { text }),

  approve: (id: string, ticketId: string) => post<void>(`/studio/projects/${id}/tickets/${ticketId}/approve`, {}),
  reject: (id: string, ticketId: string, feedback: string) =>
    post<void>(`/studio/projects/${id}/tickets/${ticketId}/reject`, { feedback }),

  addMember: (id: string, name: string, role: Role) => post<void>(`/studio/projects/${id}/team`, { name, role }),
  renameMember: (id: string, memberId: string, name: string) =>
    request<void>(`/studio/projects/${id}/team/${memberId}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  removeMember: (id: string, memberId: string) =>
    request<void>(`/studio/projects/${id}/team/${memberId}`, { method: 'DELETE' }),
};
