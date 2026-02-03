import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/login': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/logout': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/setup': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/preview': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/send-one': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/send-bulk': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
    },
  },
})
