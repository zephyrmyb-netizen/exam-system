import { defineConfig, devices } from "@playwright/test";

const baseURL = "http://127.0.0.1:4180";
const channel = process.env.PLAYWRIGHT_CHANNEL || (process.platform === "win32" ? "msedge" : undefined);
const devCommand = process.platform === "win32"
  ? "npm.cmd run dev -- --host 127.0.0.1 --port 4180 --strictPort"
  : "npm run dev -- --host 127.0.0.1 --port 4180 --strictPort";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: {
    timeout: 8_000,
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.01,
      scale: "css",
    },
  },
  snapshotPathTemplate: "{testDir}/__screenshots__/{projectName}/{arg}{ext}",
  use: {
    ...devices["Desktop Edge"],
    baseURL,
    browserName: "chromium",
    ...(channel ? { channel } : {}),
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
    colorScheme: "light",
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "visual-edge",
      use: { viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: {
    command: devCommand,
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
