import { useEffect, useState, type FormEvent } from 'react';
import { DashboardError, loadDashboard, type Dashboard, type Filters, type Source } from './api';
import { ReadinessPanels } from './ReadinessPanels';

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
  const [view, setView] = useState<View>({ status: 'loading' });

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
    setFilters({ date: draftDate, command: draftCommand });
    setReload(value => value + 1);
  }
  function reset() {
    setDraftDate('');
    setDraftCommand('');
    setFilters(latest);
    setReload(value => value + 1);
  }

  return <div className="app-shell">
    <a className="skip-link" href="#dashboard">Skip to readiness dashboard</a>
    <header className="topbar">
      <div className="brand"><span className="brand-mark" aria-hidden="true">F<span>4</span></span><div><strong>FIS4</strong><span>FLEET INFORMATION SYSTEM</span></div></div>
      <div className="topbar-context"><span>READINESS OVERVIEW</span><span className={`source-badge ${source ?? 'unknown'}`} aria-label="Selected data source">{source ? source.toUpperCase() : 'SOURCE UNCONFIRMED'}</span></div>
    </header>
    <main id="dashboard" tabIndex={-1}>
      <div className="page-heading"><div><p className="eyebrow">AIRCRAFT READINESS</p><h1>Fleet readiness</h1><p>Daily serviceability and availability across the fleet.</p></div>
        <div className="snapshot-meta"><span>SELECTED SNAPSHOT</span><strong>{view.status === 'ready' ? dateLabel(view.data.fleet.date) : 'Awaiting API response'}</strong><span>{view.status === 'ready' && view.data.fleet.command ? `Command ${view.data.fleet.command}` : 'Fleet overview'}</span></div>
      </div>
      <aside className="demo-notice" aria-label="Demonstration scope"><span className="demo-icon" aria-hidden="true">i</span><div><strong>Synthetic demonstration</strong><span>Fictional aircraft data. Local evaluation only; authentication is not implemented.</span></div></aside>
      <form className="filter-panel" onSubmit={apply} aria-label="Readiness filters">
        <div className="filter-title"><span aria-hidden="true" className="filter-glyph">☷</span><div><h2>Snapshot filters</h2><p>Choose a reporting date and command.</p></div></div>
        <div className="field"><label htmlFor="snapshot-date">Snapshot date</label><input id="snapshot-date" type="date" value={draftDate} onChange={event => setDraftDate(event.target.value)} disabled={busy} aria-describedby="date-help" /><span id="date-help">An empty date uses the latest snapshot.</span></div>
        <div className="field"><label htmlFor="command">Command</label><select id="command" value={draftCommand} onChange={event => setDraftCommand(event.target.value)} disabled={busy}><option value="">All commands</option>{availableCommands.map(command => <option key={command} value={command}>Command {command}</option>)}</select><span>Available commands come from the API.</span></div>
        <div className="filter-actions"><button type="submit" disabled={busy}>Apply filters</button><button type="button" className="secondary" onClick={reset} disabled={busy}>Latest snapshot</button></div>
      </form>
      <div className="section-caption"><h2>{view.status === 'ready' && view.data.fleet.command ? `Command ${view.data.fleet.command} overview` : 'Fleet overview'}</h2><span>{view.status === 'ready' ? 'API snapshot · display precision 1 decimal' : 'API-supplied readiness metrics'}</span></div>
      <div aria-busy={busy}>
        {view.status === 'loading' ? <section className="state-panel" role="status"><span className="spinner" aria-hidden="true" /><h2>Loading readiness…</h2><p>Checking the configured data source and retrieving one consistent snapshot.</p></section> : null}
        {view.status === 'error' ? <section className={`state-panel error-state ${view.error.kind}`} role="alert"><span className="state-symbol" aria-hidden="true">!</span><h2>{view.error.kind === 'empty' ? 'No data for this selection' : view.error.kind === 'invalid' ? 'Check the filters' : view.error.kind === 'source' ? 'Synthetic mode required' : 'Readiness data unavailable'}</h2><p>{view.error.message}</p><button type="button" onClick={() => setReload(value => value + 1)}>Try again</button></section> : null}
        {view.status === 'ready' ? <ReadinessPanels data={view.data} /> : null}
      </div>
      <footer><span>FIS4 <span aria-hidden="true">/</span> Readiness dashboard</span><span>Phase 03A · Local demonstration</span></footer>
    </main>
  </div>;
}
