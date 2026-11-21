import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import { loadSeries, WINDOWS } from './api';
import { historySeries, historySnapshot, stubHistory } from './test/historyFixtures';
import { jsonResponse, stubApi } from './test/fixtures';

describe('historical series contracts', () => {
  it.each(WINDOWS)('loads and validates the %i-day contract', async days => {
    stubHistory();
    const series = await loadSeries(historySnapshot(), days, new AbortController().signal, vi.fn());
    expect(series.point_count).toBe(days);
    expect(series.observations.at(-1)?.svc_pct).toBe(82.75);
  });
  it.each(['source', 'command', 'end', 'window', 'count', 'order', 'gap', 'status', 'sum', 'percent', 'last', 'extra-status'])('rejects malformed %s responses', async failure => {
    const body = historySeries();
    if (failure === 'source') (body as { source: string }).source = 'other';
    if (failure === 'command') body.command = 'FICTIONAL_B';
    if (failure === 'end') body.end_date = '2026-11-19';
    if (failure === 'window') body.requested_days = 90;
    if (failure === 'count') body.point_count = 31;
    if (failure === 'order') body.observations.reverse();
    if (failure === 'gap') body.observations[1].date = body.observations[0].date;
    if (failure === 'status') delete (body.observations[0].status_counts as Partial<typeof body.observations[0]['status_counts']>).PMCS;
    if (failure === 'sum') body.observations[0].status_counts.FMC = 90;
    if (failure === 'percent') body.observations[0].svc_pct = 101;
    if (failure === 'last') body.observations.at(-1)!.svc_pct = 50;
    if (failure === 'extra-status') Object.assign(body.observations[0].status_counts, { UNKNOWN: 0 });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(body)));
    await expect(loadSeries(historySnapshot(), 30, new AbortController().signal, vi.fn())).rejects.toMatchObject({ kind: 'contract' });
  });
  it('accepts an explicitly clipped interval', async () => {
    const body = historySeries(); body.observations = body.observations.slice(-3); body.point_count = 3; body.start_date = body.observations[0].date;
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(body)));
    expect((await loadSeries(historySnapshot(), 30, new AbortController().signal, vi.fn())).point_count).toBe(3);
  });
  it.each([[404, 'Not Found', 'unsupported'], [404, 'No synthetic snapshot for the requested selection', 'empty'], [503, 'hidden', 'unavailable'], [422, 'hidden', 'invalid']])('distinguishes %s / %s', async (status, detail, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail }, Number(status))));
    await expect(loadSeries(historySnapshot(), 30, new AbortController().signal, vi.fn())).rejects.toMatchObject({ kind });
  });
});

