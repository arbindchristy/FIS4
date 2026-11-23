/** Fictional acceptance records with deliberately distinct API percentages and populations. */
import { vi } from 'vitest';
import { STATUSES, type Dashboard, type HistoryWindow } from '../api';
import { historySnapshot, historySeries, historyCommands } from './historyFixtures';
import { comparison, labels, platformSeries } from './platformFixtures';
import { jsonResponse } from './fixtures';

export function scopeSnapshot(date = '2026-11-20', command: string | null = null): Dashboard {
  const counts = [[24, 2, 1, 4, 6, 3], [20, 4, 3, 5, 6, 2], [28, 2, 2, 2, 4, 2], [25, 3, 4, 1, 4, 3]];
  const values = [[78.125, 67.25], [64.375, 58.125], [91.25, 81.125], [87.125, 76.25]];
  const rows = counts.map((c, i) => ({ command: historyCommands[i], total_tails: 40, fmc_tails: c[0], pmc_tails: c[1] + c[2],
    nmcs_tails: c[3], nmcm_tails: c[4], depot_tails: c[5], svc_pct: values[i][0], avail_pct: values[i][1] }));
  const index = command === null ? -1 : historyCommands.indexOf(command);
  if (command !== null && index < 0) throw new Error('Unknown fictional fixture command');
  const c = index < 0 ? STATUSES.map((_, i) => counts.reduce((sum, row) => sum + row[i], 0)) : counts[index];
  const metrics = index < 0 ? { total_tails: 160, fmc_tails: c[0], pmc_tails: c[1] + c[2], nmcs_tails: c[3], nmcm_tails: c[4],
    depot_tails: c[5], svc_pct: 83.125, avail_pct: 72.375 } : rows[index];
  const snapshot = historySnapshot(date, command);
  snapshot.fleet.metrics = metrics;
  snapshot.commands.commands = command ? [rows[index]] : rows;
  snapshot.distribution = { source: 'synthetic', date, command, total_tails: metrics.total_tails,
    statuses: STATUSES.map((status, i) => ({ status, count: c[i], pct: c[i] / metrics.total_tails * 100 })) };
  return snapshot;
}

export function stubScopedHistory() {
  const mock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
    const url = new URL(String(input), 'http://127.0.0.1');
    if (url.pathname === '/health') return jsonResponse({ source: 'synthetic', status: 'ok' });
    const snapshot = scopeSnapshot(url.searchParams.get('date') || url.searchParams.get('end_date') || '2026-11-20', url.searchParams.get('command'));
    if (url.pathname === '/api/v1/platforms') return jsonResponse({ source: 'synthetic', command: snapshot.fleet.command, platforms: labels });
    if (url.pathname.endsWith('/platforms/series')) return jsonResponse(platformSeries(snapshot, Number(url.searchParams.get('days')) as HistoryWindow, url.searchParams.get('platform')!));
    if (url.pathname.endsWith('/history/platforms')) return jsonResponse(comparison(snapshot));
    if (url.pathname.endsWith('/series')) return jsonResponse(historySeries(snapshot, Number(url.searchParams.get('days')) as HistoryWindow));
    if (url.pathname.endsWith('/commands')) return jsonResponse(snapshot.commands);
    if (url.pathname.endsWith('/fleet')) return jsonResponse(snapshot.fleet);
    if (url.pathname.endsWith('/status-distribution')) return jsonResponse(snapshot.distribution);
    throw new Error('Unexpected fixture route');
  });
  vi.stubGlobal('fetch', mock); return mock;
}
