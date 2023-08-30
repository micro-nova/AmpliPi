import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

// set this to dev server url
// const amplipiurl = "http://192.168.0.117"
// const amplipiurl = "http://192.168.0.178"
// const amplipiurl = "http://192.168.0.119"
// const amplipiurl = "http://172.18.1.194"
const amplipiurl = "http://172.18.1.177"
// const amplipiurl = "http://fe80::4caf:b851:9a24:ffbc"
// const amplipiurl = "http://192.168.0.198"
// const amplipiurl = "http://localhost"

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
      "/static": {
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
