import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import { loadPlatforms, loadPlatformSeries, STATUSES, WINDOWS } from './api';
import { historySnapshot } from './test/historyFixtures';
import { jsonResponse, stubApi } from './test/fixtures';
import { comparison, labels, platformSeries, smallSnapshot, stubPlatforms } from './test/platformFixtures';

const signal = () => new AbortController().signal;
const section = () => within(screen.getByTestId('platform-intelligence'));

describe('platform API contracts', () => {
  it('loads fleet/command lists and comparisons and uses actual populations, including six-tail FIS-001 fixture', async () => {
    for (const snapshot of [historySnapshot(), historySnapshot('2024-11-20', 'FICTIONAL_B'), smallSnapshot()]) {
      const fetch = stubPlatforms();
      const normal = fetch.getMockImplementation()!;
      fetch.mockImplementation((input, init) => String(input).includes('/history/platforms?')
        ? Promise.resolve(jsonResponse(comparison(snapshot))) : normal(input, init));
      const data = await loadPlatforms(snapshot, signal(), vi.fn());
      expect(data.options).toEqual(labels);
      expect(data.rows.reduce((sum, row) => sum + row.total_tails, 0)).toBe(snapshot.fleet.metrics.total_tails);
      for (const code of STATUSES) expect(data.rows.reduce((sum, row) => sum + row.status_counts[code], 0)).toBe(snapshot.distribution.statuses.find(row => row.status === code)!.count);
      expect(fetch.mock.calls.every(call => call[1]?.credentials === 'omit')).toBe(true);
    }
  });
  it.each(WINDOWS)('validates %i daily points and matching platform/date/command metadata', async days => {
    const fetch = stubPlatforms(); const snapshot = historySnapshot('2024-11-20', 'FICTIONAL_C');
    const row = comparison(snapshot).platforms[1];
    const series = await loadPlatformSeries(snapshot, row, days, signal(), vi.fn());
    expect(series.point_count).toBe(days);
    expect(series.observations.at(-1)!.svc_pct).toBe(91.125);
    expect(fetch.mock.calls[0][0]).toBe(`/api/v1/readiness/history/platforms/series?end_date=2024-11-20&days=${days}&platform=UH-60M&command=FICTIONAL_C`);
  });
  it('accepts a clipped window without inferring missing days or percentages', async () => {
    const body = platformSeries(); body.observations = body.observations.slice(-2); body.point_count = 2; body.start_date = body.observations[0].date;
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(body)));
    expect((await loadPlatformSeries(historySnapshot(), comparison().platforms[0], 30, signal(), vi.fn())).point_count).toBe(2);
  });
  it.each(['date', 'command', 'filtered', 'source', 'total', 'count', 'fraction', 'pmc', 'missing-status', 'extra-status', 'percent', 'missing-field', 'duplicate', 'unknown-label', 'internal', 'status-partition'])('rejects malformed comparison: %s', async fault => {
    const body = comparison(); const row = body.platforms[0];
    if (fault === 'date') body.date = '2026-11-19';
    if (fault === 'command') body.command = 'FICTIONAL_B';
    if (fault === 'filtered') Object.assign(body, { platform: labels[0] });
    if (fault === 'source') Object.assign(body, { source: 'unknown' });
    if (fault === 'total') row.total_tails++;
    if (fault === 'count') row.fmc_tails = -1;
    if (fault === 'fraction') row.nmcm_tails = 1.5;
    if (fault === 'pmc') row.pmc_tails++;
    if (fault === 'missing-status') delete (row.status_counts as Partial<typeof row.status_counts>).PMCS;
    if (fault === 'extra-status') Object.assign(row.status_counts, { UNKNOWN: 0 });
    if (fault === 'percent') row.svc_pct = NaN;
    if (fault === 'missing-field') delete (row as Partial<typeof row>).avail_pct;
    if (fault === 'duplicate') body.platforms[1].platform = row.platform;
    if (fault === 'unknown-label') row.platform = 'UNKNOWN';
    if (fault === 'internal') Object.assign(row, { battalion: 'FICTIONAL_PRIVATE_MARKER' });
    if (fault === 'status-partition') { row.status_counts.PMCM++; row.status_counts.PMCS--; }
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => String(input).includes('/history/platforms?') ? Promise.resolve(jsonResponse(body)) : normal(input, init));
    await expect(loadPlatforms(historySnapshot(), signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });
  it.each(['duplicate', 'unsorted', 'label', 'too-many', 'command', 'source', 'internal'])('rejects invalid platform list: %s', async fault => {
    const body = { source: 'synthetic', command: null as string | null, platforms: [...labels] };
    if (fault === 'duplicate') body.platforms = [labels[0], labels[0]];
    if (fault === 'unsorted') body.platforms.reverse();
    if (fault === 'label') body.platforms[0] = 'bad platform';
    if (fault === 'too-many') body.platforms = Array.from({ length: 33 }, (_, i) => `P-${i}`);
    if (fault === 'command') body.command = 'FICTIONAL_A';
    if (fault === 'source') body.source = 'unknown';
    if (fault === 'internal') Object.assign(body, { battalion: 'FICTIONAL_PRIVATE_MARKER' });
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => String(input) === '/api/v1/platforms' ? Promise.resolve(jsonResponse(body)) : normal(input, init));
    await expect(loadPlatforms(historySnapshot(), signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });
  it.each(['platform', 'command', 'end', 'start', 'window', 'count', 'order', 'gap', 'status', 'percent', 'last', 'last-status', 'too-many', 'internal'])('rejects malformed platform series: %s', async fault => {
    const body = platformSeries();
    if (fault === 'platform') body.platform = labels[1];
    if (fault === 'command') body.command = 'FICTIONAL_B';
    if (fault === 'end') body.end_date = '2026-11-19';
    if (fault === 'start') body.start_date = '2026-02-30';
    if (fault === 'window') body.requested_days = 90;
    if (fault === 'count') body.point_count++;
    if (fault === 'order') body.observations.reverse();
    if (fault === 'gap') body.observations[1].date = body.observations[0].date;
    if (fault === 'status') body.observations[0].status_counts.NMCS = -1;
    if (fault === 'percent') body.observations[0].avail_pct = Infinity;
    if (fault === 'last') body.observations.at(-1)!.svc_pct++;
    if (fault === 'last-status') { body.observations.at(-1)!.status_counts.PMCM++; body.observations.at(-1)!.status_counts.PMCS--; }
    if (fault === 'too-many') body.observations = Array(366).fill(body.observations[0]);
    if (fault === 'internal') Object.assign(body.observations[0], { battalion: 'FICTIONAL_PRIVATE_MARKER' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(body)));
    await expect(loadPlatformSeries(historySnapshot(), comparison().platforms[0], 30, signal(), vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });
  it.each([[404, 'Not Found', 'unsupported'], [404, 'No selection', 'empty'], [422, 'hidden', 'invalid'], [503, 'hidden', 'unavailable']])('handles HTTP %i safely', async (status, detail, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(jsonResponse({ detail }, Number(status)))));
    await expect(loadPlatforms(historySnapshot(), signal(), vi.fn())).rejects.toMatchObject({ kind });
  });
  it.each(['missing-header', 'mismatch', 'malformed-json', 'oversize-stream', 'oversize-header', 'network'])('rejects transport violation: %s', async fault => {
    const body = comparison();
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => {
      if (!String(input).includes('/history/platforms?')) return normal(input, init);
      if (fault === 'network') return Promise.reject(new TypeError('FICTIONAL_PRIVATE_MARKER'));
      if (fault === 'missing-header') return Promise.resolve(new Response(JSON.stringify(body)));
      if (fault === 'mismatch') return Promise.resolve(jsonResponse({ ...body, source: 'unknown' }));
      if (fault === 'malformed-json') return Promise.resolve(new Response('FICTIONAL_PRIVATE_MARKER', { headers: { 'X-FIS4-Data-Source': 'synthetic' } }));
      return Promise.resolve(new Response(fault === 'oversize-stream' ? ' '.repeat(262145) : JSON.stringify(body),
        { headers: { 'X-FIS4-Data-Source': 'synthetic', ...(fault === 'oversize-header' ? { 'Content-Length': '262145' } : {}) } }));
    });
    await expect(loadPlatforms(historySnapshot(), signal(), vi.fn())).rejects.toMatchObject({ kind: fault === 'network' ? 'unavailable' : 'contract' });
  });
  it('blocks SQL in header or body, including malformed SQL-header responses', async () => {
    for (const response of [jsonResponse({ source: 'sql' }, 503, 'sql'), jsonResponse({ source: 'sql' }),
      new Response('not json', { headers: { 'X-FIS4-Data-Source': 'sql' } })]) {
      const report = vi.fn(); vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(response.clone())));
      await expect(loadPlatforms(historySnapshot(), signal(), report)).rejects.toMatchObject({ kind: 'source' });
      expect(report).toHaveBeenCalledWith('sql');
    }
  });
  it('rejects a pre-aborted request without fetching and handles empty data explicitly', async () => {
    const fetch = stubPlatforms(); const controller = new AbortController(); controller.abort();
    await expect(loadPlatforms(historySnapshot(), controller.signal, vi.fn())).rejects.toMatchObject({ name: 'AbortError' });
    expect(fetch).not.toHaveBeenCalled();
    fetch.mockImplementation(input => Promise.resolve(jsonResponse(String(input) === '/api/v1/platforms'
      ? { source: 'synthetic', command: null, platforms: [] } : { ...comparison(), platforms: [] })));
    await expect(loadPlatforms(historySnapshot(), signal(), vi.fn())).rejects.toMatchObject({ kind: 'empty' });
  });
});

