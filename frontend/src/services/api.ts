/* ── ChainPilot API client ── */

// Relative — Vite proxies /api to the backend in dev (see vite.config.ts),
// and in production the API is served from the same origin.
// Override with VITE_API_BASE if the backend lives elsewhere.
const BASE = import.meta.env.VITE_API_BASE ?? '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json();
}

import type {
  ActionDecisionResponse,
  AgentActionItem,
  AgentInfo,
  AIQueryResponse,
  Aisle,
  Bay,
  CustomerOrder,
  Dock,
  Forklift,
  HealthSummary,
  InventoryItem,
  OperationalEvent,
  OperationalException,
  Pallet,
  ParkingSlot,
  Shipment,
  Truck,
  Warehouse,
} from '@/types/types';

export const api = {
  warehouses: () => get<Warehouse[]>('/warehouse'),
  aisles: () => get<Aisle[]>('/aisles'),
  bays: (aisleId?: number) => get<Bay[]>(aisleId != null ? `/bays?aisle_id=${aisleId}` : '/bays'),
  docks: () => get<Dock[]>('/docks'),
  parkingSlots: () => get<ParkingSlot[]>('/parking-slots'),
  trucks: () => get<Truck[]>('/trucks'),
  shipments: () => get<Shipment[]>('/shipments'),
  pallets: () => get<Pallet[]>('/pallets'),
  inventory: () => get<InventoryItem[]>('/inventory'),
  forklifts: () => get<Forklift[]>('/forklifts'),
  orders: () => get<CustomerOrder[]>('/orders'),
  events: () => get<OperationalEvent[]>('/events'),
  exceptions: () => get<OperationalException[]>('/exceptions?resolved=false'),
  health: () => get<HealthSummary>('/health'),

  // ── Agent layer ──
  aiQuery: (query: string) => post<AIQueryResponse>('/ai/query', { query }),
  agents: () => get<AgentInfo[]>('/agents'),
  actions: (status?: string) =>
    get<AgentActionItem[]>(status ? `/actions?status=${status}` : '/actions'),
  approveAction: (id: number) =>
    post<ActionDecisionResponse>(`/actions/${id}/approve`, {}),
  rejectAction: (id: number) =>
    post<ActionDecisionResponse>(`/actions/${id}/reject`, {}),
  simulate: (shipment_code: string, extra_hours = 4) =>
    post<Record<string, unknown>>('/simulate', { shipment_code, extra_hours }),
};
