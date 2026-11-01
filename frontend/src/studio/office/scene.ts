/* Pixel office — layout and drawing. Everything is drawn with rectangles; there are no image assets. */

import { Role, TeamMember } from '../types';

export const W = 512;
export const H = 320;
const AISLE_Y = 116;

export interface Point {
  x: number;
  y: number;
}
export interface Spot extends Point {
  aisleX: number;
  facing: 'down' | 'up';
  seated?: boolean;
}

interface Desk extends Point {
  role: Role;
}

const MANAGER_DESK: Desk = { x: 40, y: 56, role: 'MANAGER' };
const REVIEWER_DESK: Desk = { x: 392, y: 56, role: 'REVIEWER' };
const QA_DESK: Desk = { x: 452, y: 56, role: 'QA' };
const DEV_DESKS: Desk[] = [
  { x: 40, y: 164, role: 'DEVELOPER' },
  { x: 120, y: 164, role: 'DEVELOPER' },
  { x: 200, y: 164, role: 'DEVELOPER' },
  { x: 40, y: 244, role: 'DEVELOPER' },
  { x: 120, y: 244, role: 'DEVELOPER' },
  { x: 200, y: 244, role: 'DEVELOPER' },
];
const ALL_DESKS = [MANAGER_DESK, REVIEWER_DESK, QA_DESK, ...DEV_DESKS];

const seatOf = (desk: Desk): Spot => ({ x: desk.x + 8, y: desk.y + 5, aisleX: desk.x - 9, facing: 'down', seated: true });

const SHELF = { x: 296, y: 128, units: 3 };
const RIG = { x: 444, y: 212 };
const WHITEBOARD = { x: 232, y: 9 };

/* ---------------------------------------------------------------- leisure
   What free agents do in the open space. This is decided entirely in the browser from the
   clock: no model is asked anything, so it costs no tokens. */
const PING_PONG = { x: 314, y: 212 };
const CHESS = { x: 392, y: 264 };

export interface Leisure {
  spot: Spot;
  /** Shown above one player of a pair, so two bubbles do not cover the table. */
  label: string;
  game: 'pingpong' | 'chess' | 'chat' | 'meeting';
}

const LEISURE_PAIRS: { game: Leisure['game']; label: string; spots: [Spot, Spot] }[] = [
  {
    game: 'pingpong',
    label: 'playing table tennis',
    spots: [
      { x: PING_PONG.x - 8, y: PING_PONG.y + 20, aisleX: 286, facing: 'down' },
      { x: PING_PONG.x + 48, y: PING_PONG.y + 20, aisleX: 372, facing: 'down' },
    ],
  },
  {
    game: 'chess',
    label: 'playing chess',
    spots: [
      { x: CHESS.x - 8, y: CHESS.y + 14, aisleX: 372, facing: 'down' },
      { x: CHESS.x + 24, y: CHESS.y + 14, aisleX: 436, facing: 'down' },
    ],
  },
  {
    game: 'chat',
    label: '…',
    spots: [
      { x: 290, y: 290, aisleX: 286, facing: 'down' },
      { x: 304, y: 292, aisleX: 286, facing: 'down' },
    ],
  },
  {
    game: 'chat',
    label: '…',
    spots: [
      { x: 374, y: 166, aisleX: 286, facing: 'down' },
      { x: 388, y: 168, aisleX: 286, facing: 'down' },
    ],
  },
];

/* --------------------------------------------------------------- meetings
   Team meetings are also only a picture of what is going on: free agents gather at the
   meeting table. Nothing is said, so nothing is spent. */
export type MeetingKind = 'planning' | 'huddle' | 'wrapup';

const MEETING_LABEL: Record<MeetingKind, string> = {
  planning: '',
  huddle: 'team huddle',
  wrapup: 'wrap-up',
};

