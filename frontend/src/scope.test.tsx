import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';
import App from './App';
import { STATUSES, WINDOWS } from './api';
import { historySeries } from './test/historyFixtures';
import { jsonResponse } from './test/fixtures';
import { scopeSnapshot, stubScopedHistory } from './test/scopeFixtures';

async function select(command: string) {
  fireEvent.change(await screen.findByLabelText('Command', { exact: true }), { target: { value: command } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
}
async function assertScope(command: string | null, date = '2026-11-20') {
  const snapshot = scopeSnapshot(date, command), m = snapshot.fleet.metrics;
  await waitFor(() => expect(screen.getByTestId('serviceability')).toHaveTextContent(`${m.svc_pct.toFixed(1)}%`));
  expect(screen.getByTestId('availability')).toHaveTextContent(`${m.avail_pct.toFixed(1)}%`);
  expect(screen.getByLabelText('Total tails count').querySelector('p')).toHaveTextContent(String(m.total_tails));
  for (const [label, value] of [['FMC', m.fmc_tails], ['PMC', m.pmc_tails], ['NMCS', m.nmcs_tails], ['NMCM', m.nmcm_tails], ['DEPOT', m.depot_tails]]) {
    expect(screen.getByLabelText(`${label} count`, { exact: true }).querySelector('p')).toHaveTextContent(String(value));
  }
  for (const status of snapshot.distribution.statuses) {
    expect(within(screen.getByLabelText(`${status.status} status`, { exact: true })).getByText(`${status.count}`, { exact: false, selector: 'strong' })).toBeVisible();
  }
  await waitFor(() => expect(screen.getByTestId('trend-detail')).toHaveTextContent(`${m.svc_pct.toFixed(1)}%`));
  if (command) {
    const fleet = scopeSnapshot().fleet.metrics;
    expect(screen.getByTestId('serviceability')).not.toHaveTextContent(`${fleet.svc_pct.toFixed(1)}%`);
    expect(screen.getByTestId('availability')).not.toHaveTextContent(`${fleet.avail_pct.toFixed(1)}%`);
    expect(screen.getByTestId('availability').closest('article')).toHaveTextContent('the selected command');
    expect(screen.getByTestId('availability').closest('article')).not.toHaveTextContent('the total fleet');
    expect(screen.getAllByLabelText(/^Command .* readiness$/)).toHaveLength(1);
    expect(screen.getByRole('heading', { name: new RegExp(`^Command ${command} overview$`) })).toBeVisible();
  }
}

it('selected A, selected B and All Commands use their own API KPIs, six statuses, history and nested platforms', async () => {
  const fetch = stubScopedHistory(); const user = userEvent.setup(); render(<App />);
  await assertScope(null);
  for (const command of ['FICTIONAL_A', 'FICTIONAL_B']) {
    await select(command); await assertScope(command);
    expect(screen.queryByLabelText(`Command ${command === 'FICTIONAL_A' ? 'FICTIONAL_B' : 'FICTIONAL_A'} readiness`)).not.toBeInTheDocument();
    const owner = within(screen.getByLabelText(`Command ${command} readiness`));
    fireEvent.click(owner.getByText(`Platform breakdown for Command ${command}`));
    await owner.findByTestId('platform-serviceability-line');
    await user.selectOptions(owner.getByLabelText('Platform', { exact: true }), 'UH-60M');
    await waitFor(() => expect(owner.getByTestId('platform-trend-detail')).toHaveTextContent('91.1%'));
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain(`/api/v1/readiness/history/series?end_date=2026-11-20&days=30&command=${command}`);
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain(`/api/v1/readiness/history/platforms/series?end_date=2026-11-20&days=30&platform=UH-60M&command=${command}`);
  }
  await select(''); await assertScope(null);
});

it('date and all windows retain command B; All Commands retains date; reset restores latest fleet', async () => {
  const fetch = stubScopedHistory(); const user = userEvent.setup(); render(<App />); await assertScope(null);
  await select('FICTIONAL_B'); await assertScope('FICTIONAL_B');
  fireEvent.change(screen.getByLabelText('Snapshot date'), { target: { value: '2024-11-20' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply filters' })); await assertScope('FICTIONAL_B', '2024-11-20');
  for (const days of WINDOWS) {
    await user.selectOptions(screen.getByLabelText('Historical window', { exact: true }), String(days));
    await waitFor(() => expect(screen.getByTestId('serviceability-line').getAttribute('points')!.split(' ')).toHaveLength(days));
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain(`/api/v1/readiness/history/series?end_date=2024-11-20&days=${days}&command=FICTIONAL_B`);
  }
  await select(''); await assertScope(null, '2024-11-20');
  await select('FICTIONAL_A'); await assertScope('FICTIONAL_A', '2024-11-20');
  fireEvent.click(screen.getByRole('button', { name: 'Latest snapshot' })); await assertScope(null);
  expect(screen.getByLabelText('Command', { exact: true })).toHaveValue('');
  expect(screen.getByLabelText('Snapshot date')).toHaveValue('2026-11-20');
}, 15000);

it.each([404, 422, 503, 'network'])('selected-command failure %s never substitutes fleet values', async fault => {
  const fetch = stubScopedHistory(); const normal = fetch.getMockImplementation()!;
  fetch.mockImplementation((input, init) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname.endsWith('/fleet') && url.searchParams.get('command') === 'FICTIONAL_A') {
      return fault === 'network' ? Promise.reject(new TypeError('offline')) : Promise.resolve(jsonResponse({ detail: 'FICTIONAL_PRIVATE' }, Number(fault)));
    }
    return normal(input, init);
  });
  render(<App />); await assertScope(null); await select('FICTIONAL_A');
  await screen.findByRole('alert');
  expect(screen.getByRole('heading', { name: /^Command FICTIONAL_A overview$/ })).toBeVisible();
  expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  expect(screen.queryByTestId('serviceability-line')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('FMC status')).not.toBeInTheDocument();
  expect(screen.queryByText('FICTIONAL_PRIVATE')).not.toBeInTheDocument();
});

it('switching A to B aborts and ignores a delayed A historical response', async () => {
  const fetch = stubScopedHistory(); const normal = fetch.getMockImplementation()!;
  let heldB: ((response: Response) => void) | undefined;
  let held: ((response: Response) => void) | undefined; let oldSignal: AbortSignal | null | undefined;
  fetch.mockImplementation((input, init) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname.endsWith('/fleet') && url.searchParams.get('command') === 'FICTIONAL_B') return new Promise(resolve => { heldB = resolve; });
    if (url.pathname === '/api/v1/readiness/history/series' && url.searchParams.get('command') === 'FICTIONAL_A') {
      oldSignal = init?.signal; return new Promise(resolve => { held = resolve; });
    }
    return normal(input, init);
  });
  render(<App />); await assertScope(null); await select('FICTIONAL_A');
  await waitFor(() => expect(held).toBeDefined());
  await select('FICTIONAL_B');
  await waitFor(() => expect(heldB).toBeDefined());
  expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  expect(screen.queryByTestId('serviceability-line')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('FMC status')).not.toBeInTheDocument();
  await act(async () => heldB?.(jsonResponse(scopeSnapshot('2026-11-20', 'FICTIONAL_B').fleet)));
  await assertScope('FICTIONAL_B');
  expect(oldSignal?.aborted).toBe(true);
  await act(async () => held?.(jsonResponse(historySeries(scopeSnapshot('2026-11-20', 'FICTIONAL_A')))));
  expect(screen.getByTestId('trend-detail')).toHaveTextContent('64.4%');
  expect(screen.getByTestId('trend-detail')).not.toHaveTextContent('78.1%');
  for (const code of STATUSES) expect(screen.getByLabelText(`${code} status`, { exact: true })).toBeVisible();
});

it('unavailable command B history preserves only B snapshot metrics and never a fleet chart', async () => {
  const fetch = stubScopedHistory(); const normal = fetch.getMockImplementation()!;
  fetch.mockImplementation((input, init) => {
    const url = new URL(String(input), 'http://localhost');
    return url.pathname === '/api/v1/readiness/history/series' && url.searchParams.get('command') === 'FICTIONAL_B'
      ? Promise.resolve(jsonResponse({ detail: 'FICTIONAL_PRIVATE' }, 503)) : normal(input, init);
  });
  render(<App />); await assertScope(null); await select('FICTIONAL_B');
  await waitFor(() => expect(screen.getByTestId('serviceability')).toHaveTextContent('64.4%'));
  expect(await screen.findByRole('alert')).toHaveTextContent('Historical data unavailable');
  expect(screen.queryByTestId('serviceability-line')).not.toBeInTheDocument();
  expect(screen.queryByTestId('trend-detail')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Total tails count')).toHaveTextContent('40');
  expect(screen.queryByLabelText('Command FICTIONAL_A readiness')).not.toBeInTheDocument();
});
