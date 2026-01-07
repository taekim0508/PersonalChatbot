import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite configuration for the frontend development server.
 *
 * Purpose: Configures build tools, path aliases, and development server settings.
 */

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // Path alias configuration
  // Purpose: Allows importing with @/ prefix instead of relative paths
  // Example: import { something } from '@/api/client' instead of '../../api/client'
  //
  // Why this is useful:
  // - Cleaner imports (no ../../../ paths)
  // - Easier refactoring (move files without breaking imports)
  // - Consistent import style across the codebase
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // Development server configuration
  // Purpose: Configures the Vite dev server (runs on localhost:5173 by default)
  server: {
    // Proxy configuration for API requests
    // Purpose: Routes API requests from frontend to backend during development
    //
    // Why this is needed:
    // - Frontend runs on Vite dev server (different port than backend)
    // - Backend runs on FastAPI server (localhost:8000)
    // - Browser same-origin policy would block direct requests
    // - Proxy makes requests appear to come from same origin
    //
    // How it works:
    // - Frontend makes request to '/chat' (relative URL)
    // - Vite intercepts and forwards to 'http://localhost:8000/chat'
    // - Response is returned to frontend as if it came from same origin
    //
    // Design decisions:
    // - changeOrigin: true - Changes the origin header to match target
    //   (needed for some backends that check origin)
    // - Only proxies /chat - Other routes (like /health) would need separate entries
    //   or we could use a catch-all pattern like '/api/*'
    proxy: {
      "/chat": {
        target: "http://localhost:8000", // Backend FastAPI server URL
        changeOrigin: true, // Changes origin header to match target
      },
      // Optional: Add health check endpoint proxy
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