// Chairs around the meeting table, filled in an order that keeps neighbours (and their name
// tags) apart for as long as possible. The top-centre chair stays empty: the manager stands there.
const topSeat = (chair: number): Spot => ({ x: 208 + chair * 22, y: 60, aisleX: 172, facing: 'down', seated: true });
const bottomSeat = (chair: number): Spot => ({ x: 208 + chair * 22, y: 95, aisleX: 172, facing: 'up', seated: true });
const MEETING_SEATS: Spot[] = [
  topSeat(0), topSeat(4), bottomSeat(2), bottomSeat(0), bottomSeat(4),
  topSeat(1), topSeat(3), bottomSeat(1), bottomSeat(3),
];

/** Seat every free team member at the meeting table; the manager stands at the whiteboard. */
export function assignMeeting(free: TeamMember[], kind: MeetingKind): Map<string, Leisure> {
  const result = new Map<string, Leisure>();
  let seat = 0;
  for (const member of free) {
    if (member.role === 'MANAGER') {
      result.set(member.id, {
        spot: { x: WHITEBOARD.x + 24, y: 42, aisleX: 172, facing: 'down' },
        label: MEETING_LABEL[kind],
        game: 'meeting',
      });
    } else if (seat < MEETING_SEATS.length) {
      result.set(member.id, { spot: MEETING_SEATS[seat], label: '', game: 'meeting' });
      seat += 1;
    }
  }
  return result;
}

export const LEISURE_EPOCH_MS = 50_000;

/**
 * Pair up free team members for a break. The same epoch and the same free people always give
 * the same pairs, so the scene is stable between refreshes; a new epoch reshuffles.
 */
export function assignLeisure(free: TeamMember[], epoch: number): Map<string, Leisure> {
  const result = new Map<string, Leisure>();
  if (free.length < 2) return result;

  let seed = (epoch * 2654435761) >>> 0;
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const people = [...free].sort((a, b) => a.id.localeCompare(b.id));
  for (let i = people.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [people[i], people[j]] = [people[j], people[i]];
  }
  // Most, not all, take a break; the rest stay at their desks
  const pairs = Math.min(LEISURE_PAIRS.length, Math.max(1, Math.floor((people.length * 0.75) / 2)));
  const offset = Math.floor(random() * LEISURE_PAIRS.length);
  for (let pair = 0; pair < pairs; pair++) {
    const activity = LEISURE_PAIRS[(offset + pair) % LEISURE_PAIRS.length];
    for (let seat = 0; seat < 2; seat++) {
      const label = activity.game === 'chat' || seat === 0 ? activity.label : '';
      result.set(people[pair * 2 + seat].id, { spot: activity.spots[seat], label, game: activity.game });
    }
  }
  return result;
}

function drawPingPong(ctx: Ctx, playing: boolean, tick: number) {
  const { x, y } = PING_PONG;
  rect(ctx, '#2b2f3a', x + 3, y + 24, 2, 5);
  rect(ctx, '#2b2f3a', x + 35, y + 24, 2, 5);
  rect(ctx, '#2f6f55', x, y, 40, 24);
  rect(ctx, '#3b8a69', x + 1, y + 1, 38, 22);
  rect(ctx, '#e9f3ee', x + 1, y + 11, 38, 1);
  rect(ctx, '#e9f3ee', x, y, 40, 1);
  rect(ctx, '#e9f3ee', x, y + 23, 40, 1);
  rect(ctx, '#dfe6ea', x + 19, y - 2, 2, 27); // net
  if (playing) {
    const phase = (tick % 56) / 56;
    const travel = phase < 0.5 ? phase * 2 : 2 - phase * 2;
    const ballX = x + 3 + travel * 33;
    const ballY = y + 10 + Math.sin(tick / 11) * 5 - Math.abs(Math.sin(phase * Math.PI * 2)) * 4;
    rect(ctx, '#fff7d6', ballX, ballY, 2, 2);
  } else {
    rect(ctx, '#c4574f', x + 5, y + 6, 4, 4); // paddles left on the table
    rect(ctx, '#4f7cc4', x + 30, y + 14, 4, 4);
  }
}

