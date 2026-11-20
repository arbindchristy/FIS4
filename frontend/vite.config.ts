import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: {
      '/health': { target: 'http://127.0.0.1:8000' },
      '/api': { target: 'http://127.0.0.1:8000' },
    },
  },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true },
  test: {
    environment: 'jsdom', setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'], maxWorkers: 1,
    restoreMocks: true, unstubGlobals: true,
  },
});
