import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"
import process from 'node:process';
// set this to dev server url; this permits one to develop on localhost while
// proxying API requests to an AmpliPi running elsewhere.
const amplipiurl = process.env.AMPLIPI_URL || "http://127.0.0.1";

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // plugins: [react(), 'macros'],
  plugins: [react()],
  // 'fontawesome-svg-core': {
  //   license: 'free'
  // },
  server: {
    host: true,
    proxy: {
      "/api": {
        target: amplipiurl,
        changeOrigin: true,
      },
      "/update": {
        target: amplipiurl + ":5001",
        changeOrigin: true,
      },
    },
  },
})
