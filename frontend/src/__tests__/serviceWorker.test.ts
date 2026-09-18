import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const serviceWorker = readFileSync(resolve(process.cwd(), "public/sw.js"), "utf8");
const appEntry = readFileSync(resolve(process.cwd(), "src/main.ts"), "utf8");
const indexHtml = readFileSync(resolve(process.cwd(), "index.html"), "utf8");

describe("production service worker", () => {
  it("cache-first serves content-hashed scripts and styles after their first successful fetch", () => {
    expect(serviceWorker).toContain('const CACHE_NAME = "xuexibao-shell-v7";');
    expect(serviceWorker).toMatch(
      /if \(\["script", "style"\]\.includes\(request\.destination\)\) \{\s*event\.respondWith\(\s*caches\.match\(request\)\.then\(\(cached\) => cached \|\| fetch\(request\)/s,
    );
  });

  it("does not let the beta site keep an old application shell after a deployment", () => {
    expect(appEntry).toContain('const isBetaBuild = import.meta.env.VITE_APP_ENV === "beta";');
    expect(appEntry).toContain('if (isBetaBuild && "serviceWorker" in navigator)');
    expect(appEntry).toContain("registration.unregister()");
    expect(appEntry).toContain('key.startsWith("xuexibao-shell-")');
  });

  it("cleans an existing beta service worker before the current module bundle starts", () => {
    expect(indexHtml).toContain('const isBetaHost = location.hostname === "beta.zephyrmyb.xyz";');
    expect(indexHtml).toContain('if ((!isVitePreview && !isBetaHost) || !("serviceWorker" in navigator)) return;');
    expect(indexHtml).toContain("registration.unregister()");
    expect(indexHtml.indexOf("registration.unregister()")).toBeLessThan(indexHtml.indexOf("/src/main.ts"));
  });
});
