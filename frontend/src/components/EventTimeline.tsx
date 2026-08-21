/* ── EventTimeline — rolling feed of operational events (bottom left) ── */
import { useDataStore } from '@/stores/dataStore';
import { severityColor } from '@/constants';

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '--';

  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.round(hours / 24)}d`;
}

export function EventTimeline() {
  const events = useDataStore((s) => s.events);
  if (events.length === 0) return null;

  return (
    <section className="event-timeline glass-panel">
      <div className="glass-panel-header">
        <span className="glass-panel-title">Event Timeline</span>
        <span className="glass-panel-code">{events.length}</span>
      </div>

      <div className="glass-panel-body" style={{ overflowY: 'auto', maxHeight: 148 }}>
        {events.map((e) => (
          <div key={e.id} className="event-item">
            <div className="event-dot" style={{ background: severityColor(e.severity) }} />
            <span className="event-time">{relativeTime(e.timestamp)}</span>
            <span className="event-message">{e.message}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
