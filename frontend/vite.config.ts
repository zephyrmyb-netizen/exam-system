import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

// Paths that exist as both frontend routes AND backend API prefixes.
// For these, we only proxy API requests (XHR/fetch), not page navigations.
const apiPrefixes = [
  "/auth",
  "/courses",
  "/practice",
  "/questions",
  "/wrongbook",
  "/imports",
  "/library",
  "/chat",
  "/exams",
  "/admin",
  "/tags",
  "/recommendations",
  "/analytics",
  "/exports",
  "/bookmarks",
  "/health",
];

function shouldBypassApi(req: { url?: string; headers?: Record<string, string> }): boolean {
  // Let page navigations (HTML requests) fall through to the SPA
  const accept = req.headers?.accept || "";
  if (accept.includes("text/html")) return true;
  return false;
}

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5174,
    proxy: apiPrefixes.reduce((acc, prefix) => {
      acc[prefix] = {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        bypass(req) {
          if (shouldBypassApi(req as { headers?: Record<string, string> })) return req.url;
        },
      };
      return acc;
    }, {} as Record<string, { target: string; changeOrigin: boolean; bypass: (req: { url?: string; headers?: Record<string, string> }) => string | undefined }>),
  },
});
