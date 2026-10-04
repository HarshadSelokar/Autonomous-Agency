/* Pixel office — canvas animation plus a DOM overlay for name tags and speech bubbles. */

import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { TeamMember, Ticket } from '../types';
import { Actor, H, Point, W, drawScene, lookFor, pathTo, spotFor } from './scene';

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

interface Props {
  team: TeamMember[];
  tickets: Ticket[];
  running: boolean;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

function bubbleFor(member: TeamMember, tickets: Ticket[], running: boolean): string {
  if (member.role === 'MANAGER' && tickets.some((t) => t.status === 'AWAITING_APPROVAL')) {
    return 'needs your approval';
  }
  if (!running) return '';
  if (member.state === 'IDLE') return 'awaiting';
  return member.activity || member.state.toLowerCase();
}

export const OfficeView: React.FC<Props> = ({ team, tickets, running, selectedId, onSelect }) => {
  const frame = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const motions = useRef(new Map<string, Motion>());
  const tags = useRef(new Map<string, HTMLDivElement>());
  const latest = useRef({ team, selectedId });
  latest.current = { team, selectedId };
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
      const { team: members, selectedId: selected } = latest.current;

      const alive = new Set(members.map((m) => m.id));
      for (const id of motions.current.keys()) if (!alive.has(id)) motions.current.delete(id);

      const actors: Actor[] = members.map((member) => {
        const { spot, typing } = spotFor(member, members);
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
          const bubble = bubbleFor(member, tickets, running);
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
