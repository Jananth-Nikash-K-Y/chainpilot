/* ── Shared constants: site layout + status→colour mapping ──
 *
 * SITE PLAN (top-down; +x = east, +z = south).
 *
 *   x:  -40      -34 … -16      2       8 ──────────────── 52
 *       GATE      PARKING     APRON  DOCK WALL         WAREHOUSE
 *
 * Kept deliberately compact: the warehouse is the subject, the yard is
 * context. backend/app/seed.py mirrors these numbers — change both together.
 */

export const SITE = {
  gate: { x: -40, z: 0 },

  parking: {
    xStart: -34,
    zStart: -14,
    cols: 4,
    rows: 5,
    padW: 5,
    padD: 6,
    gapX: 1.5,
    gapZ: 1.5,
  },

  /** Trucks berth here, nose pointing east at the dock wall. */
  apron: { x: 2, zStart: -20, slotDepth: 4.5, slots: 10 },

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

/** Structural material colours, kept separate from status colours. */
export const MATERIAL = {
  floor: '#3c414f',
  apron: '#33384a',
  yard: '#343945',
  road: '#2b303c',
  wall: '#575f75',
  frame: '#7d88a3',
  rackUpright: '#6b7490',
} as const;

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