function drawChess(ctx: Ctx, playing: boolean, tick: number) {
  const { x, y } = CHESS;
  rect(ctx, '#8f6839', x + 2, y + 14, 2, 5);
  rect(ctx, '#8f6839', x + 12, y + 14, 2, 5);
  rect(ctx, '#c9a26b', x, y, 16, 15);
  for (let row = 0; row < 4; row++) {
    for (let column = 0; column < 4; column++) {
      rect(ctx, (row + column) % 2 ? '#3d4150' : '#f4f1ea', x + 2 + column * 3, y + 2 + row * 3, 3, 3);
    }
  }
  const move = playing ? Math.floor(tick / 90) % 4 : 0;
  rect(ctx, '#c4574f', x + 3 + move * 3, y + 3, 1, 1);
  rect(ctx, '#4f7cc4', x + 12 - move * 3, y + 12, 1, 1);
  rect(ctx, '#c4574f', x + 9, y + 6, 1, 1);
  rect(ctx, '#4f7cc4', x + 6, y + 9, 1, 1);
}

export function deskFor(member: TeamMember, team: TeamMember[]): Desk {
  if (member.role === 'MANAGER') return MANAGER_DESK;
  if (member.role === 'REVIEWER') return REVIEWER_DESK;
  if (member.role === 'QA') return QA_DESK;
  const developers = team.filter((m) => m.role === 'DEVELOPER');
  return DEV_DESKS[Math.max(0, developers.findIndex((m) => m.id === member.id)) % DEV_DESKS.length];
}

/** Where a team member should be, given what the API says they are doing. */
export function spotFor(
  member: TeamMember,
  team: TeamMember[],
  leisure?: Map<string, Leisure>
): { spot: Spot; typing: boolean } {
  const desk = deskFor(member, team);
  const seat = seatOf(desk);
  if (member.state === 'IDLE') return { spot: leisure?.get(member.id)?.spot ?? seat, typing: false };

  const activity = member.activity.toLowerCase();
  const index = team.findIndex((m) => m.id === member.id);
  if (/^(reading|looking|searching|fetching)/.test(activity)) {
    const x = SHELF.x + 10 + (index % 4) * 16;
    return { spot: { x, y: SHELF.y + 40, aisleX: SHELF.x - 10, facing: 'up' }, typing: false };
  }
  if (member.role === 'QA' && activity.includes('test')) {
    return { spot: { x: RIG.x - 10, y: RIG.y + 44, aisleX: RIG.x - 8, facing: 'up' }, typing: false };
  }
  if (member.role === 'MANAGER' && (member.state === 'THINKING' || activity.includes('planning'))) {
    return { spot: { x: WHITEBOARD.x + 24, y: 42, aisleX: 172, facing: 'up' }, typing: false };
  }
  return { spot: seat, typing: true };
}

export function pathTo(from: Point, fromAisleX: number, target: Spot): Point[] {
  const points: Point[] = [
    { x: fromAisleX, y: from.y },
    { x: fromAisleX, y: AISLE_Y },
    { x: target.aisleX, y: AISLE_Y },
    { x: target.aisleX, y: target.y },
    { x: target.x, y: target.y },
  ];
  return points.filter((p, i) => {
    const previous = i === 0 ? from : points[i - 1];
    return p.x !== previous.x || p.y !== previous.y;
  });
}

/* ------------------------------------------------------------------ looks */
const HAIR = ['#2b2118', '#5a3a22', '#8a5a2b', '#d9b36c', '#1c1c24', '#7a2f2f', '#b0b0b8', '#3d2b56'];
const SKIN = ['#f1c9a5', '#e0ac7e', '#c68a5c', '#8d5a3b', '#f6d7bd'];
const SHIRT = ['#4f7cc4', '#c4574f', '#4fa37a', '#c49a4f', '#8a5fc4', '#4fb3c4', '#c44f93', '#6b7a8c'];

