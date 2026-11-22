/** Fictional test-only records; deliberately arbitrary API percentages prove display-only behavior. */
import { vi } from 'vitest';
import { STATUSES, type Dashboard, type HistoryWindow, type PlatformRow, type PlatformSeries } from '../api';
import { historySnapshot, stubHistory } from './historyFixtures';
import { jsonResponse } from './fixtures';

export const labels = ['AH-64E', 'UH-60M'];
export const platformPath = (path: string) => path === '/api/v1/platforms' || path.startsWith('/api/v1/readiness/history/platforms');
export function comparison(snapshot = historySnapshot()) {
  const full = snapshot.distribution.statuses.map(row => row.count);
  const rows: PlatformRow[] = labels.map((platform, index) => {
    const counts = full.map(value => index ? value - Math.floor(value / 2) : Math.floor(value / 2));
    return { platform, total_tails: counts.reduce((sum, value) => sum + value, 0), fmc_tails: counts[0],
      pmc_tails: counts[1] + counts[2], nmcs_tails: counts[3], nmcm_tails: counts[4], depot_tails: counts[5],
      svc_pct: index ? 91.125 : 17.25, avail_pct: index ? 58.75 : 12.5,
      status_counts: Object.fromEntries(STATUSES.map((code, i) => [code, counts[i]])) as PlatformRow['status_counts'] };
  });
  return { source: 'synthetic' as const, date: snapshot.fleet.date, command: snapshot.fleet.command, platform: null, platforms: rows };
}
export function platformSeries(snapshot = historySnapshot(), days: HistoryWindow = 30, platform = labels[0]): PlatformSeries {
  const row = comparison(snapshot).platforms.find(row => row.platform === platform)!;
  const { platform: label, ...metrics } = row;
  const observations = Array.from({ length: days }, (_, index) => ({ ...metrics,
    date: new Date(Date.parse(snapshot.fleet.date) - (days - index - 1) * 86400000).toISOString().slice(0, 10) }));
  return { source: 'synthetic', command: snapshot.fleet.command, platform: label, requested_days: days,
    start_date: observations[0].date, end_date: snapshot.fleet.date, point_count: days, observations };
}
export function stubPlatforms() {
  const base = stubHistory().getMockImplementation()!;
  const mock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = new URL(String(input), 'http://127.0.0.1:5174');
    const snapshot = historySnapshot(url.searchParams.get('date') || url.searchParams.get('end_date') || '2026-11-20', url.searchParams.get('command'));
    if (url.pathname === '/api/v1/platforms') return jsonResponse({ source: 'synthetic', command: snapshot.fleet.command, platforms: labels });
    if (url.pathname.endsWith('/platforms/series')) return jsonResponse(platformSeries(snapshot, Number(url.searchParams.get('days')) as HistoryWindow, url.searchParams.get('platform')!));
    if (url.pathname.endsWith('/history/platforms')) return jsonResponse(comparison(snapshot));
    return base(input, init);
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}
export function smallSnapshot(): Dashboard {
  const snapshot = historySnapshot('2026-11-20', 'FICTIONAL_A');
  snapshot.fleet.metrics = { total_tails: 6, fmc_tails: 1, pmc_tails: 2, nmcs_tails: 1, nmcm_tails: 1, depot_tails: 1, svc_pct: 75, avail_pct: 50 };
  snapshot.distribution.total_tails = 6;
  snapshot.distribution.statuses = STATUSES.map(status => ({ status, count: 1, pct: 100 / 6 }));
  return snapshot;
}
