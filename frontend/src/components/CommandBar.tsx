/* ── CommandBar — natural-language query input along the bottom ── */
import { useEffect, useRef, type FormEvent } from 'react';
import { useUIStore } from '@/stores/uiStore';

export function CommandBar() {
  const inputRef = useRef<HTMLInputElement>(null);
  const query = useUIStore((s) => s.commandBarQuery);
  const setQuery = useUIStore((s) => s.setCommandBarQuery);
  const submitQuery = useUIStore((s) => s.submitQuery);
  const loading = useUIStore((s) => s.commandBarLoading);

  // ⌘K / Ctrl-K focuses the bar from anywhere.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') inputRef.current?.blur();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    void submitQuery(trimmed);
  };

  return (
    <form className="app-commandbar" onSubmit={onSubmit}>
      <div className="commandbar-input-wrap">
        <span className="commandbar-icon">{loading ? '◌' : '⌕'}</span>
        <input
          ref={inputRef}
          className="commandbar-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask ChainPilot — e.g. which trucks are delayed?  (⌘K)"
          disabled={loading}
          aria-label="Ask ChainPilot"
        />
        {/* Explicit submit button: gives Enter a reliable target and a tap
            target on touch devices. */}
        <button
          type="submit"
          className="commandbar-submit"
          disabled={loading || !query.trim()}
          aria-label="Run query"
        >
          {loading ? '…' : 'Ask'}
        </button>
      </div>
    </form>
  );
}
