import { useEffect, useState } from 'react';
import { DashboardError, loadPlatforms, loadPlatformSeries, STATUSES, WINDOWS,
  type Dashboard, type FailureKind, type HistoryWindow, type PlatformData, type PlatformRow, type PlatformSeries } from './api';
import { dateLabel, TrendChart } from './HistoricalTrends';

type Props = { snapshot: Dashboard; days: HistoryWindow; setDays: (days: HistoryWindow) => void; blockSql: () => void };
type State = { snapshot: Dashboard; retry: number } & ({ status: 'loading' } | { status: 'ready'; data: PlatformData }
  | { status: 'error'; error: DashboardError });
const messages: Record<FailureKind, string> = {
  unsupported: 'Platform endpoints are not enabled for this provider. The overview remains available.',
  empty: 'No platform observations match this selection.',
  invalid: 'The API rejected the platform selection. Check the snapshot filters and try again.',
  unavailable: 'Platform data could not be reached. Check the local backend and try again.',
  contract: 'Platform data could not be validated for this snapshot. Try again.',
  source: 'This demonstration requires synthetic data.',
};
const failure = (error: unknown) => error instanceof DashboardError ? error : new DashboardError('unavailable', messages.unavailable);

function PlatformError({ error, retry, history = false }: { error: DashboardError; retry: () => void; history?: boolean }) {
  return <div className="history-message" role={error.kind === 'unsupported' ? 'status' : 'alert'}>
    <h3>{history ? 'Platform history unavailable' : 'Platform Intelligence unavailable'}</h3>
    <p>{messages[error.kind]}</p><button type="button" className="secondary" onClick={retry}>Retry platform {history ? 'history' : 'data'}</button>
  </div>;
}

export function PlatformIntelligence({ snapshot, days, setDays, blockSql }: Props) {
  const [retry, setRetry] = useState(0);
  const [preferred, setPreferred] = useState('');
  const [state, setState] = useState<State>({ snapshot, retry, status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    setState({ snapshot, retry, status: 'loading' });
    loadPlatforms(snapshot, controller.signal, source => {
      if (!controller.signal.aborted && source === 'sql') blockSql();
    }).then(data => {
      if (!controller.signal.aborted) setState({ snapshot, retry, status: 'ready', data });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ snapshot, retry, status: 'error', error: failure(error) });
    });
    return () => controller.abort();
  }, [snapshot, retry, blockSql]);
  const current = state.snapshot === snapshot && state.retry === retry ? state : { status: 'loading' as const };
  return <section className="panel platform-panel" aria-labelledby="platform-heading" data-testid="platform-intelligence">
    <div className="panel-heading"><div><p className="eyebrow">AIRCRAFT PLATFORM ANALYSIS</p><h2 id="platform-heading">Platform Intelligence</h2></div></div>
    <p className="platform-context">{dateLabel(snapshot.fleet.date)} · {snapshot.fleet.command ? `Command ${snapshot.fleet.command}` : 'All commands'}</p>
    <p className="platform-note">Platform selection affects only this section. Fleet and command overview values remain unchanged.</p>
    {current.status === 'loading' ? <p role="status">Loading platform comparisons…</p> : null}
    {current.status === 'error' ? <PlatformError error={current.error} retry={() => setRetry(value => value + 1)} /> : null}
    {current.status === 'ready' ? <PlatformView snapshot={snapshot} days={days} setDays={setDays} blockSql={blockSql}
      data={current.data} platform={current.data.options.includes(preferred) ? preferred : current.data.options[0]}
      setPlatform={setPreferred} /> : null}
  </section>;
}

function PlatformView({ snapshot, days, setDays, blockSql, data, platform, setPlatform }: Props & {
  data: PlatformData; platform: string; setPlatform: (platform: string) => void;
}) {
  const selected = data.rows.find(row => row.platform === platform)!;
  return <>
    <div className="table-scroll platform-comparisons" role="region" aria-label="Platform comparison table" tabIndex={0}>
      <table><caption>Platform comparisons · {dateLabel(snapshot.fleet.date)} · {snapshot.fleet.command ?? 'All commands'}</caption>
        <thead><tr>{['Platform', 'Total', 'PMC', ...STATUSES, 'Serviceability', 'Availability'].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
        <tbody>{data.rows.map(row => <tr key={row.platform} data-testid={`platform-row-${row.platform}`}>
          <th scope="row">{row.platform}</th><td>{row.total_tails}</td><td>{row.pmc_tails}</td>
          {STATUSES.map(code => <td key={code}>{row.status_counts[code]}</td>)}
          <td>{row.svc_pct.toFixed(1)}%</td><td>{row.avail_pct.toFixed(1)}%</td>
        </tr>)}</tbody>
      </table>
    </div>
    <div className="platform-controls"><div className="field"><label htmlFor="platform-select">Platform</label>
      <select id="platform-select" value={platform} onChange={event => setPlatform(event.target.value)}>
        {data.options.map(label => <option key={label} value={label}>{label}</option>)}
      </select></div><div className="field"><label htmlFor="platform-window">Platform historical window</label>
      <select id="platform-window" value={days} onChange={event => setDays(Number(event.target.value) as HistoryWindow)}>
        {WINDOWS.map(value => <option key={value} value={value}>{value} days</option>)}
      </select></div></div>
    <h3>Platform history: {platform}</h3>
    <PlatformHistory snapshot={snapshot} selected={selected} days={days} blockSql={blockSql} />
  </>;
}

function PlatformHistory({ snapshot, selected, days, blockSql }: {
  snapshot: Dashboard; selected: PlatformRow; days: HistoryWindow; blockSql: () => void;
}) {
  const [retry, setRetry] = useState(0);
  const key = `${snapshot.fleet.date}/${snapshot.fleet.command}/${selected.platform}/${days}/${retry}`;
  const [state, setState] = useState<{ key: string; selected: PlatformRow } &
    ({ status: 'loading' } | { status: 'ready'; series: PlatformSeries } | { status: 'error'; error: DashboardError })>(
      { key, selected, status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    setState({ key, selected, status: 'loading' });
    loadPlatformSeries(snapshot, selected, days, controller.signal, source => {
      if (!controller.signal.aborted && source === 'sql') blockSql();
    }).then(series => {
      if (!controller.signal.aborted) setState({ key, selected, status: 'ready', series });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ key, selected, status: 'error', error: failure(error) });
    });
    return () => controller.abort();
  }, [snapshot, selected, days, key, blockSql]);
  const current = state.key === key && state.selected === selected ? state : { status: 'loading' as const };
  return <div className="platform-history" role="region" aria-label="Selected platform history">
    {current.status === 'loading' ? <p role="status">Loading platform history…</p> : null}
    {current.status === 'error' ? <PlatformError history error={current.error} retry={() => setRetry(value => value + 1)} /> : null}
    {current.status === 'ready' ? <TrendChart key={key} platform={selected.platform} series={current.series} /> : null}
  </div>;
}
