import { STATUSES, type Dashboard, type HistoryWindow, type Commands } from './api';
import { useState, type ReactNode } from 'react';
import { CommandPlatforms } from './PlatformIntelligence';

const percentage = (value: number) => `${value.toFixed(1)}%`;
const count = (value: number) => value.toLocaleString('en-GB');
const statusNames: Record<string, string> = {
  FMC: 'Fully mission capable', PMCM: 'Partially capable · maintenance', PMCS: 'Partially capable · supply',
  NMCS: 'Non-mission capable · supply', NMCM: 'Non-mission capable · maintenance', DEPOT: 'Depot maintenance',
};

export function ReadinessPanels({ data, children, days, setDays, blockSql }: { data: Dashboard; children?: ReactNode; days: HistoryWindow; setDays: (days: HistoryWindow) => void; blockSql: () => void }) {
  const overview = data.overall ?? data;
  const metrics = overview.fleet.metrics;
  const counts = [
    ['Total tails', metrics.total_tails], ['FMC', metrics.fmc_tails], ['PMC', metrics.pmc_tails],
    ['NMCS', metrics.nmcs_tails], ['NMCM', metrics.nmcm_tails], ['DEPOT', metrics.depot_tails],
  ] as const;
  const statuses = [...overview.distribution.statuses].sort((a, b) => {
    const first = STATUSES.indexOf(a.status as (typeof STATUSES)[number]);
    const second = STATUSES.indexOf(b.status as (typeof STATUSES)[number]);
    return (first < 0 ? 99 : first) - (second < 0 ? 99 : second);
  });
  return <>
    <section className="kpi-grid" aria-label="Fleet readiness KPIs">
      <article className="kpi-card primary" aria-labelledby="serviceability-label">
        <div className="kpi-eyebrow"><span className="metric-symbol" aria-hidden="true">S</span><h2 id="serviceability-label">Serviceability</h2><span>FLEET</span></div>
        <p className="kpi-value" data-testid="serviceability">{percentage(metrics.svc_pct)}</p>
        <p className="kpi-description">Readiness against the serviceability population</p>
      </article>
      <article className="kpi-card" aria-labelledby="availability-label">
        <div className="kpi-eyebrow"><span className="metric-symbol" aria-hidden="true">A</span><h2 id="availability-label">Availability</h2><span>FLEET</span></div>
        <p className="kpi-value" data-testid="availability">{percentage(metrics.avail_pct)}</p>
        <p className="kpi-description">Mission-capable aircraft across the total fleet</p>
      </article>
    </section>
    <section className="count-grid" aria-label="Aircraft counts">
      {counts.map(([label, value]) => <article className="count-card" key={label} aria-label={`${label} count`}>
        <h2>{label}</h2><p>{count(value)}</p>{label === 'PMC' ? <span>PMCM + PMCS</span> : null}
      </article>)}
    </section>
    {children}
    <div className="report-grid">
      <section className="panel command-panel" aria-labelledby="command-heading">
        <div className="panel-heading"><div><p className="eyebrow">READINESS BY COMMAND</p><h2 id="command-heading">Command Readiness</h2></div><span className="panel-meta">{data.fleet.command ? `Command ${data.fleet.command}` : 'All commands'}</span></div>
        <div className="legend"><span><i className="swatch serviceability" />Serviceability</span><span><i className="swatch availability" />Availability</span></div>
        <div className="command-list">
          {data.commands.commands.map(row => <CommandRow key={`${data.fleet.date}/${row.command}`} row={row} data={data} days={days} setDays={setDays} blockSql={blockSql} />)}
        </div>
      </section>
      <section className="panel status-panel" aria-labelledby="status-heading">
        <div className="panel-heading"><div><p className="eyebrow">AIRCRAFT CONDITION</p><h2 id="status-heading">Status distribution</h2></div><span className="panel-meta">{count(overview.distribution.total_tails)} tails</span></div>
        <div className="composition-bar" role="img" aria-label="Readiness composition for the reporting snapshot">{statuses.map(row => <span key={row.status} className={`composition-${row.status.toLowerCase()}`} style={{ width: `${row.pct}%` }} title={`${row.status}: ${row.count}`} />)}</div>
        <ul className="status-list">
          {statuses.map(row => <li key={row.status} className="status-row" aria-label={`${row.status} status`}>
            <div className="status-label"><span className={`status-code status-${row.status.toLowerCase()}`}>{row.status}</span><span>{statusNames[row.status] ?? 'Unmapped status'}</span><strong>{count(row.count)}<small> tails</small></strong></div>
            <span className="status-percentage">{percentage(row.pct)}</span>
          </li>)}
        </ul>
      </section>
    </div>
    <p className="data-note">Readiness metrics and status percentages are supplied by the API. Percentages are rounded for display.</p>
  </>;
}

function CommandRow({ row, data, days, setDays, blockSql }: { row: Commands['commands'][number]; data: Dashboard;
  days: HistoryWindow; setDays: (days: HistoryWindow) => void; blockSql: () => void }) {
  const [expanded, setExpanded] = useState(false);
  return <article className="command-row" aria-label={`Command ${row.command} readiness`}>
    <div className="command-summary">
      <div className="command-title"><h3>Command {row.command}</h3><span>{count(row.total_tails)} tails</span></div>
      <div className="meter-row"><label htmlFor={`svc-${row.command}`}>Serviceability</label><meter id={`svc-${row.command}`} min="0" max="100" value={row.svc_pct}>{percentage(row.svc_pct)}</meter><strong>{percentage(row.svc_pct)}</strong></div>
      <div className="meter-row availability"><label htmlFor={`avail-${row.command}`}>Availability</label><meter id={`avail-${row.command}`} min="0" max="100" value={row.avail_pct}>{percentage(row.avail_pct)}</meter><strong>{percentage(row.avail_pct)}</strong></div>
      <dl className="command-counts">{[['FMC', row.fmc_tails], ['PMC', row.pmc_tails], ['NMCS', row.nmcs_tails], ['NMCM', row.nmcm_tails], ['NMC Total', row.nmcs_tails + row.nmcm_tails], ['DEPOT', row.depot_tails]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    </div>
    <details className="command-platforms" onToggle={event => setExpanded(event.currentTarget.open)}>
      <summary>Platform breakdown for Command {row.command}</summary>
      {expanded ? <CommandPlatforms snapshot={data} row={row} days={days} setDays={setDays} blockSql={blockSql} /> : null}
    </details>
  </article>;
}
