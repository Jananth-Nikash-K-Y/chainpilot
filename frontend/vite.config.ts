import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// ChainPilot frontend build configuration.
// Aliases "@" to "src" so feature modules can use clean imports.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Proxy API calls to the backend so the browser stays same-origin.
    // Avoids CORS entirely and sidesteps localhost resolving to ::1 while
    // uvicorn listens on 127.0.0.1.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