export interface Look {
  hair: string;
  skin: string;
  shirt: string;
  long: boolean;
}

export function lookFor(id: string, role: Role): Look {
  let hash = 7;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  return {
    hair: HAIR[hash % HAIR.length],
    skin: SKIN[(hash >>> 3) % SKIN.length],
    shirt: role === 'MANAGER' ? '#39404f' : SHIRT[(hash >>> 6) % SHIRT.length],
    long: ((hash >>> 9) & 1) === 1,
  };
}

type Ctx = CanvasRenderingContext2D;
const rect = (ctx: Ctx, color: string, x: number, y: number, w: number, h: number) => {
  ctx.fillStyle = color;
  ctx.fillRect(Math.round(x), Math.round(y), w, h);
};

export function drawPerson(
  ctx: Ctx,
  x: number,
  feetY: number,
  look: Look,
  role: Role,
  options: { facing: 'down' | 'up'; step: number; seated: boolean; typing: boolean; tick: number }
) {
  const top = feetY - 19;
  const left = x - 5;
  const bob = options.seated && options.typing ? (Math.floor(options.tick / 14) % 2) : 0;

  // shadow
  if (!options.seated) rect(ctx, 'rgba(0,0,0,0.18)', left, feetY - 1, 10, 2);
  // legs
  if (!options.seated) {
    const stride = options.step === 1 ? 1 : options.step === 2 ? -1 : 0;
    rect(ctx, '#2c3240', left + 2, feetY - 6 + Math.max(0, stride), 2, 6 - Math.max(0, stride));
    rect(ctx, '#2c3240', left + 6, feetY - 6 + Math.max(0, -stride), 2, 6 - Math.max(0, -stride));
  }
  // body
  rect(ctx, look.shirt, left + 1, top + 8 + bob, 8, 6);
  rect(ctx, look.shirt, left, top + 9 + bob, 1, 4);
  rect(ctx, look.shirt, left + 9, top + 9 + bob, 1, 4);
  rect(ctx, look.skin, left, top + 13 + bob, 1, 1);
  rect(ctx, look.skin, left + 9, top + 13 + bob, 1, 1);
  if (role === 'MANAGER' && options.facing === 'down') {
    rect(ctx, '#e8e4da', left + 4, top + 8 + bob, 2, 2);
    rect(ctx, '#b3413a', left + 4, top + 10 + bob, 2, 3);
  }
  // head
  rect(ctx, look.skin, left + 1, top + 2 + bob, 8, 6);
  rect(ctx, look.hair, left + 1, top + bob, 8, 3);
  rect(ctx, look.hair, left, top + 1 + bob, 1, look.long ? 7 : 3);
  rect(ctx, look.hair, left + 9, top + 1 + bob, 1, look.long ? 7 : 3);
  if (options.facing === 'up') {
    rect(ctx, look.hair, left + 1, top + 2 + bob, 8, look.long ? 6 : 4);
  } else {
    rect(ctx, '#20232b', left + 3, top + 4 + bob, 1, 2);
    rect(ctx, '#20232b', left + 6, top + 4 + bob, 1, 2);
    if (role === 'REVIEWER') {
      // glasses
      rect(ctx, '#20232b', left + 2, top + 4 + bob, 3, 1);
      rect(ctx, '#20232b', left + 5, top + 4 + bob, 3, 1);
    }
  }
}

