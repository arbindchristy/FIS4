import { expect, test, type Locator } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    expect(['127.0.0.1', 'localhost']).toContain(url.hostname);
    return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
  });
});

async function contrast(target: Locator) {
  return target.evaluate(element => {
    const rgb = (text: string) => text.match(/[\d.]+/g)!.slice(0, 3).map(Number);
    const lum = (channels: number[]) => {
      const v = channels.map(channel => { const c = channel / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4; });
      return .2126 * v[0] + .7152 * v[1] + .0722 * v[2];
    };
    let parent: Element | null = element;
    while (parent && ['rgba(0, 0, 0, 0)', 'transparent'].includes(getComputedStyle(parent).backgroundColor)) parent = parent.parentElement;
    const a = lum(rgb(getComputedStyle(element).color));
    const b = lum(rgb(parent ? getComputedStyle(parent).backgroundColor : 'rgb(255,255,255)'));
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  });
}

test('real history values, keyboard chart, six statuses, themes and responsive screenshots', async ({ page }, info) => {
  const response = await page.request.get('/api/v1/readiness/history/series?end_date=2026-11-20&days=30');
  expect(response.status()).toBe(200);
  const series = await response.json();
  await page.goto('/');
  await expect(page.getByTestId('serviceability-line')).toBeVisible();
  await expect(page.getByTestId('serviceability')).toHaveText(`${series.observations.at(-1).svc_pct.toFixed(1)}%`);
  await expect(page.getByLabel('Total tails count')).toContainText('160');
  const points = (await page.getByTestId('serviceability-line').getAttribute('points'))!.split(' ');
  expect(points).toHaveLength(series.point_count);
  points.forEach((point, i) => expect(Number(point.split(',')[1])).toBeCloseTo(20 + (100 - series.observations[i].svc_pct) * 1.8, 6));
  for (const theme of ['light', 'dark']) {
    if (theme === 'dark') await page.getByRole('button', { name: 'Use dark theme' }).click();
    await expect(page.locator('.app-shell')).toHaveAttribute('data-theme', theme);
    for (const target of [page.getByRole('heading', { level: 1 }), page.getByTestId('serviceability'), page.getByTestId('trend-detail'), page.getByLabel('Selected data source')]) {
      expect(await contrast(target)).toBeGreaterThanOrEqual(4.5);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`history-${theme}.png`), fullPage: true });
  }
  const chart = page.getByRole('img', { name: /Daily serviceability and availability/ });
  const box = (await chart.boundingBox())!;
  await chart.hover({ position: { x: box.width * (56 + 888 * 5 / (series.point_count - 1)) / 960, y: box.height / 2 } });
  await expect(page.getByTestId('trend-detail')).toContainText(`${series.observations[5].svc_pct.toFixed(1)}%`);
  await chart.focus(); await page.keyboard.press('Home');
  await expect(page.getByTestId('trend-detail')).toContainText(series.observations[0].svc_pct.toFixed(1));
  await page.keyboard.press('End');
  await expect(page.getByTestId('trend-detail')).toContainText(series.observations.at(-1).svc_pct.toFixed(1));
  await page.getByText('View daily readiness data (30 days)').click();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByRole('row')).toHaveCount(31);
  for (const status of ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT']) {
    await expect(page.getByRole('columnheader', { name: status, exact: true })).toBeVisible();
    await expect(page.getByLabel(`${status} status`, { exact: true })).toBeVisible();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('all windows and command/date filters stay aligned with actual backend snapshots', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('serviceability-line')).toBeVisible();
  for (const days of [30, 90, 180, 365]) {
    await page.getByLabel('Historical window').selectOption(String(days));
    await expect(page.getByText(`View daily readiness data (${days} days)`)).toBeVisible();
  }
  await page.getByLabel('Command', { exact: true }).selectOption('FICTIONAL_C');
  await page.getByLabel('Snapshot date').fill('2024-11-20');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  const body = await (await page.request.get('/api/v1/readiness/fleet?date=2024-11-20&command=FICTIONAL_C')).json();
  await expect(page.getByTestId('serviceability')).toHaveText(`${body.metrics.svc_pct.toFixed(1)}%`);
  await expect(page.getByTestId('trend-detail')).toContainText('20 Nov 2024');
  await expect(page.getByText('View daily readiness data (365 days)')).toBeVisible();
  await expect(page.getByLabel('Total tails count')).toContainText('40');
  await page.getByRole('button', { name: 'Latest snapshot' }).click();
  await expect(page.getByLabel('Total tails count')).toContainText('160');
  await expect(page.getByTestId('trend-detail')).toContainText('20 Nov 2026');
});

