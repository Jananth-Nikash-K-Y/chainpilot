/* ── AgentConsole — agent findings, tool trace and the approval queue ── */
import { useState } from 'react';
import { useUIStore } from '@/stores/uiStore';
import { SEVERITY_RANK, severityColor, toneFor } from '@/constants';

function money(v: number): string {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(0)}K`;
  return `₹${v.toFixed(0)}`;
}

export function AgentConsole() {
  const run = useUIStore((s) => s.agentRun);
  const loading = useUIStore((s) => s.commandBarLoading);
  const close = useUIStore((s) => s.closeAgentRun);
  const decide = useUIStore((s) => s.decideAction);
  const deciding = useUIStore((s) => s.decidingActionId);
  const submitQuery = useUIStore((s) => s.submitQuery);
  const activePanel = useUIStore((s) => s.activePanel);
  const actionError = useUIStore((s) => s.actionError);

  const [showTrace, setShowTrace] = useState(false);

  if (!loading && !run) return null;

  const findings = (run?.agents ?? [])
    .flatMap((a) => a.findings)
    .sort((a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9));

  const pending = (run?.actions ?? []).filter(
    (a) => a.status === 'PROPOSED' || a.status === 'VALIDATED',
  );
  const settled = (run?.actions ?? []).filter(
    (a) => a.status === 'EXECUTED' || a.status === 'REJECTED' || a.status === 'FAILED',
  );

  return (
    <section
      className={`agent-console glass-panel ${
        activePanel === 'agent' ? 'panel-active' : 'panel-inactive'
      }`}
    >
      <div className="glass-panel-header">
        <div>
          <div className="glass-panel-title">Agent Console</div>
          {run && <div className="glass-panel-code">{run.query}</div>}
        </div>
        <button className="glass-panel-close" onClick={close} aria-label="Close agent console">
          ×
        </button>
      </div>

      {loading && (
        <div className="agent-thinking">
          <div className="loading-spinner" />
          <span>Agents reasoning over live data…</span>
        </div>
      )}

      {!loading && run && (
        <div className="agent-console-scroll">
          <p className="agent-answer">{run.response}</p>

          {/* Which agents ran */}
          {run.agents.length > 0 && (
            <>
              <div className="agent-section-title">Agents engaged</div>
              <div className="agent-chips">
                {run.agents.map((a) => (
                  <span
                    key={a.agent}
                    className="agent-chip"
                    title={`${a.summary} (relevance ${(a.relevance * 100).toFixed(0)}%)`}
                  >
                    {a.agent}
                  </span>
                ))}
                <button
                  className={`agent-chip ${showTrace ? '' : 'dim'}`}
                  onClick={() => setShowTrace((v) => !v)}
                >
                  {showTrace ? 'hide' : 'show'} tool trace
                </button>
              </div>
            </>
          )}

          {/* Tool call trace — the evidence behind the answer */}
          {showTrace && (
            <>
              <div className="agent-section-title">Tool calls</div>
              {run.agents.map((a) => (
                <div key={a.agent} style={{ marginBottom: 8 }}>
                  <div className="tool-trace">
                    <b>{a.agent}</b> — {a.summary}
                  </div>
                  {a.tool_calls.map((t, i) => (
                    <div className="tool-trace" key={`${t.tool}-${i}`}>
                      → {t.tool}() <b>{t.result_summary}</b>
                    </div>
                  ))}
                </div>
              ))}
            </>
          )}

          {/* Findings */}
          {findings.length > 0 && (
            <>
              <div className="agent-section-title">Findings ({findings.length})</div>
              {findings.slice(0, 8).map((f, i) => (
                <div className="finding" key={`${f.entity_code}-${i}`}>
                  <div
                    className="finding-bar"
                    style={{ background: severityColor(f.severity) }}
                  />
                  <div>
                    <div className="finding-head">{f.headline}</div>
                    <div className="finding-detail">{f.detail}</div>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Approval queue — the human-in-the-loop gate */}
          {actionError && (
            <div className="action-error">Could not apply action: {actionError}</div>
          )}

          {pending.length > 0 && (
            <>
              <div className="agent-section-title">Awaiting your approval ({pending.length})</div>
              {pending.map((a) => (
                <div className="action-card" key={a.id}>
                  <div className="action-title">{a.title}</div>
                  <div className="action-meta">
                    <span>{a.proposed_by}</span>
                    <span className="save">save {money(a.projected_savings)}</span>
                    {a.projected_impact > 0 && <span>cost {money(a.projected_impact)}</span>}
                    <span>{(a.confidence * 100).toFixed(0)}% conf</span>
                  </div>
                  <div className="action-rationale">{a.rationale}</div>
                  {a.validation_notes && (
                    <div className="action-validation">✓ {a.validation_notes}</div>
                  )}
                  <div className="action-buttons">
                    <button
                      className="btn btn-approve"
                      disabled={deciding === a.id}
                      onClick={() => void decide(a.id, 'approve')}
                    >
                      {deciding === a.id ? 'Applying…' : 'Approve'}
                    </button>
                    <button
                      className="btn btn-reject"
                      disabled={deciding === a.id}
                      onClick={() => void decide(a.id, 'reject')}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Decided actions */}
          {settled.length > 0 && (
            <>
              <div className="agent-section-title">Decided</div>
              {settled.map((a) => (
                <div
                  className={`action-card ${a.status === 'EXECUTED' ? 'executed' : 'rejected'}`}
                  key={a.id}
                >
                  <div className="action-title">{a.title}</div>
                  <div className="action-meta">
                    <span className={`status-badge ${toneFor(a.status)}`}>{a.status}</span>
                    {a.result_message && <span>{a.result_message}</span>}
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Follow-ups */}
          {run.suggestions.length > 0 && (
            <>
              <div className="agent-section-title">Ask next</div>
              <div className="command-suggestions" style={{ padding: 0 }}>
                {run.suggestions.map((s) => (
                  <button
                    key={s}
                    className="command-suggestion-chip"
                    onClick={() => void submitQuery(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
