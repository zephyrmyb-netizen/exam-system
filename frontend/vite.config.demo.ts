// Demo-only Vite config: builds the app as ONE self-contained HTML file
// (all JS/CSS inlined) so it can be published to GitHub Pages as a single
// file. Used together with VITE_DEMO=1 / VITE_APP_ENV=beta. The regular
// vite.config.ts is untouched and remains the only config for dev/prod.
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
// @ts-expect-error the base config is a plain defineConfig object
import base from "./vite.config";

const baseConfig = base as {
  plugins?: unknown[];
  build?: Record<string, unknown>;
  [key: string]: unknown;
};

export default defineConfig({
  ...baseConfig,
  plugins: [...((baseConfig.plugins as never[]) || []), viteSingleFile()],
  build: {
    ...baseConfig.build,
    // Top-level await in main.ts (demo bootstrap) needs a modern target.
    target: "es2022",
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    chunkSizeWarningLimit: 4096,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});
