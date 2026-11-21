import { defineConfig } from '@playwright/test';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: 0,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', channel: 'msedge', headless: true },
  projects: [
    { name: 'desktop', testMatch: 'dashboard.spec.ts', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'tablet-portrait', testMatch: 'dashboard.spec.ts', use: { viewport: { width: 768, height: 1024 } } },
    { name: 'tablet-landscape', testMatch: 'dashboard.spec.ts', use: { viewport: { width: 1024, height: 768 } } },
    { name: 'history-desktop', testMatch: 'history.spec.ts', use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 1440, height: 1000 } } },
    { name: 'history-tablet', testMatch: 'history.spec.ts', use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 768, height: 1024 } } },
    { name: 'history-mobile', testMatch: 'history.spec.ts', use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 390, height: 844 } } },
  ],
  webServer: [
    {
      command: '.\\.venv\\Scripts\\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000',
      cwd: root, url: 'http://127.0.0.1:8000/health', reuseExistingServer: false, timeout: 60000,
    },
    { command: 'npm.cmd run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 60000 },
    { command: '.\\.venv\\Scripts\\python.exe -B frontend\\e2e\\history_backend.py', cwd: root,
      url: 'http://127.0.0.1:8001/health', reuseExistingServer: false, timeout: 120000 },
    { command: 'npm.cmd run dev -- --mode history-demo', url: 'http://127.0.0.1:5174', reuseExistingServer: false, timeout: 60000 },
  ],
});
