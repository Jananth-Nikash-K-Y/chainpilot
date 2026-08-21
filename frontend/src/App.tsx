import { useEffect } from 'react';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { DigitalTwinCanvas } from '@/digital-twin/scene/DigitalTwinCanvas';
import { ControlTowerPanel } from '@/components/ControlTowerPanel';
import { DetailPanel } from '@/components/DetailPanel';
import { EventTimeline } from '@/components/EventTimeline';
import { CameraControls } from '@/components/CameraControls';
import { CommandBar } from '@/components/CommandBar';
import { AgentConsole } from '@/components/AgentConsole';

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
  const error = useDataStore((s) => s.error);
  const health = useDataStore((s) => s.health);

  const activePage = useUIStore((s) => s.activePage);
  const setActivePage = useUIStore((s) => s.setActivePage);
  const setDataLoaded = useUIStore((s) => s.setDataLoaded);
  const activePanel = useUIStore((s) => s.activePanel);
  const setActivePanel = useUIStore((s) => s.setActivePanel);
  const agentRun = useUIStore((s) => s.agentRun);
  const agentLoading = useUIStore((s) => s.commandBarLoading);
  const selected = useUIStore((s) => s.selectedObject);

  useEffect(() => {
    fetchAll().then(() => setDataLoaded(true));
  }, [fetchAll, setDataLoaded]);

  const healthScore = health?.supply_chain_health ?? 0;
  const statusColor = healthScore >= 70 ? '' : healthScore >= 40 ? 'warning' : 'error';

  const agentOpen = Boolean(agentRun || agentLoading);

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
          <div className={`status-dot ${error ? 'error' : statusColor}`} />
          <span>{error ? 'OFFLINE' : loading ? 'SYNCING' : 'ONLINE'}</span>
        </div>
      </header>

      {/* ── Sidebar ── */}
      <nav className="app-sidebar">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => setActivePage(item.id)}
            title={item.label}
            aria-label={item.label}
          >
            {item.icon}
          </button>
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

        {error && !loading && (
          <div className="loading-screen">
            <div className="loading-text" style={{ color: 'var(--cp-red)' }}>
              Backend unreachable
            </div>
            <div className="agent-empty" style={{ textAlign: 'center', maxWidth: 380 }}>
              {error}
              <br />
              Start it with <code>uvicorn app.main:app --reload</code> in <code>backend/</code>.
            </div>
            <button className="btn btn-inline" onClick={() => void fetchAll()}>
              Retry
            </button>
          </div>
        )}

        <DigitalTwinCanvas />

        {/* Panel switcher — only rendered on narrow viewports (CSS-gated) */}
        <div className="panel-toggle">
          <button
            className={`camera-btn ${activePanel === 'tower' ? 'active' : ''}`}
            onClick={() => setActivePanel('tower')}
          >
            Health
          </button>
          {agentOpen && (
            <button
              className={`camera-btn ${activePanel === 'agent' ? 'active' : ''}`}
              onClick={() => setActivePanel('agent')}
            >
              Agents
            </button>
          )}
          {selected && (
            <button
              className={`camera-btn ${activePanel === 'detail' ? 'active' : ''}`}
              onClick={() => setActivePanel('detail')}
            >
              {selected.code}
            </button>
          )}
        </div>

        <ControlTowerPanel />
        <DetailPanel />
        <EventTimeline />
        <CameraControls />
        <AgentConsole />
      </main>

      {/* ── Command Bar ── */}
      <CommandBar />
    </div>
  );
}
