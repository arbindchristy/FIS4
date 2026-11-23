import { expect, test, type Page } from '@playwright/test';

const externalRequests = new WeakMap<Page, string[]>();

test.beforeEach(async ({ page }) => {
  const outside: string[] = [];
  externalRequests.set(page, outside);
  page.on('request', request => {
    const url = new URL(request.url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) outside.push(url.origin);
  });
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.hostname === '127.0.0.1' || url.hostname === 'localhost' ? route.continue() : route.abort();
  });
});

test.afterEach(async ({ page }) => {
  expect(externalRequests.get(page)).toEqual([]);
});

test('live synthetic dashboard displays backend values, statuses and responsive panels', async ({ page }, info) => {
  const api = await page.request.get('/api/v1/readiness/fleet');
  expect(api.status()).toBe(200);
  const body = await api.json();
  expect(body.source).toBe('synthetic');
  await page.goto('/');
  await expect(page.getByLabel('Selected data source')).toHaveText('SYNTHETIC');
  await expect(page.getByTestId('serviceability')).toHaveText(`${body.metrics.svc_pct.toFixed(1)}%`);
  await expect(page.getByTestId('availability')).toHaveText(`${body.metrics.avail_pct.toFixed(1)}%`);
  await expect(page.getByLabel('Total tails count')).toContainText(String(body.metrics.total_tails));
  for (const status of ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT']) await expect(page.getByLabel(`${status} status`, { exact: true })).toBeVisible();
  const panels = await page.locator('.report-grid').evaluate(element => ({ columns: getComputedStyle(element).gridTemplateColumns, width: element.clientWidth }));
  expect(panels.width).toBeGreaterThan(500);
  if (info.project.name === 'desktop') expect(panels.columns.split(' ')).toHaveLength(2);
  else expect(panels.columns.split(' ')).toHaveLength(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath('dashboard.png'), fullPage: true });
});

test('date and command filters use the live backend; reset restores latest', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('serviceability')).toHaveText('83.3%');
  await page.getByLabel('Snapshot date').fill('2026-01-01');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByTestId('serviceability')).toHaveText('75.0%');
  await expect(page.getByTestId('availability')).toHaveText('50.0%');
  await page.getByRole('button', { name: 'Latest snapshot' }).click();
  await expect(page.getByTestId('serviceability')).toHaveText('83.3%');
  await page.getByLabel('Command', { exact: true }).selectOption('B');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByTestId('serviceability')).toHaveText('83.3%');
  await expect(page.getByTestId('availability')).toHaveText('71.4%');
  await expect(page.getByLabel('Command A readiness')).toHaveCount(0);
  await expect(page.getByLabel('Total tails count')).toContainText('7');
  await page.getByRole('button', { name: 'Latest snapshot' }).click();
  await expect(page.getByLabel('Command A readiness')).toBeVisible();
});

test('empty selections and backend errors clear metrics and recover', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await page.getByLabel('Snapshot date').fill('2030-01-01');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByRole('alert')).toContainText('No data for this selection');
  await expect(page.getByTestId('serviceability')).toHaveCount(0);
  await page.getByRole('button', { name: 'Latest snapshot' }).click();
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await page.route('**/api/v1/**', route => route.abort());
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByRole('alert')).toContainText('Readiness data unavailable');
  await expect(page.getByTestId('serviceability')).toHaveCount(0);
  await page.unroute('**/api/v1/**');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByTestId('serviceability')).toBeVisible();
});

test('invalid-filter errors are readable; SQL health blocks aggregates', async ({ page }) => {
  await page.route('**/health', route => route.fulfill({ status: 422, contentType: 'application/json', headers: { 'X-FIS4-Data-Source': 'synthetic' }, body: JSON.stringify({ detail: 'FICTIONAL_PRIVATE_DETAIL' }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Check the filters');
  await expect(page.getByText('FICTIONAL_PRIVATE_DETAIL')).toHaveCount(0);
  await page.unroute('**/health');
  let aggregateRequests = 0;
  page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/v1/')) aggregateRequests++; });
  await page.route('**/health', route => route.fulfill({ status: 200, contentType: 'application/json', headers: { 'X-FIS4-Data-Source': 'sql' }, body: JSON.stringify({ status: 'ok', source: 'sql' }) }));
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByLabel('Selected data source')).toHaveText('SQL');
  await expect(page.getByRole('alert')).toContainText('Synthetic mode required');
  expect(aggregateRequests).toBe(0);
});

test('keyboard navigation and tablet controls remain usable', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('serviceability')).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to readiness dashboard' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Snapshot date')).toBeFocused();
  const command = page.getByLabel('Command', { exact: true });
  await expect(command).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Apply filters' })).toBeEnabled();
  const size = await command.boundingBox();
  expect(size?.height).toBeGreaterThanOrEqual(44);
  for (const target of [page.getByLabel('Selected data source'), page.getByTestId('serviceability'), page.getByLabel('NMCS count').locator('h2')]) {
    const contrast = await target.evaluate(element => {
      const rgb = (text: string) => text.match(/[\d.]+/g)!.slice(0, 3).map(Number);
      const luminance = (channels: number[]) => {
        const linear = channels.map(channel => { const value = channel / 255; return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4; });
        return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2];
      };
      let parent: Element | null = element;
      while (parent && ['rgba(0, 0, 0, 0)', 'transparent'].includes(getComputedStyle(parent).backgroundColor)) parent = parent.parentElement;
      const foreground = luminance(rgb(getComputedStyle(element).color));
      const background = luminance(rgb(parent ? getComputedStyle(parent).backgroundColor : 'rgb(255, 255, 255)'));
      return (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05);
    });
    expect(contrast).toBeGreaterThanOrEqual(4.5);
  }
});
