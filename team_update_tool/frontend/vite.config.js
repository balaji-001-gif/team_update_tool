import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://team.update.bizaxl.local:8000',
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://team.update.bizaxl.local:8000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://team.update.bizaxl.local:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../public/frontend'),
    emptyOutDir: true,
    sourcemap: false,
  },
})
