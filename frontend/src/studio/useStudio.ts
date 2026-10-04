/* Software Studio — live project state, kept fresh by polling the API. */

import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from './api';
import { ActivityEvent, Project, ProjectDetail } from './types';

const POLL_MS = 1500;
const MAX_EVENTS = 2000;

export interface StudioState {
  projects: Project[];
  project: ProjectDetail | null;
  events: ActivityEvent[];
  error: string | null;
  needsLogin: boolean;
  loaded: boolean;
  selectedId: string | null;
  select: (id: string | null) => void;
  refresh: () => Promise<void>;
}

export function useStudio(): StudioState {
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(() => localStorage.getItem('studio.project'));

  const cursor = useRef(0);
  const selected = useRef(selectedId);
  const busy = useRef(false);

  const select = useCallback((id: string | null) => {
    selected.current = id;
    cursor.current = 0;
    setSelectedId(id);
    setProject(null);
    setEvents([]);
    if (id) localStorage.setItem('studio.project', id);
    else localStorage.removeItem('studio.project');
  }, []);

  const refresh = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    try {
      const list = await api.listProjects();
      setProjects(list);
      setNeedsLogin(false);

      let id = selected.current;
      if (!id || !list.some((p) => p.id === id)) {
        id = list.length ? list[0].id : null;
        if (id !== selected.current) select(id);
      }
      if (id) {
        const [detail, fresh] = await Promise.all([api.getProject(id), api.events(id, cursor.current)]);
        if (selected.current === id) {
          setProject(detail);
          if (fresh.length) {
            cursor.current = fresh[fresh.length - 1].sequence;
            setEvents((previous) => [...previous, ...fresh].slice(-MAX_EVENTS));
          }
        }
      }
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setNeedsLogin(true);
      else setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      busy.current = false;
      setLoaded(true);
    }
  }, [select]);

  useEffect(() => {
    refresh();
    // No polling while the sign-in screen is showing: it would only produce 401s
    if (needsLogin) return;
    const timer = window.setInterval(refresh, POLL_MS);
    return () => window.clearInterval(timer);
  }, [refresh, needsLogin]);

  return { projects, project, events, error, needsLogin, loaded, selectedId, select, refresh };
}
