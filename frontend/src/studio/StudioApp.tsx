/* Software Studio — the office floor on the left, the command center on the right. */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api, credentials } from './api';
import { OfficeView } from './office/OfficeView';
import { drawPortrait, lookFor } from './office/scene';
import { ActivityTab, AskTab, ChangesTab, TasksTab, TeamTab } from './panels';
import { NewProject, ProjectDetail, TeamMember } from './types';
import { useStudio } from './useStudio';
import './studio.css';

type Tab = 'tasks' | 'activity' | 'ask' | 'changes' | 'team';
const TABS: { id: Tab; label: string }[] = [
  { id: 'tasks', label: 'tasks' },
  { id: 'activity', label: 'activity' },
  { id: 'ask', label: 'ask me' },
  { id: 'changes', label: 'changes' },
  { id: 'team', label: 'workers' },
];

const STATUS_TEXT: Record<string, string> = {
  CREATED: 'not started',
  PLANNING: 'planning',
  RUNNING: 'working',
  COMPLETED: 'finished',
  NEEDS_ATTENTION: 'needs attention',
  FAILED: 'failed',
  CANCELLED: 'stopped',
  INTERRUPTED: 'interrupted',
  WAITING_FOR_QUOTA: 'waiting for quota',
};

/* ------------------------------------------------------------------- login */
const Login: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const [mode, setMode] = useState<'password' | 'key'>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [key, setKey] = useState('');
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setFailure(null);
    try {
      if (mode === 'key') {
        credentials.setApiKey(key.trim());
        await api.listProjects();
      } else {
        await api.login(email.trim(), password);
      }
      onDone();
    } catch (err) {
      credentials.clear();
      setFailure(err instanceof Error ? err.message : 'Sign-in failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="studio studio-center">
      <form className="card login" onSubmit={submit}>
        <h1>Pixel Office</h1>
        <p className="note">Sign in to see your team.</p>
        <div className="segmented">
          <button type="button" className={mode === 'password' ? 'on' : ''} onClick={() => setMode('password')}>
            email
          </button>
          <button type="button" className={mode === 'key' ? 'on' : ''} onClick={() => setMode('key')}>
            admin key
          </button>
        </div>
        {mode === 'password' ? (
          <>
            <label>
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
            </label>
            <label>
              Password
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
          </>
        ) : (
          <label>
            Admin API key
            <input type="password" value={key} onChange={(e) => setKey(e.target.value)} required autoFocus />
            <span className="hint">The ADMIN_API_KEY value from the server's .env file.</span>
          </label>
        )}
        {failure && <p className="error">{failure}</p>}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'signing in…' : 'sign in'}
        </button>
      </form>
    </div>
  );
};

/* ------------------------------------------------------------- new project */
const NewProjectForm: React.FC<{ onCreate: (project: NewProject) => Promise<boolean>; onClose?: () => void }> = ({
  onCreate,
  onClose,
}) => {
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [source, setSource] = useState<'empty' | 'url' | 'path'>('empty');
  const [location, setLocation] = useState('');
  const [testCommand, setTestCommand] = useState('');
  const [engine, setEngine] = useState('');
  const [developers, setDevelopers] = useState(2);
  const [requireApproval, setRequireApproval] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    const created = await onCreate({
      name: name.trim(),
      goal: goal.trim(),
      repo_url: source === 'url' ? location.trim() : undefined,
      local_path: source === 'path' ? location.trim() : undefined,
      test_command: testCommand.trim() || undefined,
      engine,
      developers,
      require_approval: requireApproval,
    });
    setBusy(false);
    if (created && onClose) onClose();
  };

  return (
    <form className="card new-project" onSubmit={submit}>
      <h2>New project</h2>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} required maxLength={256} autoFocus />
      </label>
      <label>
        What should the team build or change?
        <textarea value={goal} onChange={(e) => setGoal(e.target.value)} required minLength={10} rows={5} />
      </label>
      <label>
        Code to work on
        <select value={source} onChange={(e) => setSource(e.target.value as typeof source)}>
          <option value="empty">Start a new empty repository</option>
          <option value="path">A git repository on this computer</option>
          <option value="url">A git repository URL (https)</option>
        </select>
      </label>
      {source !== 'empty' && (
        <label>
          {source === 'url' ? 'Repository URL' : 'Folder path'}
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder={source === 'url' ? 'https://github.com/you/repo.git' : 'D:\\code\\my-repo'}
            required
          />
          <span className="hint">The repository is cloned; your original is never changed.</span>
        </label>
      )}
      <label>
        Test command (optional)
        <input value={testCommand} onChange={(e) => setTestCommand(e.target.value)} placeholder="python -m pytest -q" />
        <span className="hint">QA runs this after every change. Leave empty to let the manager propose one.</span>
      </label>
      <div className="row">
        <label>
          Engine
          <select value={engine} onChange={(e) => setEngine(e.target.value)}>
            <option value="">Server default</option>
            <option value="agy">Antigravity CLI</option>
            <option value="loop">API key (Groq / OpenAI)</option>
          </select>
        </label>
        <label>
          Developers
          <select value={developers} onChange={(e) => setDevelopers(Number(e.target.value))}>
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="check">
        <input type="checkbox" checked={requireApproval} onChange={(e) => setRequireApproval(e.target.checked)} />
        Ask for my approval before each ticket is merged
      </label>
      <div className="row row-end">
        {onClose && (
          <button className="btn" type="button" onClick={onClose}>
            cancel
          </button>
        )}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'starting…' : 'start the team'}
        </button>
      </div>
    </form>
  );
};

