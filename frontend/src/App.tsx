import { useEffect } from 'react';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { DigitalTwinCanvas } from '@/digital-twin/scene/DigitalTwinCanvas';
import { ControlTowerPanel } from '@/components/ControlTowerPanel';
import { DetailPanel } from '@/components/DetailPanel';
import { EventTimeline } from '@/components/EventTimeline';
import { CameraControls } from '@/components/CameraControls';
import { CommandBar } from '@/components/CommandBar';
import { CommandResponse } from '@/components/CommandResponse';

const NAV_ITEMS = [
  { id: 'digital-twin', icon: '◈', label: 'Digital Twin' },
  { id: 'control-tower', icon: '◉', label: 'Control Tower' },
  { id: 'logistics', icon: '⬡', label: 'Logistics' },
  { id: 'inventory', icon: '▦', label: 'Inventory' },
  { id: 'exceptions', icon: '⚠', label: 'Exceptions' },
  { id: 'agents', icon: '◎', label: 'Agents' },
];

export default function App() {
  const fetchAll = useDataStore((s) => s.fetchAll);
  const loading = useDataStore((s) => s.loading);
  const health = useDataStore((s) => s.health);
  const activePage = useUIStore((s) => s.activePage);
  const setActivePage = useUIStore((s) => s.setActivePage);
  const setDataLoaded = useUIStore((s) => s.setDataLoaded);

  useEffect(() => {
    fetchAll().then(() => setDataLoaded(true));
  }, [fetchAll, setDataLoaded]);

  const healthScore = health?.supply_chain_health ?? 0;
  const statusColor = healthScore >= 70 ? '' : healthScore >= 40 ? 'warning' : 'error';

  return (
    <div className="app-shell">
      {/* ── Top Bar ── */}
      <header className="app-topbar">
        <div className="app-topbar-logo">
          <div className="app-topbar-logo-icon" />
          ChainPilot
        </div>
        <div className="app-topbar-status">
          <span>SYSTEM</span>
          <div className={`status-dot ${statusColor}`} />
          <span>{loading ? 'SYNCING' : 'ONLINE'}</span>
        </div>
      </header>

      {/* ── Sidebar ── */}
      <nav className="app-sidebar">
        {NAV_ITEMS.map((item) => (
          <div
            key={item.id}
            className={`sidebar-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => setActivePage(item.id)}
            title={item.label}
          >
            {item.icon}
          </div>
        ))}
      </nav>

      {/* ── Main Viewport ── */}
      <main className="app-main">
        {loading && (
          <div className="loading-screen">
            <div className="loading-spinner" />
            <div className="loading-text">Initializing Digital Twin</div>
          </div>
        )}
        <DigitalTwinCanvas />
        <ControlTowerPanel />
        <DetailPanel />
        <EventTimeline />
        <CameraControls />
        <CommandResponse />
      </main>

      {/* ── Command Bar ── */}
      <CommandBar />
    </div>
  );
}
