import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import { loadDashboard, loadCommandSnapshot, STATUSES } from './api';
import { comparison, stubPlatforms } from './test/platformFixtures';
import { historySnapshot } from './test/historyFixtures';
import { jsonResponse } from './test/fixtures';

const open = async (command: string) => fireEvent.click(await screen.findByText(`Platform breakdown for Command ${command}`));
const row = (command: string) => within(screen.getByLabelText(`Command ${command} readiness`));

describe('command-owned platform intelligence', () => {
  it('renders each command once, NMC count and lazy independent details with unique controls', async () => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation(async (input, init) => {
      const url = new URL(String(input), 'http://localhost');
      if (url.pathname.endsWith('/history/platforms') && url.searchParams.get('command') === 'FICTIONAL_B') {
        const report = comparison(historySnapshot('2026-11-20', 'FICTIONAL_B'));
        report.platforms[0].svc_pct = 31.25;
        return Promise.resolve(jsonResponse(report));
      }
      const response = await normal(input, init);
      if (url.pathname.endsWith('/platforms/series') && url.searchParams.get('command') === 'FICTIONAL_B'
          && url.searchParams.get('platform') === 'AH-64E') {
        const series = await response.json();
        series.observations.forEach((point: { svc_pct: number }) => { point.svc_pct = 31.25; });
        return jsonResponse(series);
      }
      return response;
    });
    const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    expect(screen.getAllByLabelText(/^Command .* readiness$/)).toHaveLength(4);
    expect(fetch.mock.calls.some(call => String(call[0]).includes('platforms'))).toBe(false);
    expect(row('FICTIONAL_A').getByText('NMC Total').nextElementSibling).toHaveTextContent('8');
    await open('FICTIONAL_A');
    await row('FICTIONAL_A').findByTestId('platform-serviceability-line');
    await open('FICTIONAL_B');
    await row('FICTIONAL_B').findByTestId('platform-row-AH-64E');
    expect(row('FICTIONAL_A').getByTestId('platform-row-AH-64E')).toHaveTextContent('17.3%');
    expect(row('FICTIONAL_B').getByTestId('platform-row-AH-64E')).toHaveTextContent('31.3%');
    expect(await row('FICTIONAL_B').findByTestId('platform-trend-detail')).toHaveTextContent('31.3%');
    await user.selectOptions(row('FICTIONAL_A').getByLabelText('Platform', { exact: true }), 'UH-60M');
    await waitFor(() => expect(row('FICTIONAL_A').getByTestId('platform-trend-detail')).toHaveTextContent('91.1%'));
    expect(row('FICTIONAL_B').getByLabelText('Platform', { exact: true })).toHaveValue('AH-64E');
    const ids = Array.from(document.querySelectorAll('[id]'), element => element.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(screen.getByTestId('serviceability')).toHaveTextContent('82.8%');
    expect(screen.getAllByLabelText(/^Command .* readiness$/)).toHaveLength(4);
    expect(document.body.textContent).not.toMatch(/battalion|parent_force/i);
  });

  it.each(['command-count', 'fleet-status', 'selected-command'])('rejects inconsistent %s populations', async fault => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation(async (input, init) => {
      const url = new URL(String(input), 'http://localhost');
      if (fault === 'command-count' && url.pathname.endsWith('/commands') && !url.searchParams.has('command')) {
        const snapshot = historySnapshot(); snapshot.commands.commands[0].nmcm_tails++;
        return jsonResponse(snapshot.commands);
      }
      if (fault === 'fleet-status' && url.pathname.endsWith('/status-distribution') && !url.searchParams.has('command')) {
        const snapshot = historySnapshot(); snapshot.distribution.statuses[0].count--;
        return jsonResponse(snapshot.distribution);
      }
      if (fault === 'selected-command' && url.pathname.endsWith('/fleet') && url.searchParams.has('command')) {
        const snapshot = historySnapshot('2026-11-20', 'FICTIONAL_A'); snapshot.fleet.metrics.nmcm_tails++;
        return jsonResponse(snapshot.fleet);
      }
      return normal(input, init);
    });
    await expect(loadDashboard({ date: '', command: fault === 'selected-command' ? 'FICTIONAL_A' : '' }, new AbortController().signal, vi.fn()))
      .rejects.toMatchObject({ kind: 'contract' });
  });

  it('rejects a command distribution with a PMCM/PMCS population mismatch', async () => {
    const fetch = stubPlatforms(); const snapshot = historySnapshot();
    fetch.mockResolvedValue(jsonResponse({ ...historySnapshot('2026-11-20', 'FICTIONAL_A').distribution,
      statuses: STATUSES.map(status => ({ status, count: 1, pct: 1 })) }));
    await expect(loadCommandSnapshot(snapshot, snapshot.commands.commands[0], new AbortController().signal, vi.fn()))
      .rejects.toMatchObject({ kind: 'contract' });
  });

  it('aborts collapsed details and ignores their late SQL response', async () => {
    const fetch = stubPlatforms(); const normal = fetch.getMockImplementation()!;
    let held: ((response: Response) => void) | undefined; let signal: AbortSignal | null | undefined;
    fetch.mockImplementation((input, init) => {
      if (String(input).includes('/platforms/series?')) {
        signal = init?.signal; return new Promise(resolve => { held = resolve; });
      }
      return normal(input, init);
    });
    render(<App />); await open('FICTIONAL_A');
    await waitFor(() => expect(held).toBeDefined());
    await open('FICTIONAL_A');
    await waitFor(() => expect(signal?.aborted).toBe(true));
    await act(async () => held?.(jsonResponse({ source: 'sql' }, 503, 'sql')));
    expect(row('FICTIONAL_A').queryByTestId('platform-intelligence')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SYNTHETIC');
  });
});
