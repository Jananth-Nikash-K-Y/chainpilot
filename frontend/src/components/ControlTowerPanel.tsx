/* ── ControlTowerPanel — the always-on health readout (top right) ── */
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { COLORS } from '@/constants';

function healthColor(score: number): string {
  if (score >= 70) return COLORS.green;
  if (score >= 40) return COLORS.amber;
  return COLORS.red;
}

export function ControlTowerPanel() {
  const health = useDataStore((s) => s.health);
  const activePanel = useUIStore((s) => s.activePanel);
  if (!health) return null;

  const score = health.supply_chain_health;

  const metrics: Array<{ label: string; value: string; alert?: boolean }> = [
    {
      label: 'Critical exceptions',
      value: String(health.critical_exceptions),
      alert: health.critical_exceptions > 0,
    },
    {
      label: 'Delayed shipments',
      value: String(health.delayed_shipments),
      alert: health.delayed_shipments > 0,
    },
    {
      label: 'Inventory risks',
      value: String(health.inventory_risks),
      alert: health.inventory_risks > 0,
    },
    {
      label: 'Orders at risk',
      value: String(health.orders_at_risk),
      alert: health.orders_at_risk > 0,
    },
    { label: 'Dock utilisation', value: `${health.dock_utilization_pct.toFixed(0)}%` },
    { label: 'Warehouse used', value: `${health.warehouse_utilization_pct.toFixed(0)}%` },
    { label: 'Trucks on site', value: String(health.total_trucks) },
    { label: 'Active forklifts', value: String(health.active_forklifts) },
  ];

  return (
    <aside
      className={`control-tower glass-panel ${
        activePanel === 'tower' ? 'panel-active' : 'panel-inactive'
      }`}
    >
      <div className="glass-panel-header">
        <span className="glass-panel-title">Control Tower</span>
        <span className="glass-panel-code">LIVE</span>
      </div>

      <div className="glass-panel-body">
        <div className="ct-health-score">
          <div className="ct-health-number" style={{ color: healthColor(score) }}>
            {score}
          </div>
          <div className="ct-health-label">Supply Chain Health</div>
        </div>

        {metrics.map((m) => (
          <div key={m.label} className="ct-metric">
            <span className="ct-metric-label">{m.label}</span>
            <span
              className="ct-metric-value"
              style={{ color: m.alert ? COLORS.red : undefined }}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>
    </aside>
  );
}
