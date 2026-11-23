import { test, expect } from '@playwright/test';

test('compiled React assets, root and direct dashboard refresh use only this origin', async ({ page, baseURL }) => {
 const outside: string[] = [];
 page.on('request', request => { if (new URL(request.url()).origin !== new URL(baseURL!).origin) outside.push(request.url()); });
 for (const path of ['/', '/dashboard']) {
  const response = await page.goto(path); expect(response?.status()).toBe(200);
  await expect(page.getByTestId('serviceability')).toHaveText('94.6%');
  expect(await page.locator('script[src]').first().getAttribute('src')).toMatch(/^\/assets\/.*\.js$/);
  await page.reload(); await expect(page.getByTestId('availability')).toHaveText('88.1%');
  await page.getByLabel('Command', { exact: true }).selectOption('FICTIONAL_A');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.getByTestId('serviceability')).toHaveText('92.3%');
 }
 expect(outside).toEqual([]);
});

test('only fictional read-only API and compiled UI surfaces are exposed', async ({ request }) => {
 for (const path of ['/docs', '/redoc', '/openapi.json', '/.env', '/requirements.txt', '/demo_server.py', '/readiness.py',
 '/api/unknown', '/simulator/generator.py', '/assets/../../demo_server.py', '/assets/no-file.js']) {
  const response = await request.get(path); expect(response.status(), path).toBe(404);
  expect(await response.text()).not.toMatch(/Traceback|SECRET|BEGIN PRIVATE KEY/);
 }
 const invalid = await request.get('/api/v1/readiness/fleet?command=UNTRUSTED_MARKER');
 expect(invalid.status()).toBe(404); expect(await invalid.text()).not.toContain('UNTRUSTED_MARKER');
 const malformed = await request.get('/api/v1/readiness/fleet?command=%3CUNTRUSTED_MARKER%3E');
 expect(malformed.status()).toBe(422); expect(await malformed.text()).not.toContain('UNTRUSTED_MARKER');
 const response = await request.get('/api/v1/readiness/commands?date=2026-11-20');
 const body = await response.json(); expect(body.source).toBe('synthetic');
 expect(body.commands.map((row: { command: string }) => row.command)).toEqual(['FICTIONAL_A','FICTIONAL_B','FICTIONAL_C','FICTIONAL_D']);
 expect(JSON.stringify(body)).not.toMatch(/battalion|password|username|server|database/i);
 expect((await request.post('/api/v1/readiness/fleet')).status()).toBe(405);
});
