/* ── TypeScript interfaces matching backend Pydantic schemas ── */

export interface Warehouse {
  id: number;
  name: string;
  code: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  total_area_sqm?: number;
  utilization_pct: number;
}

export interface Aisle {
  id: number;
  warehouse_id: number;
  code: string;
  zone?: string;
  capacity_pct: number;
  occupied_pct: number;
  active_pick_tasks: number;
  replenishment_tasks: number;
  risk: RiskLevel;
  position_x: number;
  position_z: number;
}

export interface Bay {
  id: number;
  aisle_id: number;
  code: string;
  level: number;
  capacity: number;
  current_quantity: number;
  sku?: string;
  stock_status: StockStatus;
  last_movement?: string;
  replenishment_required: boolean;
  position_index: number;
}

export interface Dock {
  id: number;
  warehouse_id: number;
  code: string;
  status: DockStatus;
  current_truck_id?: number;
  current_shipment_id?: number;
  activity?: string;
  occupancy_start?: string;
  estimated_completion?: string;
  position_index: number;
  current_truck_code?: string;
  current_shipment_code?: string;
}

export interface ParkingSlot {
  id: number;
  warehouse_id: number;
  code: string;
  status: ParkingSlotStatus;
  vehicle_id?: string;
  arrival_time?: string;
  expected_departure?: string;
  assigned_dock?: string;
  position_index: number;
}

export interface Truck {
  id: number;
  code: string;
  carrier: string;
  status: TruckStatus;
  dock_code?: string;
  shipment_id?: number;
  eta?: string;
  load_pct: number;
  destination?: string;
  risk: RiskLevel;
  position_x: number;
  position_y: number;
  position_z: number;
  rotation_y: number;
  shipment_code?: string;
}

export interface Shipment {
  id: number;
  code: string;
  supplier_id?: number;
  direction: 'INBOUND' | 'OUTBOUND';
  status: ShipmentStatus;
  origin?: string;
  destination?: string;
  eta?: string;
  actual_arrival?: string;
  dock_code?: string;
  sku_count: number;
  weight_kg: number;
  delay_hours: number;
  risk: RiskLevel;
  supplier_name?: string;
}

export interface Pallet {
  id: number;
  code: string;
  bay_id?: number;
  sku?: string;
  quantity: number;
  max_quantity: number;
  stock_status: StockStatus;
  condition: string;
  position_x: number;
  position_y: number;
  position_z: number;
  bay_code?: string;
}

export interface InventoryItem {
  id: number;
  sku: string;
  name: string;
  category?: string;
  bay_code?: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_point: number;
  max_quantity: number;
  stock_status: StockStatus;
  days_of_coverage: number;
  supplier_id?: number;
  last_received?: string;
  last_picked?: string;
}

export interface Forklift {
  id: number;
  warehouse_id: number;
  code: string;
  activity: ForkliftActivity;
  operator?: string;
  current_aisle?: string;
  battery_pct: number;
  position_x: number;
  position_y: number;
  position_z: number;
}

export interface CustomerOrder {
  id: number;
  code: string;
  customer_name: string;
  status: OrderStatus;
  priority: string;
  total_items: number;
  total_value: number;
  currency: string;
  promised_date?: string;
  shipment_id?: number;
  risk: RiskLevel;
}

export interface OperationalEvent {
  id: number;
  event_type: string;
  entity_type: string;
  entity_code: string;
  message: string;
  severity: string;
  timestamp: string;
  metadata_json?: string;
}

export interface OperationalException {
  id: number;
  code: string;
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  title: string;
  description: string;
  entity_type: string;
  entity_code: string;
  affected_sku?: string;
  affected_orders: number;
  potential_impact: number;
  impact_currency: string;
  inventory_coverage_days?: number;
  delay_hours: number;
  recommendation?: string;
  resolved: boolean;
  position_x: number;
  position_y: number;
  position_z: number;
  created_at: string;
}

export interface HealthSummary {
  supply_chain_health: number;
  critical_exceptions: number;
  delayed_shipments: number;
  inventory_risks: number;
  dock_utilization_pct: number;
  warehouse_utilization_pct: number;
  orders_at_risk: number;
  total_trucks: number;
  active_forklifts: number;
}

// ── Agent layer ──

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  result_summary: string;
}

export interface Finding {
  headline: string;
  detail: string;
  severity: ExceptionSeverity;
  entity_type: string;
  entity_code: string;
  metrics: Record<string, unknown>;
}

export interface AgentTrace {
  agent: string;
  relevance: number;
  summary: string;
  findings: Finding[];
  tool_calls: ToolCall[];
}

export type ActionStatus =
  | 'PROPOSED' | 'VALIDATED' | 'REJECTED' | 'EXECUTED' | 'FAILED';

export interface AgentActionItem {
  id: number;
  kind: string;
  status: ActionStatus;
  proposed_by: string;
  title: string;
  rationale: string;
  entity_type: string;
  entity_code: string;
  exception_code?: string;
  projected_impact: number;
  projected_savings: number;
  confidence: number;
  validation_notes?: string;
  result_message?: string;
  created_at: string;
  decided_at?: string;
}

export interface AIQueryResponse {
  query: string;
  response: string;
  suggestions: string[];
  agents: AgentTrace[];
  actions: AgentActionItem[];
}

export interface ActionDecisionResponse {
  ok: boolean;
  message: string;
  action?: AgentActionItem;
}

export interface AgentInfo {
  name: string;
  domain: string;
}

// ── Enums ──

export type TruckStatus =
  | 'ARRIVING' | 'WAITING' | 'AT_DOCK' | 'LOADING'
  | 'UNLOADING' | 'READY_TO_DEPART' | 'DEPARTED' | 'DELAYED';

export type DockStatus =
  | 'AVAILABLE' | 'OCCUPIED' | 'LOADING' | 'UNLOADING'
  | 'RESERVED' | 'MAINTENANCE';

export type ParkingSlotStatus =
  | 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | 'WAITING' | 'MAINTENANCE';

export type StockStatus =
  | 'HEALTHY' | 'LOW' | 'CRITICAL' | 'BLOCKED'
  | 'RESERVED' | 'REPLENISHMENT_REQUIRED';

export type ForkliftActivity =
  | 'IDLE' | 'MOVING' | 'PICKING' | 'DROPPING'
  | 'REPLENISHING' | 'CHARGING';

export type ShipmentStatus =
  | 'SCHEDULED' | 'IN_TRANSIT' | 'AT_FACILITY' | 'LOADING'
  | 'UNLOADING' | 'COMPLETED' | 'DELAYED' | 'CANCELLED';

export type OrderStatus =
  | 'PENDING' | 'PROCESSING' | 'PICKING' | 'PACKED'
  | 'SHIPPED' | 'DELIVERED' | 'AT_RISK' | 'CANCELLED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ExceptionSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ExceptionCategory =
  | 'SHIPMENT_DELAY' | 'DOCK_CONGESTION' | 'INVENTORY_RISK'
  | 'SUPPLIER_RISK' | 'ORDER_AT_RISK' | 'EQUIPMENT_ISSUE';

// ── UI types ──

export type CameraView = 'overview' | 'yard' | 'warehouse' | 'aisle' | 'bay';

export interface SelectedObject {
  type: 'truck' | 'dock' | 'parking' | 'aisle' | 'bay' | 'forklift' | 'pallet' | 'shipment' | 'exception';
  id: number;
  code: string;
}
