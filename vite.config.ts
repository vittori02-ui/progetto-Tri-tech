import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/skills": "http://127.0.0.1:8000",
      "/users": "http://127.0.0.1:8000",
      "/requests": "http://127.0.0.1:8000",
      "/feedback": "http://127.0.0.1:8000",
    },
  },
});
