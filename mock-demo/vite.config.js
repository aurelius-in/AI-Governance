import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// I configure Vite for the mock demo frontend
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // I proxy API requests to the mock server
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  define: {
    // I set environment variables for the mock demo
    'process.env.VITE_API_URL': JSON.stringify('http://localhost:3001/api/v1'),
    'process.env.VITE_MOCK_MODE': JSON.stringify('true')
  }
})
