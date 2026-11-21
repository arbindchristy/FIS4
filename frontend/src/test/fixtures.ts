/** Fictional API responses for tests only; never imported by application modules. */
import { vi } from 'vitest';
import type { Commands, Distribution, Fleet, Metrics, Source } from '../api';

const latestMetrics: Metrics = { total_tails: 7, fmc_tails: 3, pmc_tails: 2, nmcs_tails: 0, nmcm_tails: 1, depot_tails: 1, svc_pct: 83.33333333333334, avail_pct: 71.42857142857143 };
const firstMetrics: Metrics = { total_tails: 6, fmc_tails: 1, pmc_tails: 2, nmcs_tails: 1, nmcm_tails: 1, depot_tails: 1, svc_pct: 75, avail_pct: 50 };
const a: Metrics & { command: string } = { command: 'A', total_tails: 3, fmc_tails: 2, pmc_tails: 1, nmcs_tails: 0, nmcm_tails: 0, depot_tails: 0, svc_pct: 100, avail_pct: 100 };
const b: Metrics & { command: string } = { command: 'B', total_tails: 4, fmc_tails: 1, pmc_tails: 1, nmcs_tails: 0, nmcm_tails: 1, depot_tails: 1, svc_pct: 66.66666666666666, avail_pct: 50 };
export const latestFleet: Fleet = { source: 'synthetic', date: '2026-01-03', command: null, metrics: latestMetrics };
export const latestCommands: Commands = { source: 'synthetic', date: '2026-01-03', command: null, commands: [a, b] };
export const latestDistribution: Distribution = { source: 'synthetic', date: '2026-01-03', command: null, total_tails: 7, statuses: [
  { status: 'FMC', count: 3, pct: 42.857142857142854 }, { status: 'PMCM', count: 1, pct: 14.285714285714285 },
  { status: 'PMCS', count: 1, pct: 14.285714285714285 }, { status: 'NMCS', count: 0, pct: 0 },
  { status: 'NMCM', count: 1, pct: 14.285714285714285 }, { status: 'DEPOT', count: 1, pct: 14.285714285714285 },
] };

export function jsonResponse(body: unknown, status = 200, source: Source = 'synthetic'): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'X-FIS4-Data-Source': source } });
}

export function stubApi() {
  const mock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
    const url = new URL(String(input), 'http://127.0.0.1:5173');
    if (url.pathname.endsWith('/history/series')) return jsonResponse({ detail: 'Not Found' }, 404);
    if (url.pathname === '/health') return jsonResponse({ status: 'ok', source: 'synthetic' });
    const date = url.searchParams.get('date') || '2026-01-03';
    const command = url.searchParams.get('command');
    if (!['2026-01-01', '2026-01-02', '2026-01-03'].includes(date)) return jsonResponse({ detail: 'No snapshot' }, 404);
    if (url.pathname.endsWith('/commands')) {
      return jsonResponse({ ...latestCommands, date, command, commands: command ? latestCommands.commands.filter(row => row.command === command) : latestCommands.commands });
    }
    if (url.pathname.endsWith('/fleet')) return jsonResponse({ ...latestFleet, date, command, metrics: command === 'B' ? b : date === '2026-01-03' ? latestMetrics : firstMetrics });
    if (url.pathname.endsWith('/status-distribution')) return jsonResponse({ ...latestDistribution, date, command });
    throw new Error(`Unexpected test URL: ${url.pathname}`);
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}
