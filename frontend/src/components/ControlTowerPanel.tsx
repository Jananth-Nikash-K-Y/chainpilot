/* ── ControlTowerPanel — collapsed health pill, expandable to full metrics ── */
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';

function healthTone(score: number): string {
  if (score >= 70) return 'var(--cp-green)';
  if (score >= 40) return 'var(--cp-amber)';
  return 'var(--cp-red)';
}

export function ControlTowerPanel() {
  const health = useDataStore((s) => s.health);
  const activePanel = useUIStore((s) => s.activePanel);
  const expanded = useUIStore((s) => s.towerExpanded);
  const toggle = useUIStore((s) => s.toggleTower);

  if (!health) return null;

  const score = health.supply_chain_health;
  const tone = healthTone(score);

  // Only things actually demanding attention belong in the collapsed pill.
  const alerts = [
    { label: 'critical', value: health.critical_exceptions },
    { label: 'delayed', value: health.delayed_shipments },
    { label: 'stock', value: health.inventory_risks },
    { label: 'orders', value: health.orders_at_risk },
  ].filter((a) => a.value > 0);

  const panelClass = activePanel === 'tower' ? 'panel-active' : 'panel-inactive';

  if (!expanded) {
    return (
      <button
        className={`hud-pill ${panelClass}`}
        style={{ ['--pill-accent' as string]: tone }}
        onClick={toggle}
        aria-expanded={false}
        aria-label="Expand control tower"
        title="Supply chain health — click to expand"
      >
        <span className="hud-pill-score" style={{ color: tone }}>
          {score}
        </span>
        <span className="hud-pill-body">
          <span className="hud-pill-title">Supply chain health</span>
          <span className="hud-pill-sub">
            {alerts.length === 0
              ? 'All clear'
              : alerts.map((a) => `${a.value} ${a.label}`).join(' · ')}
          </span>
        </span>
        <span className="hud-pill-chevron">▸</span>
      </button>
    );
  }

  const metrics: Array<{ label: string; value: string; alert?: boolean }> = [
    { label: 'Critical exceptions', value: String(health.critical_exceptions), alert: health.critical_exceptions > 0 },
    { label: 'Delayed shipments', value: String(health.delayed_shipments), alert: health.delayed_shipments > 0 },
    { label: 'Inventory risks', value: String(health.inventory_risks), alert: health.inventory_risks > 0 },
    { label: 'Orders at risk', value: String(health.orders_at_risk), alert: health.orders_at_risk > 0 },
    { label: 'Dock utilisation', value: `${health.dock_utilization_pct.toFixed(0)}%` },
    { label: 'Warehouse used', value: `${health.warehouse_utilization_pct.toFixed(0)}%` },
    { label: 'Trucks on site', value: String(health.total_trucks) },
    { label: 'Active forklifts', value: String(health.active_forklifts) },
  ];

  return (
    <aside className={`control-tower glass-panel ${panelClass}`}>
      <div className="glass-panel-header">
        <span className="glass-panel-title">Control Tower</span>
        <button
          className="glass-panel-close"
          onClick={toggle}
          aria-expanded
          aria-label="Minimise control tower"
          title="Minimise"
        >
          −
        </button>
      </div>

      <div className="glass-panel-body">
        <div className="ct-health-score">
          <div className="ct-health-number" style={{ color: tone }}>
            {score}
          </div>
          <div className="ct-health-label">Supply Chain Health</div>
        </div>

        {metrics.map((m) => (
          <div key={m.label} className="ct-metric">
            <span className="ct-metric-label">{m.label}</span>
            <span
              className="ct-metric-value"
              style={{ color: m.alert ? 'var(--cp-red)' : undefined }}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>
    </aside>
  );
}
