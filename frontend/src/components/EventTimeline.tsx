/* ── EventTimeline — collapsed to a latest-event pill, expandable to the feed ── */
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { SEVERITY_RANK, severityColor } from '@/constants';

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
  const expanded = useUIStore((s) => s.timelineExpanded);
  const toggle = useUIStore((s) => s.toggleTimeline);

  if (events.length === 0) return null;

  // Surface the most urgent recent event, not merely the newest.
  const headline =
    [...events]
      .slice(0, 8)
      .sort((a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9))[0] ??
    events[0];

  const urgent = events.filter(
    (e) => e.severity === 'CRITICAL' || e.severity === 'HIGH',
  ).length;

  if (!expanded) {
    return (
      <button
        className="hud-pill hud-pill--events"
        style={{ ['--pill-accent' as string]: severityColor(headline.severity) }}
        onClick={toggle}
        aria-expanded={false}
        aria-label="Expand event timeline"
        title="Recent operational events — click to expand"
      >
        <span
          className="event-dot"
          style={{ background: severityColor(headline.severity) }}
        />
        <span className="hud-pill-body">
          <span className="hud-pill-title">
            {relativeTime(headline.timestamp)} · {headline.entity_code}
          </span>
          <span className="hud-pill-sub">{headline.message}</span>
        </span>
        <span className="hud-pill-count">
          {urgent > 0 ? `${urgent}!` : events.length}
        </span>
      </button>
    );
  }

  return (
    <section className="event-timeline glass-panel">
      <div className="glass-panel-header">
        <span className="glass-panel-title">Event Timeline</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="glass-panel-code">{events.length}</span>
          <button
            className="glass-panel-close"
            onClick={toggle}
            aria-expanded
            aria-label="Minimise event timeline"
            title="Minimise"
          >
            −
          </button>
        </div>
      </div>

      <div className="glass-panel-body" style={{ overflowY: 'auto', maxHeight: 168 }}>
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
