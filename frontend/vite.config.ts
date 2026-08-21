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
  },
});