describe('historical dashboard', () => {
  it('defaults to light, toggles dark and preserves data', async () => {
    stubHistory(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability-line');
    expect(screen.getByRole('button', { name: 'Use dark theme' })).toHaveAttribute('aria-pressed', 'false');
    await user.click(screen.getByRole('button', { name: 'Use dark theme' }));
    expect(screen.getByRole('button', { name: 'Use light theme' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('serviceability')).toHaveTextContent('82.8%');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Helicopter');
  });
  it('uses every API observation without smoothing and exposes keyboard/table values', async () => {
    stubHistory(); const user = userEvent.setup(); render(<App />);
    const line = await screen.findByTestId('serviceability-line');
    expect(line.getAttribute('points')?.split(' ')).toHaveLength(30);
    expect(screen.getByTestId('availability-line').getAttribute('points')?.split(' ')).toHaveLength(30);
    expect(screen.getByTestId('trend-detail')).toHaveTextContent('82.8%');
    fireEvent.change(screen.getByLabelText('Inspect historical day'), { target: { value: '1' } });
    expect(screen.getByTestId('trend-detail')).toHaveTextContent('81.8%');
    await user.click(screen.getByText('View daily readiness data (30 days)'));
    expect(screen.getByRole('table')).toBeVisible();
    expect(screen.getAllByRole('row')).toHaveLength(31);
    for (const code of ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT']) expect(screen.getByRole('columnheader', { name: code })).toBeVisible();
  });
  it('keeps reporting date, command and window synchronized', async () => {
    const fetch = stubHistory(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability-line');
    for (const days of WINDOWS) {
      await user.selectOptions(screen.getByLabelText('Historical window'), String(days));
      await waitFor(() => expect(screen.getByTestId('serviceability-line').getAttribute('points')?.split(' ')).toHaveLength(days));
    }
    await user.selectOptions(screen.getByLabelText('Command'), 'FICTIONAL_B');
    fireEvent.change(screen.getByLabelText('Snapshot date'), { target: { value: '2026-10-01' } });
    await user.click(screen.getByRole('button', { name: 'Apply filters' }));
    await screen.findByTestId('serviceability-line');
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain('/api/v1/readiness/history/series?end_date=2026-10-01&days=365&command=FICTIONAL_B');
    expect(screen.getByTestId('trend-detail')).toHaveTextContent('01 Oct 2026');
  });
  it('keeps CSV snapshots usable when history is unsupported', async () => {
    stubApi(); render(<App />);
    await screen.findByText('History not enabled');
    expect(screen.getByTestId('serviceability')).toHaveTextContent('83.3%');
    expect(screen.queryByTestId('serviceability-line')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('handles historical failure and retry without discarding valid snapshot values', async () => {
    const fetch = stubHistory(); const normal = fetch.getMockImplementation()!; let failed = true;
    fetch.mockImplementation((input, init) => String(input).includes('/series') && failed ? Promise.resolve(jsonResponse({ detail: 'hidden' }, 503)) : normal(input, init));
    const user = userEvent.setup(); render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Historical data unavailable');
    expect(screen.getByTestId('serviceability')).toBeVisible();
    failed = false; await user.click(screen.getByRole('button', { name: 'Retry history' }));
    expect(await screen.findByTestId('serviceability-line')).toBeVisible();
  });
  it('blocks SQL reported by a history response and clears all fictional metrics', async () => {
    const fetch = stubHistory(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => String(input).includes('/series') ? Promise.resolve(jsonResponse({ source: 'sql' }, 503, 'sql')) : normal(input, init));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Synthetic mode required');
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SQL');
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  });
  it('shows an explicit empty-history state with no fabricated chart', async () => {
    const fetch = stubHistory(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation((input, init) => String(input).includes('/series')
      ? Promise.resolve(jsonResponse({ ...historySeries(), point_count: 0, observations: [] })) : normal(input, init));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('No historical observations');
    expect(screen.queryByTestId('serviceability-line')).not.toBeInTheDocument();
    expect(screen.getByTestId('serviceability')).toBeVisible();
  });
  it('cancels obsolete windows and ignores late responses even if transport ignores abort', async () => {
    const fetch = stubHistory(); const normal = fetch.getMockImplementation()!;
    let oldSignal: AbortSignal | null | undefined;
    let resolveOld: ((response: Response) => void) | undefined;
    fetch.mockImplementation((input, init) => {
      if (String(input).includes('/series') && String(input).includes('days=30')) {
        oldSignal = init?.signal; return new Promise(resolve => { resolveOld = resolve; });
      }
      return normal(input, init);
    });
    const user = userEvent.setup(); render(<App />);
    await waitFor(() => expect(resolveOld).toBeDefined());
    await user.selectOptions(screen.getByLabelText('Historical window'), '90');
    await screen.findByTestId('serviceability-line');
    expect(oldSignal?.aborted).toBe(true);
    await act(async () => resolveOld?.(jsonResponse(historySeries())));
    expect(screen.getByText('View daily readiness data (90 days)')).toBeVisible();
    expect(screen.getByTestId('serviceability-line').getAttribute('points')?.split(' ')).toHaveLength(90);
  });
});
