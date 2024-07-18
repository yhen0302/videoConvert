import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";


// https://vitejs.dev/config/
export default defineConfig({
  base: "./",
  plugins: [
    vue(),
  ],
  resolve: {
    alias: [
      { find: "@", replacement: path.resolve(__dirname, "./src") },
    ],
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    open: true,
    // 代理
    proxy: {
      "/api": {
        target: "http://10.1.10.49:9001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      }
    }
  }
});
