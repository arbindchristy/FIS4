import { expect, test, type Locator } from '@playwright/test';

const end = '2026-11-20';
const path = '/api/v1/readiness/history/platforms';
const dateLabel = (day: string) => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${day}T00:00:00Z`));

test.beforeEach(async ({ page }) => {
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    expect(['127.0.0.1', 'localhost']).toContain(url.hostname);
    return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
  });
});

async function contrast(target: Locator) {
  return target.evaluate(element => {
    const lum = (text: string) => {
      const values = text.match(/[\d.]+/g)!.slice(0, 3).map(Number).map(value => {
        const c = value / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
      });
      return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
    };
    let parent: Element | null = element;
    while (parent && ['rgba(0, 0, 0, 0)', 'transparent'].includes(getComputedStyle(parent).backgroundColor)) parent = parent.parentElement;
    const a = lum(getComputedStyle(element).color), b = lum(getComputedStyle(parent!).backgroundColor);
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  });
}

test('actual platform comparisons reconcile, selection preserves fleet and themes/keyboard stay usable', async ({ page }, info) => {
  const rows = await (await page.request.get(`${path}?date=${end}`)).json();
  const options = await (await page.request.get('/api/v1/platforms')).json();
  const fleet = await (await page.request.get(`/api/v1/readiness/fleet?date=${end}`)).json();
  expect(rows.platforms.reduce((sum: number, row: { total_tails: number }) => sum + row.total_tails, 0)).toBe(fleet.metrics.total_tails);
  await page.goto('/');
  const section = page.getByTestId('platform-intelligence');
  await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Fleet Intelligence Dashboard');
  await expect(page).toHaveTitle('Fleet Intelligence Dashboard | Fleet Intelligence Suite');
  await expect(section.getByLabel('Platform', { exact: true }).locator('option')).toHaveText(options.platforms);
  for (const row of rows.platforms) {
    const cells = section.getByTestId(`platform-row-${row.platform}`).getByRole('cell');
    await expect(cells.first()).toHaveText(String(row.total_tails));
    await expect(cells.nth(8)).toHaveText(`${row.svc_pct.toFixed(1)}%`);
    await expect(cells.nth(9)).toHaveText(`${row.avail_pct.toFixed(1)}%`);
  }
  const commandCards = await page.locator('.command-list').textContent();
  const selected = options.platforms[1];
  await section.getByLabel('Platform', { exact: true }).selectOption(selected);
  const series = await (await page.request.get(`${path}/series?end_date=${end}&days=30&platform=${selected}`)).json();
  await expect(section.getByTestId('platform-trend-detail')).toContainText(`${series.observations.at(-1).svc_pct.toFixed(1)}%`);
  await expect(page.getByTestId('serviceability')).toHaveText(`${fleet.metrics.svc_pct.toFixed(1)}%`);
  await expect(page.getByTestId('availability')).toHaveText(`${fleet.metrics.avail_pct.toFixed(1)}%`);
  await expect.poll(() => page.locator('.command-list').textContent()).toBe(commandCards);
  for (const theme of ['light', 'dark']) {
    if (theme === 'dark') await page.getByRole('button', { name: 'Use dark theme' }).click();
    await expect(page.locator('.app-shell')).toHaveAttribute('data-theme', theme);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    for (const target of [section.getByRole('heading', { name: 'Platform Intelligence', exact: true }), section.getByLabel('Platform', { exact: true }), section.getByTestId('platform-trend-detail')]) {
      expect(await contrast(target)).toBeGreaterThanOrEqual(4.5);
    }
    await page.screenshot({ path: info.outputPath(`platform-${theme}.png`), fullPage: true });
    const chart = section.getByRole('img', { name: new RegExp(`Platform ${selected} daily`) });
    await chart.focus(); await page.keyboard.press('Home');
    await expect(section.getByTestId('platform-trend-detail')).toContainText(dateLabel(series.start_date));
    await page.keyboard.press('ArrowRight');
    await expect(section.getByTestId('platform-trend-detail')).toContainText(dateLabel(series.observations[1].date));
    await page.keyboard.press('End');
    await expect(section.getByTestId('platform-trend-detail')).toContainText(dateLabel(end));
  }
  await section.getByText('View platform daily readiness data (30 days)').click();
  const table = section.getByRole('region', { name: 'Platform daily data table' });
  await expect(table.getByRole('row')).toHaveCount(31);
  for (const code of ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT']) await expect(table.getByRole('columnheader', { name: code, exact: true })).toBeVisible();
  await expect(section).not.toContainText(/battalion|parent_force/i);
});

test('command/date/platform and every history window align with backend while overview remains authoritative', async ({ page }) => {
  await page.goto('/');
  const section = page.getByTestId('platform-intelligence');
  await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
  await page.getByLabel('Command', { exact: true }).selectOption('FICTIONAL_B');
  await page.getByLabel('Snapshot date').fill('2024-11-20');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
  await section.getByLabel('Platform', { exact: true }).selectOption('UH-60M');
  const fleet = await (await page.request.get('/api/v1/readiness/fleet?date=2024-11-20&command=FICTIONAL_B')).json();
  for (const days of [30, 90, 180, 365]) {
    await section.getByLabel('Platform historical window').selectOption(String(days));
    const body = await (await page.request.get(`${path}/series?end_date=2024-11-20&days=${days}&platform=UH-60M&command=FICTIONAL_B`)).json();
    await expect(section.getByText(`View platform daily readiness data (${days} days)`)).toBeVisible();
    await expect(section.getByTestId('platform-trend-detail')).toContainText(`${body.observations.at(-1).svc_pct.toFixed(1)}%`);
    const points = (await section.getByTestId('platform-serviceability-line').getAttribute('points'))!.split(' ');
    expect(points).toHaveLength(days);
    points.forEach((point, index) => expect(Number(point.split(',')[1])).toBeCloseTo(20 + (100 - body.observations[index].svc_pct) * 1.8, 6));
    await expect(page.getByLabel('Historical window', { exact: true })).toHaveValue(String(days));
    await expect(page.getByTestId('serviceability')).toHaveText(`${fleet.metrics.svc_pct.toFixed(1)}%`);
    await expect(page.getByTestId('availability')).toHaveText(`${fleet.metrics.avail_pct.toFixed(1)}%`);
    await expect(section.locator('.platform-context')).toContainText('20 Nov 2024');
    await expect(section.locator('.platform-context')).toContainText('FICTIONAL_B');
  }
  await expect(page.getByLabel('Total tails count')).toContainText('40');
});

test('unsupported, network and SQL platform responses stay safe with retry and source blocking', async ({ page }) => {
  await page.route('**/api/v1/platforms*', route => route.fulfill({ status: 404, headers: { 'X-FIS4-Data-Source': 'synthetic' }, contentType: 'application/json', body: JSON.stringify({ detail: 'Not Found' }) }));
  await page.goto('/');
  const section = page.getByTestId('platform-intelligence');
  await expect(section.getByText('Platform Intelligence unavailable')).toBeVisible();
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await expect(page.getByTestId('serviceability-line')).toBeVisible();
  await page.unroute('**/api/v1/platforms*');
  await section.getByRole('button', { name: 'Retry platform data' }).click();
  await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
  await page.route('**/api/v1/readiness/history/platforms/series?*', route => route.abort());
  await section.getByLabel('Platform historical window').selectOption('90');
  await expect(section.getByRole('alert')).toContainText('Platform history unavailable');
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await page.unroute('**/api/v1/readiness/history/platforms/series?*');
  await page.route('**/api/v1/readiness/history/platforms/series?*', route => route.fulfill({ status: 503, headers: { 'X-FIS4-Data-Source': 'sql' }, contentType: 'application/json', body: JSON.stringify({ source: 'sql' }) }));
  await section.getByRole('button', { name: 'Retry platform history' }).click();
  await expect(page.getByRole('alert')).toContainText('Synthetic mode required');
  await expect(page.getByTestId('serviceability')).toHaveCount(0);
  await expect(page.getByLabel('Selected data source')).toHaveText('SQL');
});

test('rapid platform/window changes abort delayed responses and never display obsolete selections', async ({ page }) => {
  const original = await (await page.request.get(`${path}/series?end_date=${end}&days=30&platform=AH-64E`)).json();
  let captured = false; let cancelled = false; let release: () => void = () => {};
  const held = new Promise<void>(resolve => { release = resolve; });
  page.on('requestfailed', request => { if (request.url().includes('/platforms/series?') && request.url().includes('platform=AH-64E')) cancelled = true; });
  await page.route('**/api/v1/readiness/history/platforms/series?*', async route => {
    if (new URL(route.request().url()).searchParams.get('platform') !== 'AH-64E') return route.continue();
    captured = true; await held;
    try { await route.fulfill({ status: 200, headers: { 'X-FIS4-Data-Source': 'synthetic' }, contentType: 'application/json', body: JSON.stringify(original) }); }
    catch { expect(route.request().failure()).not.toBeNull(); }
  });
  try {
    await page.goto('/');
    const section = page.getByTestId('platform-intelligence');
    await expect.poll(() => captured).toBe(true);
    await section.getByLabel('Platform', { exact: true }).selectOption('UH-60M');
    await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
    await expect.poll(() => cancelled).toBe(true);
    await section.getByLabel('Platform historical window').selectOption('90');
    await section.getByLabel('Platform historical window').selectOption('180');
    await expect(section.getByText('View platform daily readiness data (180 days)')).toBeVisible();
    release();
    await expect(section.getByRole('heading', { name: 'Platform history: UH-60M' })).toBeVisible();
    expect((await section.getByTestId('platform-serviceability-line').getAttribute('points'))!.split(' ')).toHaveLength(180);
    await expect(page.getByLabel('Selected data source')).toHaveText('SYNTHETIC');
  } finally { release(); }
});

test.describe('platform mobile touch', () => {
  test.use({ hasTouch: true });
  test('touch swipes scroll the platform plot and comparison table in both themes', async ({ page, context }, info) => {
    test.skip(info.project.name !== 'history-mobile', 'Actual touch overflow case uses the mobile viewport.');
    const input = await context.newCDPSession(page);
    try {
      for (const theme of ['light', 'dark']) {
        await page.goto('/');
        const section = page.getByTestId('platform-intelligence');
        await expect(section.getByTestId('platform-serviceability-line')).toBeVisible();
        if (theme === 'dark') await page.getByRole('button', { name: 'Use dark theme' }).click();
        for (const name of ['Platform trend plot', 'Platform comparison table']) {
          const region = section.getByRole('region', { name, exact: true });
          await region.scrollIntoViewIfNeeded();
          const box = (await region.boundingBox())!;
          const before = await region.evaluate(element => element.scrollLeft);
          const x = box.x + box.width - 24, y = box.y + box.height / 2;
          await input.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y, id: 0 }] });
          for (let step = 1; step <= 12; step++) {
            await input.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x - step * 15, y, id: 0 }] });
            await page.waitForTimeout(20);
          }
          await input.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
          await expect.poll(() => region.evaluate(element => element.scrollLeft)).toBeGreaterThan(before + 60);
        }
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      }
    } finally { await input.detach(); }
  });
});
