import { memo, useEffect, useId, useMemo, useState } from 'react';
import { DashboardError, loadSeries, STATUSES, WINDOWS, type Dashboard, type HistorySeries, type HistoryWindow } from './api';

export const dateLabel = (day: string) => new Intl.DateTimeFormat('en-GB', {
  day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC',
}).format(new Date(`${day}T00:00:00Z`));
const pct = (value: number) => `${value.toFixed(1)}%`;
type State = { key: string; status: 'loading' } | { key: string; status: 'ready'; series: HistorySeries }
  | { key: string; status: 'error'; error: DashboardError };

export function HistoricalTrends({ snapshot, days, setDays, blockSql }: {
  snapshot: Dashboard; days: HistoryWindow; setDays: (days: HistoryWindow) => void; blockSql: () => void;
}) {
  const [retry, setRetry] = useState(0);
  const key = `${snapshot.fleet.date}/${snapshot.fleet.command}/${days}/${retry}`;
  const [state, setState] = useState<State>({ key, status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    setState({ key, status: 'loading' });
    loadSeries(snapshot, days, controller.signal, source => {
      if (!controller.signal.aborted && source === 'sql') blockSql();
    }).then(series => {
      if (!controller.signal.aborted) setState({ key, status: 'ready', series });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      const failure = error instanceof DashboardError ? error : new DashboardError('unavailable', 'Historical data could not be reached. Try again.');
      setState({ key, status: 'error', error: failure });
    });
    return () => controller.abort();
  }, [snapshot, days, key, blockSql]);
  const current = state.key === key ? state : { key, status: 'loading' as const };
  return <section className="panel trend-panel" aria-labelledby="trend-heading">
    <div className="panel-heading"><div><p className="eyebrow">HISTORICAL READINESS</p><h2 id="trend-heading">Readiness over time</h2></div>
      <div className="field"><label htmlFor="history-window">Historical window</label><select id="history-window" value={days} onChange={event => setDays(Number(event.target.value) as HistoryWindow)}>
        {WINDOWS.map(window => <option value={window} key={window}>{window} days</option>)}
      </select></div></div>
    {current.status === 'loading' ? <p role="status">Loading historical observations…</p> : null}
    {current.status === 'error' ? <div className="history-message" role={current.error.kind === 'unsupported' ? 'status' : 'alert'}>
      <h3>{current.error.kind === 'unsupported' ? 'History not enabled' : current.error.kind === 'empty' ? 'No historical observations' : current.error.kind === 'invalid' ? 'Check the historical selection' : 'Historical data unavailable'}</h3>
      <p>{current.error.message}</p>{current.error.kind !== 'unsupported' ? <button type="button" onClick={() => setRetry(value => value + 1)}>Retry history</button> : null}
    </div> : null}
    {current.status === 'ready' ? <TrendChart key={key} series={current.series} /> : null}
  </section>;
}

function TrendChart({ series }: { series: HistorySeries }) {
  const titleId = useId();
  const [index, setIndex] = useState(series.observations.length - 1);
  const rows = series.observations;
  const x = (i: number) => rows.length === 1 ? 504 : 56 + i / (rows.length - 1) * 888;
  const y = (value: number) => 20 + (100 - value) * 1.8;
  const lines = useMemo(() => ({
    svc: rows.map((row, i) => `${rows.length === 1 ? 504 : 56 + i / (rows.length - 1) * 888},${20 + (100 - row.svc_pct) * 1.8}`).join(' '),
    avail: rows.map((row, i) => `${rows.length === 1 ? 504 : 56 + i / (rows.length - 1) * 888},${20 + (100 - row.avail_pct) * 1.8}`).join(' '),
  }), [rows]);
  const selected = rows[index];
  const detail = `${dateLabel(selected.date)} · Serviceability ${pct(selected.svc_pct)} · Availability ${pct(selected.avail_pct)}`;
  return <>
    <p className="trend-period">{dateLabel(series.start_date)} – {dateLabel(series.end_date)} · {series.point_count} daily observations · {series.command ?? 'All commands'}</p>
    <div className="legend trend-legend"><span><i className="line-key svc" aria-hidden="true" />Serviceability</span><span><i className="line-key avail" aria-hidden="true" />Availability</span></div>
    <div className="chart-scroll" tabIndex={0} role="region" aria-label="Historical trend plot"><svg className="trend-chart" viewBox="0 0 960 244" role="img" aria-labelledby={titleId} tabIndex={0}
      aria-describedby={`${titleId}-detail`} onKeyDown={event => {
        const target = event.key === 'Home' ? 0 : event.key === 'End' ? rows.length - 1
          : event.key === 'ArrowLeft' ? Math.max(0, index - 1) : event.key === 'ArrowRight' ? Math.min(rows.length - 1, index + 1) : null;
        if (target !== null) { event.preventDefault(); setIndex(target); }
      }} onPointerMove={event => {
        const bounds = event.currentTarget.getBoundingClientRect();
        const position = ((event.clientX - bounds.left) / bounds.width * 960 - 56) / 888;
        setIndex(Math.max(0, Math.min(rows.length - 1, Math.round(position * (rows.length - 1)))));
      }}>
      <title id={titleId}>Daily serviceability and availability, 0 to 100 percent. Use arrow keys, Home or End to inspect observations.</title>
      {[0, 25, 50, 75, 100].map(value => <g key={value}><line x1="56" x2="944" y1={y(value)} y2={y(value)} className="chart-grid" /><text x="44" y={y(value) + 4} textAnchor="end">{value}%</text></g>)}
      <polyline data-testid="serviceability-line" className="trend-line svc" points={lines.svc} />
      <polyline data-testid="availability-line" className="trend-line avail" points={lines.avail} />
      <line className="chart-cursor" x1={x(index)} x2={x(index)} y1="20" y2="200" />
      <circle className="svc-dot" cx={x(index)} cy={y(selected.svc_pct)} r="4" /><circle className="avail-dot" cx={x(index)} cy={y(selected.avail_pct)} r="4" />
      {[...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])].map(i => <text key={i} x={x(i)} y="229" textAnchor={i === 0 ? 'start' : i === rows.length - 1 ? 'end' : 'middle'}>{dateLabel(rows[i].date)}</text>)}
    </svg></div>
    <p className="plot-help">Hover or focus the chart to inspect a day. On narrow screens, scroll the plot to see the full date axis.</p>
    <p className="trend-detail" id={`${titleId}-detail`} aria-live="polite" data-testid="trend-detail">{detail}</p>
    <label className="day-picker" htmlFor={`${titleId}-day`}>Inspect historical day<input id={`${titleId}-day`} type="range" min={0} max={rows.length - 1} value={index}
      aria-valuetext={detail} onChange={event => setIndex(Number(event.target.value))} /></label>
    <TrendTable series={series} />
  </>;
}

const TrendTable = memo(function TrendTable({ series }: { series: HistorySeries }) {
  return <details className="trend-table"><summary>View daily readiness data ({series.point_count} days)</summary>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Historical data table"><table>
      <caption>Daily historical readiness · {series.command ?? 'All commands'} · percentages supplied by the API</caption>
      <thead><tr>{['Date', 'Serviceability', 'Availability', 'Total', 'PMC', ...STATUSES].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
      <tbody>{series.observations.map(row => <tr key={row.date}><th scope="row">{row.date}</th><td>{pct(row.svc_pct)}</td><td>{pct(row.avail_pct)}</td><td>{row.total_tails}</td><td>{row.pmc_tails}</td>
        {STATUSES.map(code => <td key={code}>{row.status_counts[code]}</td>)}</tr>)}</tbody>
    </table></div>
  </details>;
});