/* -------------------------------------------------------------- agent card */
const Portrait: React.FC<{ member: TeamMember }> = ({ member }) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const ctx = canvas.current?.getContext('2d');
    if (ctx) drawPortrait(ctx, lookFor(member.id, member.role), member.role);
  }, [member.id, member.role]);
  return <canvas ref={canvas} width={14} height={16} className="portrait" aria-hidden />;
};

const AgentBar: React.FC<{
  project: ProjectDetail;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onAdd: () => void;
}> = ({ project, selectedId, onSelect, onAdd }) => (
  <div className="agent-bar">
    {project.team.map((member) => {
      const busy = project.is_running && member.state !== 'IDLE';
      return (
        <button
          key={member.id}
          className={`agent ${member.id === selectedId ? 'agent-selected' : ''}`}
          onClick={() => onSelect(member.id === selectedId ? null : member.id)}
        >
          <Portrait member={member} />
          <span className="agent-text">
            <span className="agent-name">
              {member.name} <span className={`pill role-${member.role.toLowerCase()}`}>{member.role.toLowerCase()}</span>
            </span>
            <span className={`agent-state ${busy ? 'agent-busy' : ''}`}>
              {busy ? member.activity || member.state.toLowerCase() : 'idle'}
            </span>
          </span>
        </button>
      );
    })}
    <button className="agent agent-add" onClick={onAdd}>
      + add agent
    </button>
  </div>
);

/* ---------------------------------------------------------- delete dialog */
const DeleteDialog: React.FC<{
  project: ProjectDetail;
  onDelete: (removeWorkspace: boolean) => Promise<boolean>;
  onClose: () => void;
}> = ({ project, onDelete, onClose }) => {
  const [removeWorkspace, setRemoveWorkspace] = useState(false);
  const [busy, setBusy] = useState(false);
  return (
    <div className="overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="card" role="dialog" aria-modal="true" aria-label="Delete project">
        <h2>Delete project</h2>
        <p>
          Delete <b>{project.name}</b>? Its tickets and activity history are removed. This cannot be undone.
        </p>
        <label className="check">
          <input type="checkbox" checked={removeWorkspace} onChange={(e) => setRemoveWorkspace(e.target.checked)} />
          Also delete the code the team wrote
        </label>
        <p className="note">
          {removeWorkspace
            ? `The folder ${project.workspace_path || '(not created yet)'} will be deleted.`
            : `The code stays on disk at ${project.workspace_path || '(not created yet)'}.`}
        </p>
        <div className="row row-end">
          <button className="btn" onClick={onClose}>
            cancel
          </button>
          <button
            className="btn btn-bad"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              const done = await onDelete(removeWorkspace);
              setBusy(false);
              if (done) onClose();
            }}
          >
            {busy ? 'deleting…' : 'delete project'}
          </button>
        </div>
      </div>
    </div>
  );
};

