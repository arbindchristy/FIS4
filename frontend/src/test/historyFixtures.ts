/** Fabricated API-shaped records for frontend tests only. No runtime import. */
import { vi } from 'vitest';
import { STATUSES, type Dashboard, type HistorySeries, type HistoryWindow } from '../api';
import { jsonResponse } from './fixtures';

export const historyCommands = ['FICTIONAL_A', 'FICTIONAL_B', 'FICTIONAL_C', 'FICTIONAL_D'];
export function historySnapshot(date = '2026-11-20', command: string | null = null): Dashboard {
  const counts = command ? [25, 3, 2, 3, 5, 2] : [100, 12, 8, 12, 20, 8];
  const metrics = { total_tails: command ? 40 : 160, fmc_tails: counts[0], pmc_tails: counts[1] + counts[2],
    nmcs_tails: counts[3], nmcm_tails: counts[4], depot_tails: counts[5], svc_pct: 82.75, avail_pct: 71.25 };
  return { fleet: { source: 'synthetic', date, command, metrics },
    commands: { source: 'synthetic', date, command, commands: (command ? [command] : historyCommands).map(code => ({
      ...(command ? metrics : { total_tails: 40, fmc_tails: 25, pmc_tails: 5, nmcs_tails: 3, nmcm_tails: 5, depot_tails: 2, svc_pct: 82.75, avail_pct: 71.25 }), command: code })) },
    distribution: { source: 'synthetic', date, command, total_tails: metrics.total_tails,
      statuses: STATUSES.map((code, i) => ({ status: code, count: counts[i], pct: counts[i] / metrics.total_tails * 100 })) },
    availableCommands: historyCommands };
}

export function historySeries(snapshot = historySnapshot(), days: HistoryWindow = 30): HistorySeries {
  const end = snapshot.fleet.date;
  const observations = Array.from({ length: days }, (_, index) => ({ ...snapshot.fleet.metrics,
    date: new Date(Date.parse(end) - (days - 1 - index) * 86400000).toISOString().slice(0, 10),
    svc_pct: index === days - 1 ? snapshot.fleet.metrics.svc_pct : 82.75 - index % 12,
    avail_pct: index === days - 1 ? snapshot.fleet.metrics.avail_pct : 71.25 - index % 9,
    status_counts: Object.fromEntries(snapshot.distribution.statuses.map(row => [row.status, row.count])) as HistorySeries['observations'][number]['status_counts'],
  }));
  return { source: 'synthetic', command: snapshot.fleet.command, requested_days: days,
    start_date: observations[0].date, end_date: end, point_count: days, observations };
}

export function stubHistory() {
  const mock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
    const url = new URL(String(input), 'http://127.0.0.1:5173');
    if (url.pathname === '/api/v1/platforms' || url.pathname.startsWith('/api/v1/readiness/history/platforms')) return jsonResponse({ detail: 'Not Found' }, 404);
    if (url.pathname === '/health') return jsonResponse({ source: 'synthetic', status: 'ok' });
    const date = url.searchParams.get('date') || url.searchParams.get('end_date') || '2026-11-20';
    const snapshot = historySnapshot(date, url.searchParams.get('command'));
    if (url.pathname.endsWith('/series')) return jsonResponse(historySeries(snapshot, Number(url.searchParams.get('days')) as HistoryWindow));
    if (url.pathname.endsWith('/commands')) return jsonResponse(snapshot.commands);
    if (url.pathname.endsWith('/fleet')) return jsonResponse(snapshot.fleet);
    if (url.pathname.endsWith('/status-distribution')) return jsonResponse(snapshot.distribution);
    throw new Error('Unexpected fixture URL');
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}
