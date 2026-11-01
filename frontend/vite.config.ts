import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/studio': { target: 'http://localhost:8000', changeOrigin: true },
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/identity': { target: 'http://localhost:8000', changeOrigin: true },
      '/tenants': { target: 'http://localhost:8000', changeOrigin: true },
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/office': { target: 'http://localhost:8000', changeOrigin: true },
      '/departments': { target: 'http://localhost:8000', changeOrigin: true },
      '/teams': { target: 'http://localhost:8000', changeOrigin: true },
      '/tasks': { target: 'http://localhost:8000', changeOrigin: true },
      '/software-projects': { target: 'http://localhost:8000', changeOrigin: true },
      '/meetings': { target: 'http://localhost:8000', changeOrigin: true },
      '/governance': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
});