/* --------------------------------------------------------------------- app */
const PANEL_KEY = 'studio.panelWidth';
const PANEL_MIN = 340;
const FLOOR_MIN = 360;
const clampPanel = (width: number) =>
  Math.round(Math.max(PANEL_MIN, Math.min(width, Math.max(PANEL_MIN, window.innerWidth - FLOOR_MIN))));

export const StudioApp: React.FC = () => {
  const studio = useStudio();
  const { project } = studio;
  const [tab, setTab] = useState<Tab>(() => {
    const fromHash = window.location.hash.replace('#', '') as Tab;
    return TABS.some((t) => t.id === fromHash) ? fromHash : 'tasks';
  });
  const [creating, setCreating] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [panelWidth, setPanelWidth] = useState(() =>
    clampPanel(Number(localStorage.getItem(PANEL_KEY)) || window.innerWidth * 0.42)
  );
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    localStorage.setItem(PANEL_KEY, String(panelWidth));
  }, [panelWidth]);

  useEffect(() => {
    const onResize = () => setPanelWidth((width) => clampPanel(width));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const onMove = (event: PointerEvent) => setPanelWidth(clampPanel(window.innerWidth - event.clientX));
    const onUp = () => setDragging(false);
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
  }, [dragging]);

  const run = useCallback(
    async (action: () => Promise<unknown>) => {
      try {
        await action();
        setNotice(null);
        await studio.refresh();
        return true;
      } catch (err) {
        setNotice(err instanceof Error ? err.message : 'Something went wrong');
        return false;
      }
    },
    [studio.refresh]
  );

  const create = (draft: NewProject) =>
    run(async () => {
      const created = await api.createProject(draft);
      studio.select(created.id);
    });

  if (studio.needsLogin) return <Login onDone={studio.refresh} />;
  if (!studio.loaded) return <div className="studio studio-center"><p className="note">Loading…</p></div>;

  const header = (
    <header className="topbar">
      <span className="brand">Pixel Office</span>
      {studio.projects.length > 0 && (
        <select
          className="project-select"
          value={studio.selectedId ?? ''}
          onChange={(e) => studio.select(e.target.value)}
          aria-label="Project"
        >
          {studio.projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      )}
      <button className="btn" onClick={() => setCreating(true)}>
        + new project
      </button>
      <span className="spacer" />
      {project && <span className="pill">{project.engine === 'agy' ? 'Antigravity' : 'API key'} engine</span>}
      {project && <span className="pill mono">{(project.usage.total_tokens ?? 0).toLocaleString()} tokens</span>}
      {(credentials.token || credentials.apiKey) && (
        <button
          className="btn"
          onClick={() => {
            credentials.clear();
            studio.refresh();
          }}
        >
          sign out
        </button>
      )}
    </header>
  );

  if (!project) {
    return (
      <div className="studio">
        {header}
        {studio.error && <div className="banner banner-error">{studio.error}</div>}
        {notice && <div className="banner banner-error">{notice}</div>}
        <div className="studio-center">
          {studio.projects.length === 0 && !studio.error ? (
            <NewProjectForm onCreate={create} />
          ) : (
            <p className="note">{studio.error ? 'Waiting for the server…' : 'Loading the project…'}</p>
          )}
        </div>
      </div>
    );
  }

  const manager = project.team.find((m) => m.role === 'MANAGER');
  const approvals = project.tickets.filter((t) => t.status === 'AWAITING_APPROVAL' && !t.approval).length;
  const canStart = !project.is_running && project.status !== 'COMPLETED' && project.status !== 'WAITING_FOR_QUOTA';
  const selected = project.team.find((m) => m.id === selectedAgent);

  return (
    <div className={`studio ${dragging ? 'studio-dragging' : ''}`}>
      {header}
      {studio.error && <div className="banner banner-error">{studio.error}</div>}
      {notice && (
        <div className="banner banner-error">
          {notice}
          <button className="btn btn-small" onClick={() => setNotice(null)}>
            dismiss
          </button>
        </div>
      )}
      {project.failure_reason && project.status !== 'RUNNING' && project.status !== 'PLANNING' && (
        <div className="banner banner-warn">
          {project.status === 'WAITING_FOR_QUOTA'
            ? 'Out of model quota. The team resumes by itself when it can.'
            : `The project stopped: ${
                project.failure_reason.length > 260
                  ? project.failure_reason.slice(0, 260) + '…'
                  : project.failure_reason
              }`}
        </div>
      )}

      <main className="workspace">
        <section className="floor">
          <OfficeView
            team={project.team}
            tickets={project.tickets}
            running={project.is_running}
            selectedId={selectedAgent}
            onSelect={setSelectedAgent}
          />
          {selected && (
            <div className="agent-detail">
              <b>{selected.name}</b> · {selected.role.toLowerCase()}
              {selected.ticket_title ? ` · working on “${selected.ticket_title}”` : ' · no ticket right now'}
            </div>
          )}
          <AgentBar
            project={project}
            selectedId={selectedAgent}
            onSelect={setSelectedAgent}
            onAdd={() => setTab('team')}
          />
        </section>

        <div
          className="splitter"
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize the command center"
          aria-valuenow={panelWidth}
          aria-valuemin={PANEL_MIN}
          tabIndex={0}
          title="Drag to resize. Double-click to reset."
          onPointerDown={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDoubleClick={() => setPanelWidth(clampPanel(window.innerWidth * 0.42))}
          onKeyDown={(event) => {
            if (event.key === 'ArrowLeft') setPanelWidth((width) => clampPanel(width + 24));
            if (event.key === 'ArrowRight') setPanelWidth((width) => clampPanel(width - 24));
          }}
        />
        <aside className="command" style={{ flexBasis: panelWidth, width: panelWidth }}>
          <div className="command-head">
            <div>
              <div className="command-title">Command Center</div>
              <div className="command-sub">
                <span className={`status status-${project.status.toLowerCase()}`}>
                  {STATUS_TEXT[project.status] ?? project.status.toLowerCase()}
                </span>
                {manager?.name} runs the floor
              </div>
            </div>
            <div className="command-actions">
              {project.is_running || project.status === 'WAITING_FOR_QUOTA' ? (
                <button className="btn btn-bad" onClick={() => run(() => api.cancel(project.id))}>
                  ■ stop
                </button>
              ) : (
                <button className="btn btn-good" disabled={!canStart} onClick={() => run(() => api.start(project.id))}>
                  ▶ {project.tickets.length ? 'resume' : 'start'}
                </button>
              )}
              <button
                className="btn"
                disabled={project.is_running}
                title={project.is_running ? 'Stop the project before deleting it' : 'Delete this project'}
                onClick={() => setDeleting(true)}
              >
                delete
              </button>
            </div>
          </div>
          <p className="goal" title={project.goal}>
            {project.goal}
          </p>
          <nav className="tabs">
            {TABS.map((item) => (
              <button key={item.id} className={tab === item.id ? 'on' : ''} onClick={() => setTab(item.id)}>
                {item.label}
                {item.id === 'tasks' && approvals > 0 && <span className="badge">{approvals}</span>}
              </button>
            ))}
          </nav>
          <div className="tab-body">
            {tab === 'tasks' && <TasksTab project={project} run={run} />}
            {tab === 'activity' && <ActivityTab events={studio.events} />}
            {tab === 'ask' && <AskTab project={project} events={studio.events} run={run} />}
            {tab === 'changes' && <ChangesTab project={project} />}
            {tab === 'team' && <TeamTab project={project} run={run} />}
          </div>
        </aside>
      </main>

      {deleting && (
        <DeleteDialog
          project={project}
          onClose={() => setDeleting(false)}
          onDelete={(removeWorkspace) =>
            run(async () => {
              await api.deleteProject(project.id, removeWorkspace);
              studio.select(null);
            })
          }
        />
      )}
      {creating && (
        <div className="overlay" onClick={(e) => e.target === e.currentTarget && setCreating(false)}>
          <NewProjectForm onCreate={create} onClose={() => setCreating(false)} />
        </div>
      )}
    </div>
  );
};

export default StudioApp;
