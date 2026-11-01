/* Command Center tabs: tasks board, activity feed, ask, changes, team. */

import React, { useEffect, useRef, useState } from 'react';
import { api } from './api';
import { ActivityEvent, Changes, ProjectDetail, Role, Ticket, TicketStatus } from './types';

type Run = (action: () => Promise<unknown>) => Promise<boolean>;

const COLUMNS: { title: string; tone: string; statuses: TicketStatus[] }[] = [
  { title: 'TODO', tone: 'blue', statuses: ['TODO'] },
  { title: 'DOING', tone: 'amber', statuses: ['IN_PROGRESS', 'TESTING'] },
  { title: 'REVIEW', tone: 'violet', statuses: ['IN_REVIEW', 'AWAITING_APPROVAL'] },
  { title: 'BLOCKED', tone: 'red', statuses: ['BLOCKED'] },
  { title: 'DONE', tone: 'green', statuses: ['DONE'] },
];

const STATUS_LABEL: Record<TicketStatus, string> = {
  TODO: 'to do',
  IN_PROGRESS: 'coding',
  TESTING: 'testing',
  IN_REVIEW: 'in review',
  AWAITING_APPROVAL: 'needs you',
  DONE: 'done',
  BLOCKED: 'blocked',
};

/* ------------------------------------------------------------------- tasks */
const TicketCard: React.FC<{ ticket: Ticket; project: ProjectDetail; run: Run }> = ({ ticket, project, run }) => {
  const [open, setOpen] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState('');
  const assignee = project.team.find((m) => m.id === ticket.assignee_id);
  const waiting = ticket.status === 'AWAITING_APPROVAL' && !ticket.approval;

  return (
    <div className={`ticket ${waiting ? 'ticket-waiting' : ''}`}>
      <button className="ticket-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="ticket-number">#{ticket.sequence}</span>
        <span className="ticket-title">{ticket.title}</span>
      </button>
      <div className="ticket-meta">
        <span className={`pill pill-${ticket.status.toLowerCase()}`}>{STATUS_LABEL[ticket.status]}</span>
        {assignee && <span className="pill">{assignee.name}</span>}
        {ticket.attempts > 1 && <span className="pill">try {ticket.attempts}</span>}
        {ticket.commit_sha && <span className="pill mono">{ticket.commit_sha.slice(0, 7)}</span>}
      </div>
      {open && (
        <div className="ticket-body">
          {ticket.description && <p>{ticket.description}</p>}
          {ticket.acceptance_criteria && (
            <p>
              <b>Done when:</b> {ticket.acceptance_criteria}
            </p>
          )}
          {ticket.feedback && (
            <p className="ticket-feedback">
              <b>Latest feedback:</b> {ticket.feedback}
            </p>
          )}
        </div>
      )}
      {waiting && (
        <div className="ticket-approval">
          {!rejecting ? (
            <>
              <button className="btn btn-good" onClick={() => run(() => api.approve(project.id, ticket.id))}>
                approve
              </button>
              <button className="btn" onClick={() => setRejecting(true)}>
                send back
              </button>
            </>
          ) : (
            <form
              onSubmit={async (event) => {
                event.preventDefault();
                if (await run(() => api.reject(project.id, ticket.id, reason))) setRejecting(false);
              }}
            >
              <input
                autoFocus
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="What should change?"
              />
              <button className="btn btn-bad" type="submit" disabled={!reason.trim()}>
                send back
              </button>
              <button className="btn" type="button" onClick={() => setRejecting(false)}>
                cancel
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
};

export const TasksTab: React.FC<{ project: ProjectDetail; run: Run }> = ({ project, run }) => {
  if (!project.tickets.length) {
    return (
      <p className="empty">
        {project.is_running ? 'The manager is planning the work. Tickets appear here in a moment.' : 'No tickets yet.'}
      </p>
    );
  }
  return (
    <div className="board">
      {COLUMNS.map((column) => {
        const tickets = project.tickets.filter((t) => column.statuses.includes(t.status));
        return (
          <section key={column.title} className={`column column-${column.tone}`}>
            <header>
              <span>{column.title}</span>
              <span>{tickets.length}</span>
            </header>
            <div className="column-body">
              {tickets.length === 0 && <span className="column-empty">—</span>}
              {tickets.map((ticket) => (
                <TicketCard key={ticket.id} ticket={ticket} project={project} run={run} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
};

/* ---------------------------------------------------------------- activity */
const time = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

export const ActivityTab: React.FC<{ events: ActivityEvent[] }> = ({ events }) => {
  const end = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  useEffect(() => {
    if (pinned.current) end.current?.scrollIntoView({ block: 'end' });
  }, [events.length]);

  if (!events.length) return <p className="empty">Nothing has happened yet.</p>;
  return (
    <div
      className="feed"
      ref={box}
      onScroll={() => {
        const element = box.current;
        if (element) pinned.current = element.scrollHeight - element.scrollTop - element.clientHeight < 40;
      }}
    >
      {events.map((event) => (
        <div key={event.sequence} className={`feed-line feed-${event.kind}`}>
          <span className="feed-time">{time(event.created_at)}</span>
          <span className={`feed-actor role-${event.actor_role.toLowerCase()}`}>{event.actor_name}</span>
          <span className="feed-text">{event.summary}</span>
        </div>
      ))}
      <div ref={end} />
    </div>
  );
};

/* --------------------------------------------------------------------- ask */
// Model answers arrive as Markdown; show them as plain text without the markup characters
const plain = (text: string) => text.replace(/\*\*(.+?)\*\*/g, '$1').replace(/`([^`]+)`/g, '$1');

export const AskTab: React.FC<{ project: ProjectDetail; events: ActivityEvent[]; run: Run }> = ({ project, events, run }) => {
  const [text, setText] = useState('');
  const [asking, setAsking] = useState(false);
  const manager = project.team.find((m) => m.role === 'MANAGER');
  const thread = events.filter((e) => e.kind === 'human_message' || e.kind === 'message');
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: 'end' });
  }, [thread.length, asking]);

  const send = async (mode: 'ask' | 'tell') => {
    const message = text.trim();
    if (!message) return;
    if (mode === 'ask') setAsking(true);
    const ok = await run(() => (mode === 'ask' ? api.ask(project.id, message) : api.tell(project.id, message)));
    setAsking(false);
    if (ok) setText('');
  };

  return (
    <div className="ask">
      <div className="ask-thread">
        {!thread.length && (
          <p className="empty">
            Ask {manager?.name ?? 'the manager'} how the project is going, or give the team an instruction they will
            follow from their next step.
          </p>
        )}
        {thread.map((event) => {
          const mine = event.kind === 'human_message';
          const body = (mine ? event.detail.text : event.detail.answer) as string | undefined;
          return (
            <div key={event.sequence} className={`message ${mine ? 'message-mine' : ''}`}>
              <div className="message-who">
                {mine ? (event.detail.guidance ? 'you → team' : 'you') : event.actor_name}
              </div>
              <div className="message-text">{plain(body || event.summary)}</div>
            </div>
          );
        })}
        {asking && <div className="message"><div className="message-who">{manager?.name}</div><div className="message-text">thinking…</div></div>}
        <div ref={end} />
      </div>
      <form
        className="ask-form"
        onSubmit={(event) => {
          event.preventDefault();
          send('ask');
        }}
      >
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Type a question or an instruction…"
          rows={3}
        />
        <div className="ask-buttons">
          <button className="btn btn-primary" type="submit" disabled={!text.trim() || asking}>
            ask {manager?.name ?? 'manager'}
          </button>
          <button className="btn" type="button" disabled={!text.trim() || asking} onClick={() => send('tell')}>
            tell the team
          </button>
        </div>
      </form>
    </div>
  );
};

/* ----------------------------------------------------------------- changes */
export const ChangesTab: React.FC<{ project: ProjectDetail }> = ({ project }) => {
  const [changes, setChanges] = useState<Changes | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const done = project.tickets.filter((t) => t.status === 'DONE').length;

  useEffect(() => {
    let cancelled = false;
    api
      .changes(project.id)
      .then((result) => !cancelled && (setChanges(result), setFailure(null)))
      .catch((err) => !cancelled && setFailure(err.message));
    return () => {
      cancelled = true;
    };
  }, [project.id, done]);

  if (failure) return <p className="empty">Could not load changes: {failure}</p>;
  if (!changes) return <p className="empty">Loading…</p>;
  if (!changes.commits.length) return <p className="empty">Nothing has been merged yet.</p>;

  return (
    <div className="changes">
      <div className="changes-meta">
        <span className="pill mono">{changes.branch}</span>
        <span className="pill">{changes.commits.length} commit(s)</span>
      </div>
      <p className="changes-path">
        Workspace: <span className="mono">{project.workspace_path}</span>
      </p>
      <ul className="commits">
        {changes.commits.map((commit) => (
          <li key={commit.sha}>
            <span className="mono">{commit.sha.slice(0, 7)}</span> {commit.subject}
          </li>
        ))}
      </ul>
      <pre className="diff">
        {changes.diff.split('\n').map((line, index) => {
          const kind = line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ')
            ? 'file'
            : line.startsWith('+')
              ? 'add'
              : line.startsWith('-')
                ? 'del'
                : line.startsWith('@@')
                  ? 'hunk'
                  : '';
          return (
            <span key={index} className={kind ? `diff-${kind}` : undefined}>
              {line + '\n'}
            </span>
          );
        })}
      </pre>
    </div>
  );
};

/* -------------------------------------------------------------------- team */
const ROLE_LABEL: Record<Role, string> = { MANAGER: 'manager', DEVELOPER: 'developer', QA: 'qa', REVIEWER: 'reviewer' };

export const TeamTab: React.FC<{ project: ProjectDetail; run: Run }> = ({ project, run }) => {
  const [name, setName] = useState('');
  const [renaming, setRenaming] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const locked = project.is_running;
  const developers = project.team.filter((m) => m.role === 'DEVELOPER').length;

  return (
    <div className="team">
      {locked && (
        <p className="note">
          You can rename anyone now. Adding or removing developers needs the project to be stopped.
        </p>
      )}
      <ul className="team-list">
        {project.team.map((member) => (
          <li key={member.id}>
            {renaming === member.id ? (
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (await run(() => api.renameMember(project.id, member.id, draft))) setRenaming(null);
                }}
              >
                <input autoFocus value={draft} onChange={(event) => setDraft(event.target.value)} maxLength={64} />
                <button className="btn btn-primary" type="submit" disabled={!draft.trim()}>
                  save
                </button>
                <button className="btn" type="button" onClick={() => setRenaming(null)}>
                  cancel
                </button>
              </form>
            ) : (
              <>
                <span className="team-name">{member.name}</span>
                <span className={`pill role-${member.role.toLowerCase()}`}>{ROLE_LABEL[member.role]}</span>
                <span className="team-activity">
                  {member.state === 'IDLE' ? 'idle' : member.activity || member.state.toLowerCase()}
                </span>
                <button
                  className="btn btn-small"
                  onClick={() => {
                    setRenaming(member.id);
                    setDraft(member.name);
                  }}
                >
                  rename
                </button>
                {member.role === 'DEVELOPER' && (
                  <button
                    className="btn btn-small"
                    disabled={locked || developers <= 1}
                    onClick={() => run(() => api.removeMember(project.id, member.id))}
                  >
                    remove
                  </button>
                )}
              </>
            )}
          </li>
        ))}
      </ul>
      <form
        className="team-add"
        onSubmit={async (event) => {
          event.preventDefault();
          if (await run(() => api.addMember(project.id, name.trim(), 'DEVELOPER'))) setName('');
        }}
      >
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="New developer's name"
          maxLength={64}
          disabled={locked || developers >= 6}
        />
        <button className="btn btn-primary" type="submit" disabled={locked || !name.trim() || developers >= 6}>
          + add developer
        </button>
      </form>
      <p className="note">
        A team has one manager, one QA, one reviewer and up to six developers. Developers work tickets at the same
        time, each in their own copy of the code.
      </p>
    </div>
  );
};