function drawDesk(ctx: Ctx, desk: Desk, occupied: boolean, screenOn: boolean, tick: number) {
  // chair behind the desk
  rect(ctx, '#6b5a4a', desk.x + 3, desk.y - 8, 10, 12);
  rect(ctx, '#7d6a57', desk.x + 4, desk.y - 7, 8, 9);
  // desk top and front
  rect(ctx, '#d2ab72', desk.x, desk.y + 3, 34, 9);
  rect(ctx, '#e0bd86', desk.x, desk.y + 3, 34, 2);
  rect(ctx, '#a67c48', desk.x, desk.y + 12, 34, 5);
  rect(ctx, '#8f6839', desk.x, desk.y + 16, 34, 1);
  rect(ctx, '#8f6839', desk.x + 1, desk.y + 17, 2, 3);
  rect(ctx, '#8f6839', desk.x + 31, desk.y + 17, 2, 3);
  // monitor
  rect(ctx, '#2b2f3a', desk.x + 18, desk.y - 5, 13, 10);
  rect(ctx, screenOn ? '#123a4d' : '#3b4252', desk.x + 19, desk.y - 4, 11, 8);
  if (screenOn) {
    const scroll = Math.floor(tick / 10) % 4;
    for (let line = 0; line < 3; line++) {
      const width = 3 + ((line * 5 + scroll * 3) % 7);
      rect(ctx, line === scroll % 3 ? '#9be7ff' : '#4fc3e8', desk.x + 20, desk.y - 3 + line * 2, width, 1);
    }
  }
  rect(ctx, '#2b2f3a', desk.x + 23, desk.y + 5, 3, 2);
  // keyboard and a mug where someone works
  rect(ctx, '#e9e6df', desk.x + 4, desk.y + 7, 10, 3);
  if (occupied) {
    rect(ctx, '#f4f1ea', desk.x + 29, desk.y + 7, 3, 3);
    rect(ctx, '#6b4a2b', desk.x + 30, desk.y + 7, 1, 1);
  }
}

function drawPlant(ctx: Ctx, x: number, y: number) {
  rect(ctx, '#b0623e', x + 2, y + 8, 6, 5);
  rect(ctx, '#3f8f5a', x + 1, y + 2, 8, 7);
  rect(ctx, '#56a86f', x + 3, y, 4, 5);
  rect(ctx, '#2f7347', x + 4, y + 4, 2, 4);
}

function drawFloor(ctx: Ctx) {
  for (let ty = 0; ty < H / 16; ty++) {
    for (let tx = 0; tx < W / 16; tx++) {
      rect(ctx, (tx + ty) % 2 === 0 ? '#8fa59c' : '#879d94', tx * 16, ty * 16, 16, 16);
      rect(ctx, '#9db3aa', tx * 16 + 7, ty * 16 + 7, 2, 2);
    }
  }
}

function drawWalls(ctx: Ctx) {
  const wall = '#3d4150';
  const face = '#b5b0bf';
  const trim = '#8e889c';
  // top wall with face
  rect(ctx, face, 0, 0, W, 22);
  rect(ctx, trim, 0, 20, W, 2);
  rect(ctx, wall, 0, 0, W, 4);
  // sides and bottom
  rect(ctx, wall, 0, 0, 4, H);
  rect(ctx, wall, W - 4, 0, 4, H);
  rect(ctx, wall, 0, H - 4, W, 4);
  rect(ctx, '#8fa59c', 236, H - 4, 40, 4); // entrance

  // room partitions (short walls with openings, so walking paths stay clear)
  const partition = (x: number, y: number, w: number, h: number) => {
    rect(ctx, face, x, y, w, h);
    rect(ctx, wall, x, y, w, 3);
    rect(ctx, trim, x, y + h - 2, w, 2);
  };
  partition(140, 22, 5, 62);
  partition(366, 22, 5, 62);
  partition(4, 96, 20, 12);
  partition(60, 96, 85, 12);
  partition(196, 96, 175, 12);
  partition(410, 96, 20, 12);
  partition(470, 96, 38, 12);

  // windows
  for (const x of [84, 300, 330]) {
    rect(ctx, '#5b6478', x, 5, 24, 13);
    rect(ctx, '#bfe3f2', x + 1, 6, 10, 11);
    rect(ctx, '#bfe3f2', x + 13, 6, 10, 11);
    rect(ctx, '#e4f4fb', x + 2, 7, 3, 3);
  }
  // wall clock
  rect(ctx, '#3d4150', 14, 6, 11, 11);
  rect(ctx, '#f4f1ea', 15, 7, 9, 9);
  rect(ctx, '#b3413a', 19, 9, 1, 3);
  rect(ctx, '#3d4150', 19, 11, 3, 1);
  // whiteboard in the meeting room
  rect(ctx, '#6f7384', WHITEBOARD.x, WHITEBOARD.y - 4, 50, 15);
  rect(ctx, '#f7f5ef', WHITEBOARD.x + 1, WHITEBOARD.y - 3, 48, 13);
  rect(ctx, '#4f7cc4', WHITEBOARD.x + 4, WHITEBOARD.y, 14, 1);
  rect(ctx, '#c4574f', WHITEBOARD.x + 4, WHITEBOARD.y + 3, 22, 1);
  rect(ctx, '#4fa37a', WHITEBOARD.x + 4, WHITEBOARD.y + 6, 9, 1);
  rect(ctx, '#e3c94f', WHITEBOARD.x + 34, WHITEBOARD.y - 1, 6, 6);
  rect(ctx, '#e89a4f', WHITEBOARD.x + 41, WHITEBOARD.y + 3, 6, 6);
}

