import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
// import https from 'https'

// set this to dev server url
//TODO: find a way to do this from cli
// const amplipiurl = "http://amplipi10.local/"
const amplipiurl = "http://192.168.0.178/"

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
    // https: false,
    proxy: {
      '/api': {
        target: amplipiurl,
        changeOrigin: true,
        // secure: false,
        // agent: new https.Agent()
      },
      '/static': {
        target: amplipiurl,
        changeOrigin: true,
        // secure: false,
        // agent: new https.Agent()
      }
    }
  },
})
