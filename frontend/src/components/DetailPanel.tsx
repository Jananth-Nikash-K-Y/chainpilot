/* ── DetailPanel — inspector for whatever is selected in the twin ── */
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { toneFor } from '@/constants';

type Row = { label: string; value: string; badge?: string };

function fmtTime(iso?: string): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? '—'
    : d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
}

function fmtMoney(value: number, currency: string): string {
  return `${currency === 'INR' ? '₹' : ''}${value.toLocaleString()}`;
}

export function DetailPanel() {
  const selected = useUIStore((s) => s.selectedObject);
  const setSelected = useUIStore((s) => s.setSelected);
  const activePanel = useUIStore((s) => s.activePanel);
  // Select individual slices — subscribing to the whole store returns a new
  // object reference on every change and re-renders this panel constantly.
  const trucks = useDataStore((s) => s.trucks);
  const docks = useDataStore((s) => s.docks);
  const parkingSlots = useDataStore((s) => s.parkingSlots);
  const aisles = useDataStore((s) => s.aisles);
  const bays = useDataStore((s) => s.bays);
  const forklifts = useDataStore((s) => s.forklifts);
  const pallets = useDataStore((s) => s.pallets);
  const shipments = useDataStore((s) => s.shipments);
  const exceptions = useDataStore((s) => s.exceptions);
  const data = {
    trucks, docks, parkingSlots, aisles, bays,
    forklifts, pallets, shipments, exceptions,
  };

  if (!selected) return null;

  let title = selected.type.toUpperCase();
  let rows: Row[] = [];

  switch (selected.type) {
    case 'truck': {
      const t = data.trucks.find((x) => x.id === selected.id);
      if (!t) break;
      title = 'Truck';
      rows = [
        { label: 'Status', value: t.status, badge: t.status },
        { label: 'Carrier', value: t.carrier },
        { label: 'Dock', value: t.dock_code ?? '—' },
        { label: 'Shipment', value: t.shipment_code ?? '—' },
        { label: 'Load', value: `${t.load_pct.toFixed(0)}%` },
        { label: 'Destination', value: t.destination ?? '—' },
        { label: 'ETA', value: fmtTime(t.eta) },
        { label: 'Risk', value: t.risk, badge: t.risk },
      ];
      break;
    }
    case 'dock': {
      const d = data.docks.find((x) => x.id === selected.id);
      if (!d) break;
      title = 'Dock';
      rows = [
        { label: 'Status', value: d.status, badge: d.status },
        { label: 'Truck', value: d.current_truck_code ?? '—' },
        { label: 'Shipment', value: d.current_shipment_code ?? '—' },
        { label: 'Activity', value: d.activity ?? '—' },
        { label: 'Since', value: fmtTime(d.occupancy_start) },
        { label: 'Est. complete', value: fmtTime(d.estimated_completion) },
      ];
      break;
    }
    case 'parking': {
      const p = data.parkingSlots.find((x) => x.id === selected.id);
      if (!p) break;
      title = 'Parking Slot';
      rows = [
        { label: 'Status', value: p.status, badge: p.status },
        { label: 'Vehicle', value: p.vehicle_id ?? '—' },
        { label: 'Arrived', value: fmtTime(p.arrival_time) },
        { label: 'Departs', value: fmtTime(p.expected_departure) },
        { label: 'Assigned dock', value: p.assigned_dock ?? '—' },
      ];
      break;
    }
    case 'aisle': {
      const a = data.aisles.find((x) => x.id === selected.id);
      if (!a) break;
      title = 'Aisle';
      rows = [
        { label: 'Zone', value: a.zone ?? '—' },
        { label: 'Occupied', value: `${a.occupied_pct.toFixed(0)}%` },
        { label: 'Capacity', value: `${a.capacity_pct.toFixed(0)}%` },
        { label: 'Pick tasks', value: String(a.active_pick_tasks) },
        { label: 'Replenishments', value: String(a.replenishment_tasks) },
        { label: 'Risk', value: a.risk, badge: a.risk },
      ];
      break;
    }
    case 'bay': {
      const b = data.bays.find((x) => x.id === selected.id);
      if (!b) break;
      title = 'Bay';
      rows = [
        { label: 'Stock status', value: b.stock_status, badge: b.stock_status },
        { label: 'SKU', value: b.sku ?? '—' },
        { label: 'Quantity', value: `${b.current_quantity} / ${b.capacity}` },
        { label: 'Rack level', value: String(b.level) },
        { label: 'Replenish', value: b.replenishment_required ? 'Required' : 'No' },
        { label: 'Last movement', value: fmtTime(b.last_movement) },
      ];
      break;
    }
    case 'forklift': {
      const f = data.forklifts.find((x) => x.id === selected.id);
      if (!f) break;
      title = 'Forklift';
      rows = [
        { label: 'Activity', value: f.activity, badge: f.activity },
        { label: 'Operator', value: f.operator ?? '—' },
        { label: 'Aisle', value: f.current_aisle ?? '—' },
        { label: 'Battery', value: `${f.battery_pct.toFixed(0)}%` },
      ];
      break;
    }
    case 'pallet': {
      const p = data.pallets.find((x) => x.id === selected.id);
      if (!p) break;
      title = 'Pallet';
      rows = [
        { label: 'Stock status', value: p.stock_status, badge: p.stock_status },
        { label: 'SKU', value: p.sku ?? '—' },
        { label: 'Quantity', value: `${p.quantity} / ${p.max_quantity}` },
        { label: 'Condition', value: p.condition },
        { label: 'Bay', value: p.bay_code ?? '—' },
      ];
      break;
    }
    case 'shipment': {
      const s = data.shipments.find((x) => x.id === selected.id);
      if (!s) break;
      title = 'Shipment';
      rows = [
        { label: 'Status', value: s.status, badge: s.status },
        { label: 'Direction', value: s.direction },
        { label: 'Supplier', value: s.supplier_name ?? '—' },
        { label: 'Origin', value: s.origin ?? '—' },
        { label: 'Destination', value: s.destination ?? '—' },
        { label: 'ETA', value: fmtTime(s.eta) },
        { label: 'Delay', value: s.delay_hours ? `+${s.delay_hours}h` : 'None' },
        { label: 'Weight', value: `${s.weight_kg.toLocaleString()} kg` },
        { label: 'Risk', value: s.risk, badge: s.risk },
      ];
      break;
    }
    case 'exception': {
      const e = data.exceptions.find((x) => x.id === selected.id);
      if (!e) break;
      title = 'Exception';
      rows = [
        { label: 'Severity', value: e.severity, badge: e.severity },
        { label: 'Category', value: e.category.replace(/_/g, ' ') },
        { label: 'Entity', value: `${e.entity_type} ${e.entity_code}` },
        { label: 'Affected SKU', value: e.affected_sku ?? '—' },
        { label: 'Orders hit', value: String(e.affected_orders) },
        { label: 'Impact', value: fmtMoney(e.potential_impact, e.impact_currency) },
        {
          label: 'Coverage',
          value: e.inventory_coverage_days != null ? `${e.inventory_coverage_days}d` : '—',
        },
        { label: 'Delay', value: e.delay_hours ? `+${e.delay_hours}h` : 'None' },
      ];
      break;
    }
  }

  const exception =
    selected.type === 'exception' ? data.exceptions.find((x) => x.id === selected.id) : null;

  return (
    <section
      className={`detail-panel-overlay glass-panel ${
        activePanel === 'detail' ? 'panel-active' : 'panel-inactive'
      }`}
    >
      <div className="glass-panel-header">
        <div>
          <div className="glass-panel-title">{title}</div>
          <div className="glass-panel-code">{selected.code}</div>
        </div>
        <button
          className="glass-panel-close"
          onClick={() => setSelected(null)}
          aria-label="Close detail panel"
        >
          ×
        </button>
      </div>

      <div className="glass-panel-body">
        {rows.length === 0 && (
          <div className="detail-row">
            <span className="detail-label">No data</span>
          </div>
        )}

        {rows.map((r) => (
          <div key={r.label} className="detail-row">
            <span className="detail-label">{r.label}</span>
            {r.badge ? (
              <span className={`status-badge ${toneFor(r.badge)}`}>{r.value}</span>
            ) : (
              <span className="detail-value">{r.value}</span>
            )}
          </div>
        ))}

        {exception?.recommendation && (
          <div style={{ marginTop: 12 }}>
            <div className="detail-label" style={{ marginBottom: 4 }}>
              Recommendation
            </div>
            <div style={{ fontSize: 12, lineHeight: 1.5, color: 'var(--cp-text-secondary)' }}>
              {exception.recommendation}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