function drawMeetingTable(ctx: Ctx) {
  const x = 196;
  const y = 58;
  for (let i = 0; i < 5; i++) {
    rect(ctx, '#7a3048', x + 6 + i * 22, y - 9, 12, 10);
    rect(ctx, '#93405b', x + 7 + i * 22, y - 8, 10, 7);
  }
  rect(ctx, '#c9a26b', x, y, 120, 24);
  rect(ctx, '#dab985', x, y, 120, 3);
  rect(ctx, '#a47c48', x, y + 24, 120, 5);
  for (let i = 0; i < 5; i++) {
    rect(ctx, '#7a3048', x + 6 + i * 22, y + 26, 12, 9);
    rect(ctx, '#93405b', x + 7 + i * 22, y + 27, 10, 6);
  }
  drawPlant(ctx, x + 54, y + 4);
}

function drawShelf(ctx: Ctx) {
  const colors = ['#c4574f', '#4f7cc4', '#e3c94f', '#4fa37a', '#8a5fc4', '#e89a4f'];
  for (let unit = 0; unit < SHELF.units; unit++) {
    const x = SHELF.x + unit * 24;
    rect(ctx, '#7a5a35', x, SHELF.y - 6, 22, 30);
    rect(ctx, '#5f4526', x, SHELF.y - 6, 22, 2);
    for (let row = 0; row < 3; row++) {
      rect(ctx, '#4a351d', x + 2, SHELF.y - 3 + row * 9, 18, 7);
      for (let book = 0; book < 6; book++) {
        const color = colors[(unit * 2 + row * 3 + book) % colors.length];
        const height = 5 + ((unit + row + book) % 2);
        rect(ctx, color, x + 3 + book * 3, SHELF.y + 4 - height + row * 9, 2, height);
      }
    }
  }
}

function drawRig(ctx: Ctx, running: boolean, tick: number) {
  for (let i = 0; i < 2; i++) {
    const x = RIG.x + i * 24;
    rect(ctx, '#3a3f4c', x, RIG.y, 22, 40);
    rect(ctx, '#4a5060', x + 1, RIG.y + 1, 20, 38);
    for (let row = 0; row < 6; row++) {
      rect(ctx, '#2b2f3a', x + 3, RIG.y + 4 + row * 6, 16, 4);
      const lit = running ? (Math.floor(tick / 6) + row + i) % 3 !== 0 : row === 0;
      rect(ctx, lit ? (running ? '#6ee787' : '#4fa37a') : '#565d6e', x + 4, RIG.y + 5 + row * 6, 2, 2);
      rect(ctx, running && (Math.floor(tick / 9) + row) % 2 ? '#f0c14a' : '#565d6e', x + 8, RIG.y + 5 + row * 6, 2, 2);
    }
  }
}

