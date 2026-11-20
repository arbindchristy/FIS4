import { defineConfig } from '@playwright/test';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: 0,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', channel: 'msedge', headless: true },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'tablet-portrait', use: { viewport: { width: 768, height: 1024 } } },
    { name: 'tablet-landscape', use: { viewport: { width: 1024, height: 768 } } },
  ],
  webServer: [
    {
      command: '.\\.venv\\Scripts\\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000',
      cwd: root, url: 'http://127.0.0.1:8000/health', reuseExistingServer: false, timeout: 60000,
    },
    { command: 'npm.cmd run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 60000 },
  ],
});
