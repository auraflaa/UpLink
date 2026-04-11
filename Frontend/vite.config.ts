import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modifyâ€”file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      headers: {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Cross-Origin-Embedder-Policy": "unsafe-none"
      },
      proxy: {
        '/api/main': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        },
        '/api/scheduler': {
          target: 'http://127.0.0.1:8002',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/scheduler/, '')
        },
        '/api/events': {
          target: 'http://127.0.0.1:8003',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/events/, '')
        },
        '/api/embeddings': {
          target: 'http://127.0.0.1:6377',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/embeddings/, '')
        },
        '/api/documents': {
          target: 'http://127.0.0.1:8004',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/documents/, '')
        }
      }
    },
  };
});
