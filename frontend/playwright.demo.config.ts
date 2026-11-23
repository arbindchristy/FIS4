import { defineConfig } from '@playwright/test';

const baseURL = process.env.FIS4_DEMO_BASE_URL ?? 'http://127.0.0.1:18081';
const target = new URL(baseURL);
if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(target.hostname)
  || target.username || target.password || target.search || target.hash || target.pathname !== '/') {
  throw new Error('Demo verification requires an explicit loopback HTTP origin.');
}

export default defineConfig({
  testDir: './e2e', testMatch: 'demo.spec.ts', workers: 1, retries: 0,
  reporter: 'list',
  use: { baseURL, channel: 'msedge', headless: true },
});