function drawKitchen(ctx: Ctx) {
  // counter
  rect(ctx, '#d8d2c4', 376, 130, 48, 12);
  rect(ctx, '#bdb6a6', 376, 142, 48, 6);
  // coffee machine
  rect(ctx, '#3a3f4c', 380, 118, 14, 16);
  rect(ctx, '#b3413a', 382, 120, 10, 3);
  rect(ctx, '#f4f1ea', 385, 128, 4, 4);
  // water cooler
  rect(ctx, '#bfe3f2', 404, 112, 10, 12);
  rect(ctx, '#e9e6df', 403, 124, 12, 14);
  rect(ctx, '#4f7cc4', 406, 128, 2, 2);
}

export interface Actor {
  member: TeamMember;
  look: Look;
  x: number;
  y: number;
  facing: 'down' | 'up';
  seated: boolean;
  typing: boolean;
  step: number;
}

/** A game is only animated once both players are standing at the table. */
function bothArrived(actors: Actor[], spots: [Spot, Spot]): boolean {
  return spots.every((spot) => actors.some((a) => Math.abs(a.x - spot.x) < 1 && Math.abs(a.y - spot.y) < 1));
}

export function drawScene(ctx: Ctx, actors: Actor[], team: TeamMember[], tick: number, selectedId: string | null) {
  ctx.imageSmoothingEnabled = false;
  drawFloor(ctx);
  drawWalls(ctx);
  drawKitchen(ctx);
  drawShelf(ctx);

  const occupied = new Map<Desk, Actor | undefined>();
  for (const actor of actors) occupied.set(deskFor(actor.member, team), actor);

  const qa = actors.find((a) => a.member.role === 'QA');
  const testing = !!qa && qa.member.state !== 'IDLE' && qa.member.activity.toLowerCase().includes('test');

  type Drawable = { y: number; draw: () => void };
  const drawables: Drawable[] = [
    { y: 58 + 30, draw: () => drawMeetingTable(ctx) },
    { y: RIG.y + 40, draw: () => drawRig(ctx, testing, tick) },
    { y: PING_PONG.y + 24, draw: () => drawPingPong(ctx, bothArrived(actors, LEISURE_PAIRS[0].spots), tick) },
    { y: CHESS.y + 16, draw: () => drawChess(ctx, bothArrived(actors, LEISURE_PAIRS[1].spots), tick) },
    { y: 110, draw: () => drawPlant(ctx, 150, 84) },
    { y: 300, draw: () => drawPlant(ctx, 10, 296) },
    { y: 300, draw: () => drawPlant(ctx, 490, 296) },
  ];
  for (const desk of ALL_DESKS) {
    const owner = occupied.get(desk);
    const screenOn = !!owner && owner.seated && owner.typing;
    drawables.push({ y: desk.y + 16, draw: () => drawDesk(ctx, desk, !!owner, screenOn, tick) });
  }
  for (const actor of actors) {
    drawables.push({
      y: actor.y,
      draw: () => {
        if (actor.member.id === selectedId) {
          rect(ctx, '#ffe27a', actor.x - 7, actor.y - 21, 14, 1);
          rect(ctx, '#ffe27a', actor.x - 7, actor.y, 14, 1);
          rect(ctx, '#ffe27a', actor.x - 7, actor.y - 21, 1, 22);
          rect(ctx, '#ffe27a', actor.x + 6, actor.y - 21, 1, 22);
        }
        drawPerson(ctx, actor.x, actor.y, actor.look, actor.member.role, {
          facing: actor.facing,
          step: actor.step,
          seated: actor.seated,
          typing: actor.typing,
          tick,
        });
      },
    });
  }
  drawables.sort((a, b) => a.y - b.y);
  for (const item of drawables) item.draw();
}

export function drawPortrait(ctx: Ctx, look: Look, role: Role) {
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, 14, 16);
  drawPerson(ctx, 7, 21, look, role, { facing: 'down', step: 0, seated: true, typing: false, tick: 0 });
}
