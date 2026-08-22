/* ── Shared constants: site layout + status→colour mapping ──
 *
 * SITE PLAN (top-down; +x = east, +z = south). Zones are laid out in bands
 * along z so traffic lanes and standing areas never overlap:
 *
 *   z = -22  delayed shoulder
 *   z = -14  holding lane (waiting for a berth)
 *   z =  -6 … +6   MAIN ROAD  (gate → apron; inbound north half, outbound south)
 *   z = +12 … +35  PARKING YARD
 *
 *   x:  -40 ────────────────── -6      4       8 ─────────── 52
 *       GATE     ROAD / YARD         APRON  DOCK WALL   WAREHOUSE
 *
 * backend/app/seed.py mirrors these numbers — change both together.
 */

export const SITE = {
  gate: { x: -40, z: 0 },

  /** Main road corridor. Nothing may be parked inside this band. */
  road: { xStart: -40, xEnd: -6, z: 0, width: 12 },

  /** Parking sits entirely south of the road corridor. */
  parking: {
    xStart: -40,
    zStart: 12,
    cols: 5,
    rows: 4,
    padW: 5,
    padD: 6,
    gapX: 1.5,
    gapZ: 1.5,
  },

  /** Trucks berth here, nose pointing east at the dock wall. */
  apron: { x: 4, zStart: -20, slotDepth: 4.5, slots: 10 },

  dockWall: { x: 8, zMin: -24, zMax: 24, height: 10 },

  warehouse: { xMin: 8, xMax: 52, zMin: -24, zMax: 24, height: 11 },

  /** Aisles run north–south inside the building; bays extend along +z. */
  aisle: { xStart: 14, spacing: 8, z: -20, bayDepth: 4, baysPerAisle: 10, count: 5 },

  ground: { size: 160 },
} as const;

/** z-centre of a dock berth by its position_index. */
export const dockZ = (slot: number): number =>
  SITE.apron.zStart + slot * SITE.apron.slotDepth;

/** Grid position of a parking slot by its position_index. */
export function parkingPosition(index: number): [number, number] {
  const { xStart, zStart, cols, padW, padD, gapX, gapZ } = SITE.parking;
  const col = index % cols;
  const row = Math.floor(index / cols);
  return [xStart + col * (padW + gapX), zStart + row * (padD + gapZ)];
}

// ── Palette (mirrors the CSS custom properties in index.css) ──────────────

export const COLORS = {
  cyan: '#00d4ff',
  blue: '#3b82f6',
  lime: '#84cc16',
  green: '#22c55e',
  amber: '#f59e0b',
  red: '#ef4444',
  purple: '#a855f7',
  slate: '#6b7490',
} as const;

/** Structural material colours, per theme. Status colours stay constant so
 *  a CRITICAL bay reads the same in either mode. */
export interface SceneTheme {
  background: string;
  fog: string;
  floor: string;
  apron: string;
  yard: string;
  road: string;
  wall: string;
  frame: string;
  rackUpright: string;
  grid: string;
  gridSection: string;
  label: string;
  lane: string;
  trailer: string;
  ambient: number;
  hemi: number;
  sun: number;
  fill: number;
  emissive: number;
}

export const SCENE: Record<'light' | 'dark', SceneTheme> = {
  light: {
    background: '#dfe4ec',
    fog: '#dfe4ec',
    floor: '#d5dae4',
    apron: '#c3cad6',
    yard: '#cbd1dc',
    road: '#aeb6c4',
    wall: '#eef1f6',
    frame: '#98a2b6',
    rackUpright: '#8a94aa',
    grid: '#b9c1d0',
    gridSection: '#94a0b6',
    label: '#3b4358',
    lane: '#c8cedb',
    trailer: '#aeb7c8',
    ambient: 1.0,
    hemi: 0.75,
    sun: 1.5,
    fill: 0.25,
    emissive: 0.18,
  },
  dark: {
    background: '#161a24',
    fog: '#161a24',
    floor: '#3c414f',
    apron: '#33384a',
    yard: '#343945',
    road: '#2b303c',
    wall: '#575f75',
    frame: '#7d88a3',
    rackUpright: '#6b7490',
    grid: '#454c5e',
    gridSection: '#5b6a8a',
    label: '#c3ccdf',
    lane: '#4a5163',
    trailer: '#7c869e',
    ambient: 0.75,
    hemi: 0.85,
    sun: 1.5,
    fill: 0.9,
    emissive: 0.4,
  },
};

export type BadgeTone = 'green' | 'cyan' | 'amber' | 'red' | 'lime';

/** Maps any domain status string to a badge tone used by the CSS. */
export function toneFor(status: string): BadgeTone {
  switch (status) {
    case 'AVAILABLE':
    case 'COMPLETED':
    case 'DELIVERED':
    case 'HEALTHY':
    case 'EXECUTED':
      return 'green';
    case 'LOADING':
    case 'UNLOADING':
    case 'IN_TRANSIT':
    case 'PICKING':
    case 'MOVING':
    case 'AT_DOCK':
    case 'AT_FACILITY':
    case 'PROCESSING':
    case 'VALIDATED':
      return 'cyan';
    case 'WAITING':
    case 'RESERVED':
    case 'ARRIVING':
    case 'SCHEDULED':
    case 'PENDING':
    case 'MEDIUM':
    case 'LOW':
    case 'PROPOSED':
    case 'REPLENISHMENT_REQUIRED':
      return 'amber';
    case 'DELAYED':
    case 'CRITICAL':
    case 'HIGH':
    case 'AT_RISK':
    case 'BLOCKED':
    case 'CANCELLED':
    case 'MAINTENANCE':
    case 'REJECTED':
    case 'FAILED':
      return 'red';
    default:
      return 'lime';
  }
}

/** Maps a status to a hex colour for 3D materials. */
export function colorFor(status: string): string {
  const tone = toneFor(status);
  return {
    green: COLORS.green,
    cyan: COLORS.cyan,
    amber: COLORS.amber,
    red: COLORS.red,
    lime: COLORS.lime,
  }[tone];
}

/** Severity/risk → colour, ordered by urgency. */
export function severityColor(sev: string): string {
  switch (sev) {
    case 'CRITICAL':
      return COLORS.red;
    case 'HIGH':
      return COLORS.amber;
    case 'MEDIUM':
      return COLORS.cyan;
    default:
      return COLORS.slate;
  }
}

/** Severity rank for sorting — lower is more urgent. */
export const SEVERITY_RANK: Record<string, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};
