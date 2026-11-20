import { describe, expect, it, vi } from 'vitest';
import { DashboardError, loadDashboard, validDate } from './api';
import { jsonResponse, latestCommands, latestDistribution, latestFleet, stubApi } from './test/fixtures';

const filters = { date: '', command: '' };
const signal = () => new AbortController().signal;

describe('readiness API integration', () => {
  it('resolves latest date from the API, then pins all metric requests to it', async () => {
    const fetch = stubApi();
    const result = await loadDashboard(filters, signal(), vi.fn());
    expect(result.fleet.metrics.svc_pct).toBe(latestFleet.metrics.svc_pct);
    expect(result.availableCommands).toEqual(['A', 'B']);
    expect(fetch.mock.calls.map(call => String(call[0]))).toEqual([
      '/health', '/api/v1/readiness/commands', '/api/v1/readiness/fleet?date=2026-01-03', '/api/v1/status-distribution?date=2026-01-03',
    ]);
    expect(fetch.mock.calls.every(call => call[1]?.credentials === 'omit')).toBe(true);
  });

  it('passes date and command to each selected aggregate without shrinking the command choices', async () => {
    const fetch = stubApi();
    const data = await loadDashboard({ date: '2026-01-03', command: 'B' }, signal(), vi.fn());
    expect(data.availableCommands).toEqual(['A', 'B']);
    expect(data.commands.commands.map(row => row.command)).toEqual(['B']);
    expect(fetch.mock.calls.map(call => call[0])).toContain('/api/v1/readiness/fleet?date=2026-01-03&command=B');
    expect(fetch.mock.calls.map(call => call[0])).toContain('/api/v1/status-distribution?date=2026-01-03&command=B');
  });

  it('reports SQL and blocks every aggregate request when health selects SQL', async () => {
    const fetch = vi.fn().mockResolvedValue(jsonResponse({ status: 'ok', source: 'sql' }, 200, 'sql'));
    vi.stubGlobal('fetch', fetch);
    const source = vi.fn();
    await expect(loadDashboard(filters, signal(), source)).rejects.toMatchObject({ kind: 'source', source: 'sql' });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toBe('/health');
    expect(source).toHaveBeenCalledWith('sql');
  });

  it.each([
    [404, 'empty'], [422, 'invalid'], [500, 'unavailable'], [503, 'unavailable'],
  ])('maps HTTP %i into a safe %s state without disclosing server details', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'FICTIONAL_PRIVATE_SERVER_DETAIL' }, Number(status))));
    try { await loadDashboard(filters, signal(), vi.fn()); throw new Error('Expected failure'); }
    catch (error) {
      expect(error).toBeInstanceOf(DashboardError);
      expect(error).toMatchObject({ kind });
      expect(String(error)).not.toContain('FICTIONAL_PRIVATE_SERVER_DETAIL');
    }
  });

  it('maps network failure into a safe availability error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('FICTIONAL_PRIVATE_NETWORK_DETAIL')));
    await expect(loadDashboard(filters, signal(), vi.fn())).rejects.toMatchObject({ kind: 'unavailable' });
  });

  it('rejects malformed JSON instead of rendering substitute data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>error</html>', { status: 200 })));
    await expect(loadDashboard(filters, signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });

  it('rejects contradictory source headers and body metadata', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok', source: 'synthetic' }), { headers: { 'X-FIS4-Data-Source': 'other' } })));
    await expect(loadDashboard(filters, signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });

  it('rejects invalid calendar dates and command syntax before fetching', async () => {
    const fetch = stubApi();
    for (const invalid of [{ date: '2026-02-30', command: '' }, { date: 'bad', command: '' }, { date: '', command: 'B;bad' }]) {
      await expect(loadDashboard(invalid, signal(), vi.fn())).rejects.toMatchObject({ kind: 'invalid' });
    }
    expect(fetch).not.toHaveBeenCalled();
    expect(validDate('2026-02-28')).toBe(true);
    expect(validDate('0000-01-01')).toBe(false);
  });

  it('does not fetch for an already-cancelled request', async () => {
    const fetch = stubApi();
    const controller = new AbortController(); controller.abort();
    await expect(loadDashboard(filters, controller.signal, vi.fn())).rejects.toMatchObject({ name: 'AbortError' });
    expect(fetch).not.toHaveBeenCalled();
  });

  it('turns a request deadline into a retryable error', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn((_path, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(new DOMException('cancelled', 'AbortError')));
    })));
    const outcome = loadDashboard(filters, signal(), vi.fn()).catch(error => error);
    await vi.advanceTimersByTimeAsync(15001);
    expect(await outcome).toMatchObject({ kind: 'unavailable' });
    vi.useRealTimers();
  });

  it.each(['missing-count', 'bad-percentage', 'wrong-date', 'missing-status', 'duplicate-command'])('rejects broken %s contracts', async failure => {
    const fetch = stubApi();
    const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation(async (input, init) => {
      const path = String(input);
      if (path.includes('/fleet') && failure === 'missing-count') return jsonResponse({ ...latestFleet, metrics: { svc_pct: 75, avail_pct: 50 } });
      if (path.includes('/fleet') && failure === 'bad-percentage') return jsonResponse({ ...latestFleet, metrics: { ...latestFleet.metrics, svc_pct: 101 } });
      if (path.includes('/fleet') && failure === 'wrong-date') return jsonResponse({ ...latestFleet, date: '2026-01-02' });
      if (path.includes('/status-distribution') && failure === 'missing-status') return jsonResponse({ ...latestDistribution, statuses: latestDistribution.statuses.slice(1) });
      if (path.includes('/commands') && failure === 'duplicate-command') return jsonResponse({ ...latestCommands, commands: [latestCommands.commands[0], latestCommands.commands[0]] });
      return normal(input, init);
    });
    await expect(loadDashboard(filters, signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });

  it('handles a valid empty API snapshot explicitly', async () => {
    const fetch = stubApi(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation(async (input, init) => String(input).includes('/commands')
      ? jsonResponse({ ...latestCommands, commands: [] }) : normal(input, init));
    await expect(loadDashboard(filters, signal(), vi.fn())).rejects.toMatchObject({ kind: 'empty' });
  });
});
