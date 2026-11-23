import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import { jsonResponse, latestFleet, stubApi } from './test/fixtures';

describe('readiness dashboard', () => {
  it('shows loading and an unconfirmed source before API evidence arrives', () => {
    vi.stubGlobal('fetch', vi.fn((_path, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(new DOMException('cancelled', 'AbortError')));
    })));
    render(<App />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading readiness');
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SOURCE UNCONFIRMED');
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  });

  it('renders API values, all six canonical statuses and counts including zero', async () => {
    stubApi(); render(<App />);
    expect(await screen.findByTestId('serviceability')).toHaveTextContent('83.3%');
    expect(screen.getByTestId('availability')).toHaveTextContent('71.4%');
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SYNTHETIC');
    expect(screen.getByLabelText('Total tails count')).toHaveTextContent('7');
    expect(screen.getByLabelText('NMCS count')).toHaveTextContent('0');
    expect(screen.getByLabelText('PMC count')).toHaveTextContent('PMCM + PMCS');
    for (const code of ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT']) expect(screen.getByLabelText(`${code} status`)).toBeVisible();
    expect(screen.getAllByRole('meter', { name: 'Serviceability' })).toHaveLength(2);
  });

  it('applies a command filter through API queries and keeps other commands selectable', async () => {
    const fetch = stubApi(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    await user.selectOptions(screen.getByLabelText('Command'), 'B');
    await user.click(screen.getByRole('button', { name: 'Apply filters' }));
    await waitFor(() => expect(screen.getByTestId('serviceability')).toHaveTextContent('83.3%'));
    expect(screen.queryByLabelText('Command A readiness')).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Command A' })).toBeInTheDocument();
    expect(fetch.mock.calls.map(call => String(call[0]))).toContain('/api/v1/readiness/commands?date=2026-01-03&command=B');
  });

  it('applies date selection and resets both filters to the latest API snapshot', async () => {
    stubApi(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    fireEvent.change(screen.getByLabelText('Snapshot date'), { target: { value: '2026-01-01' } });
    await user.click(screen.getByRole('button', { name: 'Apply filters' }));
    await waitFor(() => expect(screen.getByTestId('serviceability')).toHaveTextContent('75.0%'));
    await user.click(screen.getByRole('button', { name: 'Latest snapshot' }));
    await waitFor(() => expect(screen.getByTestId('serviceability')).toHaveTextContent('83.3%'));
    expect(screen.getByLabelText('Snapshot date')).toHaveValue('2026-01-03');
    expect(screen.getByLabelText('Command')).toHaveValue('');
  });

  it.each([[404, 'No data for this selection'], [422, 'Check the filters'], [503, 'Readiness data unavailable']])('displays HTTP %i without stale metrics', async (status, heading) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'PRIVATE_DETAIL' }, Number(status))));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent(String(heading));
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
    expect(screen.queryByText('PRIVATE_DETAIL')).not.toBeInTheDocument();
  });

  it('reports SQL prominently and blocks aggregate requests', async () => {
    const fetch = vi.fn().mockResolvedValue(jsonResponse({ source: 'sql', status: 'ok' }, 200, 'sql'));
    vi.stubGlobal('fetch', fetch); render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Synthetic mode required');
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SQL');
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  });

  it('keeps SQL reported when a late parallel synthetic response follows a source error', async () => {
    const fetch = stubApi(); const normal = fetch.getMockImplementation()!;
    let resolveFleet: ((response: Response) => void) | undefined;
    fetch.mockImplementation(async (input, init) => {
      if (String(input).includes('/fleet')) return new Promise<Response>(resolve => { resolveFleet = resolve; });
      if (String(input).includes('/status-distribution')) return jsonResponse({ source: 'sql' }, 503, 'sql');
      return normal(input, init);
    });
    render(<App />);
    await screen.findByRole('alert');
    await act(async () => resolveFleet?.(jsonResponse(latestFleet)));
    expect(screen.getByLabelText('Selected data source')).toHaveTextContent('SQL');
    expect(screen.queryByTestId('serviceability')).not.toBeInTheDocument();
  });

  it('retries a failed request and renders only real returned values', async () => {
    const fetch = stubApi(); const normal = fetch.getMockImplementation()!;
    fetch.mockRejectedValueOnce(new TypeError('offline'));
    const user = userEvent.setup(); render(<App />);
    await screen.findByRole('alert');
    fetch.mockImplementation(normal);
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByTestId('serviceability')).toHaveTextContent('83.3%');
  });

  it('preserves backend percentages instead of recomputing from counts', async () => {
    const fetch = stubApi(); const normal = fetch.getMockImplementation()!;
    fetch.mockImplementation(async (input, init) => String(input).includes('/fleet')
      ? jsonResponse({ ...latestFleet, metrics: { ...latestFleet.metrics, svc_pct: 61.25, avail_pct: 40.25 } }) : normal(input, init));
    render(<App />);
    expect(await screen.findByTestId('serviceability')).toHaveTextContent('61.3%');
    expect(screen.getByTestId('availability')).toHaveTextContent('40.3%');
  });

  it('exposes labels, skip navigation and keyboard-operable filters', async () => {
    stubApi(); const user = userEvent.setup(); render(<App />);
    await screen.findByTestId('serviceability');
    await user.tab();
    expect(screen.getByRole('link', { name: 'Skip to readiness dashboard' })).toHaveFocus();
    await user.tab();
    expect(screen.getByLabelText('Snapshot date')).toHaveFocus();
    expect(within(screen.getByRole('form', { name: 'Readiness filters' })).getByRole('button', { name: 'Apply filters' })).toBeEnabled();
  });

  it('cancels work on unmount', async () => {
    let requestSignal: AbortSignal | undefined;
    vi.stubGlobal('fetch', vi.fn((_input, init: RequestInit) => {
      requestSignal = init.signal as AbortSignal;
      return new Promise((_resolve, reject) => {
        init.signal?.addEventListener('abort', () => reject(new DOMException('cancelled', 'AbortError')));
      });
    }));
    const view = render(<App />);
    await act(async () => view.unmount());
    expect(requestSignal?.aborted).toBe(true);
  });
});
