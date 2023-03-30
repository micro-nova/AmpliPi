import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// set this to dev server url
//TODO: find a way to do this from cli
const amplipiurl = "http://amplipi13.local/"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: amplipiurl,
        changeOrigin: true
      },
      '/static': {
        target: amplipiurl,
        changeOrigin: true
      }
    }
  },
})
