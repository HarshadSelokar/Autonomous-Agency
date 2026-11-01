/* Pixel office — canvas animation plus a DOM overlay for name tags and speech bubbles. */

import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { TeamMember, Ticket } from '../types';
import {
  Actor,
  H,
  LEISURE_EPOCH_MS,
  Leisure,
  MeetingKind,
  Point,
  W,
  assignLeisure,
  assignMeeting,
  drawScene,
  lookFor,
  pathTo,
  spotFor,
} from './scene';

const SPEED = 46; // pixels per second
const ROLE_SIGIL: Record<string, string> = { MANAGER: '★', DEVELOPER: '>', QA: '$', REVIEWER: '@' };

interface Motion {
  x: number;
  y: number;
  aisleX: number;
  path: Point[];
  targetKey: string;
  facing: 'down' | 'up';
  seated: boolean;
  typing: boolean;
  walked: number;
}

const HUDDLE_MS = 20_000;
const WRAPUP_MS = 30_000;

interface Props {
  team: TeamMember[];
  tickets: Ticket[];
  status: string;
  running: boolean;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

const needsApproval = (member: TeamMember, tickets: Ticket[]) =>
  member.role === 'MANAGER' && tickets.some((t) => t.status === 'AWAITING_APPROVAL' && !t.approval);

function bubbleFor(member: TeamMember, tickets: Ticket[], running: boolean, leisure: Map<string, Leisure>): string {
  if (needsApproval(member, tickets)) return 'needs your approval';
  const pastime = member.state === 'IDLE' ? leisure.get(member.id) : undefined;
  if (pastime) return pastime.label; // empty for people seated in a meeting
  if (!running) return '';
  if (member.state === 'IDLE') return 'awaiting';
  return member.activity || member.state.toLowerCase();
}

export const OfficeView: React.FC<Props> = ({ team, tickets, status, running, selectedId, onSelect }) => {
  const frame = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const motions = useRef(new Map<string, Motion>());
  const tags = useRef(new Map<string, HTMLDivElement>());
  // Free agents take breaks together. Purely cosmetic and decided here, from the clock.
  const [epoch, setEpoch] = useState(() => Math.floor(Date.now() / LEISURE_EPOCH_MS));
  useEffect(() => {
    const timer = window.setInterval(() => setEpoch(Math.floor(Date.now() / LEISURE_EPOCH_MS)), 5000);
    return () => window.clearInterval(timer);
  }, []);
  // Meetings: the whole time the manager is planning, a short huddle when a ticket gets
  // blocked, and a wrap-up when the project ends. Timed here, while this page is open.
  const [timedMeeting, setTimedMeeting] = useState<MeetingKind | null>(null);
  const freeKey = (running || timedMeeting)
    ? team
        .filter((m) => m.state === 'IDLE' && !needsApproval(m, tickets))
        .map((m) => m.id)
        .join(',')
    : '';
  const blocked = tickets.filter((t) => t.status === 'BLOCKED').length;
  const seen = useRef({ status, blocked });
  useEffect(() => {
    const before = seen.current;
    seen.current = { status, blocked };
    let kind: MeetingKind | null = null;
    if (before.status !== status && (status === 'COMPLETED' || status === 'NEEDS_ATTENTION')) kind = 'wrapup';
    else if (blocked > before.blocked && running) kind = 'huddle';
    if (!kind) return;
    setTimedMeeting(kind);
    const timer = window.setTimeout(() => setTimedMeeting(null), kind === 'wrapup' ? WRAPUP_MS : HUDDLE_MS);
    return () => window.clearTimeout(timer);
  }, [status, blocked, running]);
  const meeting: MeetingKind | null = running && status === 'PLANNING' ? 'planning' : timedMeeting;

  const leisure = useMemo(
    () => {
      const freeIds = freeKey ? freeKey.split(',') : [];
      const free = team.filter((m) => freeIds.includes(m.id));
      return meeting ? assignMeeting(free, meeting) : assignLeisure(free, epoch);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [freeKey, epoch, meeting]
  );

  const latest = useRef({ team, selectedId, leisure });
  latest.current = { team, selectedId, leisure };
  const [scale, setScale] = useState(2);
  const scaleRef = useRef(scale);
  scaleRef.current = scale;

  useLayoutEffect(() => {
    const element = frame.current;
    if (!element) return;
    const fit = () => {
      const raw = Math.min(element.clientWidth / W, element.clientHeight / H);
      setScale(Math.max(1, Math.floor(raw * 4) / 4));
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const ctx = canvas.current?.getContext('2d');
    if (!ctx) return;
    let raf = 0;
    let previous = performance.now();
    let tick = 0;

    const loop = (now: number) => {
      const dt = Math.min(0.1, (now - previous) / 1000);
      previous = now;
      tick += 1;
      const { team: members, selectedId: selected, leisure: pastimes } = latest.current;

      const alive = new Set(members.map((m) => m.id));
      for (const id of motions.current.keys()) if (!alive.has(id)) motions.current.delete(id);

      const actors: Actor[] = members.map((member) => {
        const { spot, typing } = spotFor(member, members, pastimes);
        const key = `${spot.x},${spot.y}`;
        let motion = motions.current.get(member.id);
        if (!motion) {
          motion = {
            x: spot.x, y: spot.y, aisleX: spot.aisleX, path: [], targetKey: key,
            facing: spot.facing, seated: !!spot.seated, typing, walked: 0,
          };
          motions.current.set(member.id, motion);
        } else if (motion.targetKey !== key) {
          motion.path = pathTo(motion, motion.aisleX, spot);
          motion.targetKey = key;
          motion.aisleX = spot.aisleX;
          motion.seated = false;
        }

        let budget = SPEED * dt;
        while (budget > 0 && motion.path.length) {
          const next = motion.path[0];
          const dx = next.x - motion.x;
          const dy = next.y - motion.y;
          const distance = Math.abs(dx) + Math.abs(dy);
          if (distance <= budget) {
            motion.x = next.x;
            motion.y = next.y;
            motion.path.shift();
            budget -= distance;
          } else {
            motion.x += Math.sign(dx) * Math.min(Math.abs(dx), budget);
            motion.y += dx === 0 ? Math.sign(dy) * budget : 0;
            if (dy !== 0 && dx === 0) motion.facing = dy < 0 ? 'up' : 'down';
            else motion.facing = 'down';
            budget = 0;
          }
          motion.walked += 1;
        }
        const walking = motion.path.length > 0;
        if (!walking) {
          motion.facing = spot.facing;
          motion.seated = !!spot.seated;
        }
        motion.typing = typing && !walking;

        return {
          member,
          look: lookFor(member.id, member.role),
          x: motion.x,
          y: motion.y,
          facing: motion.facing,
          seated: motion.seated,
          typing: motion.typing,
          step: walking ? 1 + (Math.floor(motion.walked / 6) % 2) : 0,
        };
      });

      drawScene(ctx, actors, members, tick, selected);

      for (const actor of actors) {
        const tag = tags.current.get(actor.member.id);
        if (tag) tag.style.transform = `translate(${actor.x * scaleRef.current}px, ${actor.y * scaleRef.current}px)`;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / scale;
    const y = (event.clientY - bounds.top) / scale;
    let hit: string | null = null;
    for (const [id, motion] of motions.current) {
      if (Math.abs(motion.x - x) < 9 && y > motion.y - 22 && y < motion.y + 4) hit = id;
    }
    onSelect(hit);
  };

  return (
    <div className="office-frame" ref={frame}>
      <div className="office-stage" style={{ width: W * scale, height: H * scale }}>
        <canvas
          ref={canvas}
          width={W}
          height={H}
          onClick={handleClick}
          style={{ width: W * scale, height: H * scale }}
          aria-label="Office floor with the team at work"
        />
        {team.map((member) => {
          const bubble = bubbleFor(member, tickets, running, leisure);
          return (
            <div
              key={member.id}
              className="office-tag"
              ref={(node) => {
                if (node) tags.current.set(member.id, node);
                else tags.current.delete(member.id);
              }}
            >
              {bubble && (
                <div className="bubble" style={{ bottom: 22 * scale }}>
                  <span className="sigil">{ROLE_SIGIL[member.role]}</span> {bubble}
                </div>
              )}
              <div className={`nametag ${member.id === selectedId ? 'selected' : ''}`} style={{ top: 2 * scale }}>
                {member.name}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