describe('platform dashboard integration', () => {
  it('shows API percentages verbatim, all statuses, identity and independent platform selection', async () => {
    const fetch = stubPlatforms(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await screen.findByTestId('platform-intelligence');
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Fleet Intelligence Dashboard');
    expect(screen.getAllByText('Fleet Intelligence Suite').length).toBeGreaterThan(0);
    expect(screen.getByLabelText('Demonstration scope')).toHaveTextContent('authentication is not implemented');
    expect(section().getByTestId('platform-row-AH-64E')).toHaveTextContent('17.3%');
    for (const code of STATUSES) expect(within(section().getByRole('region', { name: 'Platform comparison table' })).getByRole('columnheader', { name: new RegExp(`^${code}$`) })).toBeVisible();
    const fleet = screen.getByTestId('serviceability').textContent;
    const availability = screen.getByTestId('availability').textContent;
    const commandCards = screen.getAllByLabelText(/^Command .* readiness$/).map(node => node.querySelector('.command-summary')?.textContent);
    const overviewCalls = fetch.mock.calls.filter(call => String(call[0]).includes('/fleet?')).length;
    await user.selectOptions(screen.getByLabelText('Platform', { exact: true }), labels[1]);
    await waitFor(() => expect(section().getByTestId('platform-trend-detail')).toHaveTextContent('91.1%'));
    expect(screen.getByTestId('serviceability').textContent).toBe(fleet);
    expect(screen.getByTestId('availability').textContent).toBe(availability);
    expect(screen.getAllByLabelText(/^Command .* readiness$/).map(node => node.querySelector('.command-summary')?.textContent)).toEqual(commandCards);
    expect(fetch.mock.calls.filter(call => String(call[0]).includes('/fleet?'))).toHaveLength(overviewCalls);
    await user.click(screen.getByRole('button', { name: 'Use dark theme' }));
    expect(screen.getByRole('button', { name: 'Use light theme' })).toHaveAttribute('aria-pressed', 'true');
    expect(section().queryByText(/battalion|FICTIONAL_PRIVATE_MARKER/i)).not.toBeInTheDocument();
  });
  it('synchronizes command overview, date, platform and both window controls', async () => {
    const fetch = stubPlatforms(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await screen.findByTestId('platform-intelligence');
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line');
    for (const days of WINDOWS) {
      await user.selectOptions(screen.getByLabelText('Platform historical window'), String(days));
      await waitFor(() => expect(section().getByTestId('platform-serviceability-line').getAttribute('points')!.split(' ')).toHaveLength(days));
      expect(screen.getByLabelText('Historical window', { exact: true })).toHaveValue(String(days));
    }
    await user.selectOptions(screen.getByLabelText('Command', { exact: true }), 'FICTIONAL_B');
    fireEvent.change(screen.getByLabelText('Snapshot date'), { target: { value: '2024-11-20' } });
    await user.click(screen.getByRole('button', { name: 'Apply filters' }));
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_B'));
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line');
    expect(screen.getByLabelText('Total tails count')).toHaveTextContent('40');
    expect(within(section().getByRole('region', { name: 'Platform comparison table' })).getByRole('caption')).toHaveTextContent('20 Nov 2024');
    await user.selectOptions(screen.getByLabelText('Platform', { exact: true }), labels[1]);
    await waitFor(() => expect(section().getByTestId('platform-trend-detail')).toHaveTextContent('91.1%'));
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain('/api/v1/readiness/history/platforms/series?end_date=2024-11-20&days=365&platform=UH-60M&command=FICTIONAL_B');
    expect(screen.getByTestId('serviceability')).toHaveTextContent('82.8%');
  }, 15000);
  it('contains malformed/HTTP/network failures, retries and never renders raw/internal details', async () => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!; let broken = true;
    fetch.mockImplementation((input, init) => String(input).includes('/history/platforms?') && broken
      ? Promise.resolve(jsonResponse({ ...comparison(), battalion: 'FICTIONAL_PRIVATE_MARKER' })) : normal(input, init));
    const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await screen.findByTestId('platform-intelligence');
    await within(await screen.findByTestId('platform-intelligence')).findByRole('alert');
    expect(screen.queryByText('FICTIONAL_PRIVATE_MARKER')).not.toBeInTheDocument();
    expect(screen.getByTestId('serviceability')).toBeVisible();
    expect(screen.getByTestId('serviceability-line')).toBeVisible();
    expect(section().queryByRole('table')).not.toBeInTheDocument();
    broken = false; await user.click(section().getByRole('button', { name: 'Retry platform data' }));
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line');
  });
  it('keeps CSV snapshot/history unsupported states contained and blocks later SQL platform responses', async () => {
    stubApi(); const first = render(<App />);
    await screen.findByTestId('serviceability');
    fireEvent.click(await screen.findByText('Platform breakdown for Command A'));
    await screen.findByTestId('platform-intelligence');
    await within(await screen.findByTestId('platform-intelligence')).findByText('Platform Intelligence unavailable');
    expect(screen.getByTestId('serviceability')).toHaveTextContent('83.3%');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument(); first.unmount();
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => String(input).includes('/platforms/series?') ? Promise.resolve(jsonResponse({ source: 'sql' }, 503, 'sql')) : normal(input, init));
    render(<App />);
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await screen.findByText('Synthetic mode required');
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SQL');
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
    expect(screen.queryByTestId('platform-intelligence')).not.toBeInTheDocument();
  });
  it('cancels old platform/window history and ignores a late SQL response from an aborted request', async () => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    let held: ((value: Response) => void) | undefined; let oldSignal: AbortSignal | null | undefined;
    fetch.mockImplementation((input, init) => {
      if (String(input).includes('/platforms/series?') && String(input).includes('days=30')) {
        oldSignal = init?.signal; return new Promise(resolve => { held = resolve; });
      }
      return normal(input, init);
    });
    const user = userEvent.setup(); render(<App />);
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await waitFor(() => expect(held).toBeDefined());
    await user.selectOptions(screen.getByLabelText('Platform historical window'), '90');
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line'); expect(oldSignal?.aborted).toBe(true);
    await act(async () => held?.(jsonResponse({ source: 'sql' }, 503, 'sql')));
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SYNTHETIC');
    expect(section().getByTestId('platform-serviceability-line').getAttribute('points')!.split(' ')).toHaveLength(90);
  });
  it('invalidates delayed comparison responses on snapshot/command changes', async () => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    let held: ((value: Response) => void) | undefined; let oldSignal: AbortSignal | null | undefined;
    fetch.mockImplementation((input, init) => {
      if (String(input) === '/api/v1/readiness/history/platforms?date=2026-11-20&command=FICTIONAL_A') {
        oldSignal = init?.signal; return new Promise(resolve => { held = resolve; });
      }
      return normal(input, init);
    });
    const user = userEvent.setup(); render(<App />); fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A')); await waitFor(() => expect(held).toBeDefined());
    await user.selectOptions(screen.getByLabelText('Command', { exact: true }), 'FICTIONAL_A');
    fireEvent.change(screen.getByLabelText('Snapshot date'), { target: { value: '2024-11-20' } });
    await user.click(screen.getByRole('button', { name: 'Apply filters' }));
    fireEvent.click(await screen.findByText('Platform breakdown for Command FICTIONAL_A'));
    await within(await screen.findByTestId('platform-intelligence')).findByTestId('platform-serviceability-line'); expect(oldSignal?.aborted).toBe(true);
    await act(async () => held?.(jsonResponse(comparison())));
    expect(within(section().getByRole('region', { name: 'Platform comparison table' })).getByRole('caption')).toHaveTextContent('20 Nov 2024');
    expect(within(section().getByRole('region', { name: 'Platform comparison table' })).getByRole('caption')).toHaveTextContent('FICTIONAL_A');
    expect(screen.getByLabelText('Total tails count')).toHaveTextContent('40');
  });
});
