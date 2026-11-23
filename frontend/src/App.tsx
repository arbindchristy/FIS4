import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { DashboardError, loadDashboard, type Dashboard, type Filters, type Source } from './api';
import { ReadinessPanels } from './ReadinessPanels';
import { HistoricalTrends } from './HistoricalTrends';
import type { HistoryWindow } from './api';

type View = { status: 'loading' } | { status: 'ready'; data: Dashboard } | { status: 'error'; error: DashboardError };
const latest: Filters = { date: '', command: '' };
const dateLabel = (day: string) => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${day}T00:00:00Z`));

export default function App() {
  const [filters, setFilters] = useState<Filters>(latest);
  const [draftDate, setDraftDate] = useState('');
  const [draftCommand, setDraftCommand] = useState('');
  const [availableCommands, setAvailableCommands] = useState<string[]>([]);
  const [source, setSource] = useState<Source | null>(null);
  const [reload, setReload] = useState(0);
  const [days, setDays] = useState<HistoryWindow>(30);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [view, setView] = useState<View>({ status: 'loading' });
  const blockSql = useCallback(() => {
    setSource('sql');
    setView({ status: 'error', error: new DashboardError('source', 'SQL is configured. This demonstration accepts synthetic data only.', 'sql') });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setView({ status: 'loading' });
    setSource(null);
    let sqlReported = false;
    const reportSource = (value: Source) => {
      sqlReported = sqlReported || value === 'sql';
      if (!controller.signal.aborted) setSource(sqlReported ? 'sql' : value);
    };
    loadDashboard(filters, controller.signal, reportSource).then(data => {
      if (controller.signal.aborted) return;
      setAvailableCommands(data.availableCommands);
      setDraftDate(data.fleet.date);
      setView({ status: 'ready', data });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      const failure = error instanceof DashboardError ? error : new DashboardError('unavailable', 'The readiness API could not be reached. Try again.');
      if (failure.source) setSource(failure.source);
      setView({ status: 'error', error: failure });
    });
    return () => controller.abort();
  }, [filters.date, filters.command, reload]);

  const busy = view.status === 'loading';
  function apply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setView({ status: 'loading' });
    setFilters({ date: draftDate, command: draftCommand });
    setReload(value => value + 1);
  }
  function reset() {
    setView({ status: 'loading' });
    setDraftDate('');
    setDraftCommand('');
    setFilters(latest);
    setReload(value => value + 1);
  }

  return <div className="app-shell" data-theme={theme}>
    <a className="skip-link" href="#dashboard">Skip to readiness dashboard</a>
    <header className="topbar">
      <div className="brand"><span className="brand-mark" aria-hidden="true">F<span>4</span></span><div><strong>Fleet Intelligence Suite</strong><span>FIS4</span></div></div>
      <div className="topbar-context"><span>READINESS OVERVIEW</span><span className={`source-badge ${source ?? 'unknown'}`} aria-label="Selected data source">{source ? source.toUpperCase() : 'SOURCE UNCONFIRMED'}</span></div>
    </header>
    <main id="dashboard" tabIndex={-1}>
      <div className="page-heading"><div><p className="eyebrow">HELICOPTER READINESS</p><h1>Fleet Intelligence Dashboard</h1><p>Snapshot and historical readiness across the fictional fleet.</p></div>
        <div className="snapshot-meta"><span>SELECTED SNAPSHOT</span><strong>{view.status === 'ready' ? dateLabel(view.data.fleet.date) : 'Awaiting API response'}</strong><span>{filters.command ? `Command ${filters.command}` : 'Fleet overview'}</span></div>
      </div>
      <aside className="demo-notice" aria-label="Demonstration scope"><span className="demo-icon" aria-hidden="true">i</span><div><strong>Synthetic demonstration</strong><span>Fictional helicopter history, not live operational intelligence. Local evaluation only; authentication is not implemented.</span></div></aside>
      <form className="filter-panel" onSubmit={apply} aria-label="Readiness filters">
        <div className="filter-title"><span aria-hidden="true" className="filter-glyph">☷</span><div><h2>Snapshot filters</h2><p>Choose a reporting date and command.</p></div></div>
        <div className="field"><label htmlFor="snapshot-date">Snapshot date</label><input id="snapshot-date" type="date" value={draftDate} onChange={event => setDraftDate(event.target.value)} disabled={busy} aria-describedby="date-help" /><span id="date-help">An empty date uses the latest snapshot.</span></div>
        <div className="field"><label htmlFor="command">Command</label><select id="command" value={draftCommand} onChange={event => setDraftCommand(event.target.value)} disabled={busy}><option value="">All commands</option>{availableCommands.map(command => <option key={command} value={command}>Command {command}</option>)}</select><span>Available commands come from the API.</span></div>
        <div className="filter-actions"><button type="submit" disabled={busy}>Apply filters</button><button type="button" className="secondary" onClick={reset} disabled={busy}>Latest snapshot</button></div>
      </form>
      <div className="section-caption"><h2>{filters.command ? `Command ${filters.command} overview` : 'Fleet overview'}</h2><span>{view.status === 'ready' ? 'API snapshot · display precision 1 decimal' : 'API-supplied readiness metrics'}</span></div>
      <div className="theme-controls"><button type="button" className="secondary" aria-pressed={theme === 'dark'} onClick={() => setTheme(value => value === 'light' ? 'dark' : 'light')}>Use {theme === 'light' ? 'dark' : 'light'} theme</button></div>
      <div aria-busy={busy}>
        {view.status === 'loading' ? <section className="state-panel" role="status"><span className="spinner" aria-hidden="true" /><h2>Loading readiness…</h2><p>Checking the configured data source and retrieving one consistent snapshot.</p></section> : null}
        {view.status === 'error' ? <section className={`state-panel error-state ${view.error.kind}`} role="alert"><span className="state-symbol" aria-hidden="true">!</span><h2>{view.error.kind === 'empty' ? 'No data for this selection' : view.error.kind === 'invalid' ? 'Check the filters' : view.error.kind === 'source' ? 'Synthetic mode required' : 'Readiness data unavailable'}</h2><p>{view.error.message}</p><button type="button" onClick={() => setReload(value => value + 1)}>Try again</button></section> : null}
        {view.status === 'ready' ? <ReadinessPanels data={view.data} days={days} setDays={setDays} blockSql={blockSql}><HistoricalTrends snapshot={view.data} days={days} setDays={setDays} blockSql={blockSql} /></ReadinessPanels> : null}
      </div>
      <footer><span>Fleet Intelligence Suite <span aria-hidden="true">/</span> Fleet Intelligence Dashboard</span><span>Historical demonstration · Local demonstration</span></footer>
    </main>
  </div>;
}
