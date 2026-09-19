import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Backend Django API'sine dev sirasinda proxy (CORS'u basitlestirmek icin)
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