test('malformed/unavailable history stays separate from snapshots and SQL remains blocked', async ({ page }) => {
  await page.route('**/api/v1/readiness/history/series?*', route => route.fulfill({ status: 200,
    headers: { 'X-FIS4-Data-Source': 'synthetic' }, contentType: 'application/json', body: JSON.stringify({ source: 'synthetic', observations: [] }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Historical data unavailable');
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await expect(page.getByTestId('serviceability-line')).toHaveCount(0);
  await page.unroute('**/api/v1/readiness/history/series?*');
  await page.getByRole('button', { name: 'Retry history' }).click();
  await expect(page.getByTestId('serviceability-line')).toBeVisible();
  await page.route('**/api/v1/readiness/history/series?*', route => route.abort());
  await page.getByLabel('Historical window').selectOption('90');
  await expect(page.getByRole('alert')).toContainText('Historical data unavailable');
  await page.unroute('**/api/v1/readiness/history/series?*');
  await page.route('**/api/v1/readiness/history/series?*', route => route.fulfill({ status: 503,
    headers: { 'X-FIS4-Data-Source': 'sql' }, contentType: 'application/json', body: JSON.stringify({ source: 'sql' }) }));
  await page.getByRole('button', { name: 'Retry history' }).click();
  await expect(page.getByRole('alert')).toContainText('Synthetic mode required');
  await expect(page.getByLabel('Selected data source')).toHaveText('SQL');
  await expect(page.getByTestId('serviceability')).toHaveCount(0);
});

test('switching windows aborts obsolete requests and ignores a delayed response', async ({ page }) => {
  const original = await (await page.request.get('/api/v1/readiness/history/series?end_date=2026-11-20&days=30')).json();
  let captured = false;
  let cancelled = false;
  let release: () => void = () => {};
  let finish: () => void = () => {};
  const held = new Promise<void>(resolve => { release = resolve; });
  const done = new Promise<void>(resolve => { finish = resolve; });
  page.on('requestfailed', request => {
    const url = new URL(request.url());
    if (url.pathname.endsWith('/series') && url.searchParams.get('days') === '30') cancelled = true;
  });
  await page.route('**/api/v1/readiness/history/series?*', async route => {
    if (new URL(route.request().url()).searchParams.get('days') !== '30') return route.continue();
    captured = true;
    await held;
    try {
      await route.fulfill({ status: 200, headers: { 'X-FIS4-Data-Source': 'synthetic' }, contentType: 'application/json', body: JSON.stringify(original) });
    } catch {
      expect(route.request().failure()).not.toBeNull();
    } finally { finish(); }
  });
  await page.goto('/');
  await expect.poll(() => captured).toBe(true);
  await page.getByLabel('Historical window').selectOption('90');
  await expect(page.getByText('View daily readiness data (90 days)')).toBeVisible();
  await expect.poll(() => cancelled).toBe(true);
  release(); await done;
  await expect(page.getByText('View daily readiness data (90 days)')).toBeVisible();
  expect((await page.getByTestId('serviceability-line').getAttribute('points'))!.split(' ')).toHaveLength(90);
});
