import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const frontendRoot = process.cwd();
const readFrontendFile = (path: string) => readFileSync(resolve(frontendRoot, path), "utf8");

describe("design foundation", () => {
  it("keeps the canonical design tokens in base.css", () => {
    const baseCss = readFrontendFile("src/styles/base.css");

    for (const token of [
      "--primary:",
      "--glass-card:",
      "--font-sans:",
      "--space-4:",
      "--radius-lg:",
      "--shadow-card:",
      "--safe-area-top:",
      "--shell-max:",
    ]) {
      expect(baseCss, `missing ${token}`).toContain(token);
    }
    const darkBlock = baseCss.match(/html\.dark\s*\{([\s\S]*?)\n\}/)?.[1] || "";
    expect(darkBlock).not.toBe("");
    for (const token of [
      "--primary-glow: rgba(16, 185, 129, 0.28);",
      "--teal-soft: rgba(13, 148, 136, 0.16);",
      "--violet-soft: rgba(124, 58, 237, 0.18);",
      "--amber-strong: #fcd34d;",
      "--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.22);",
      "--shadow-sm: 0 2px 10px rgba(0, 0, 0, 0.24);",
    ]) {
      expect(darkBlock, `missing dark token ${token}`).toContain(token);
    }
    expect(baseCss).toContain("@media (min-width: 760px)");
  });

  it("has no competing root token blocks in legacy stylesheets", () => {
    expect(readFrontendFile("src/style.css")).not.toMatch(/^:root\s*\{/m);
    expect(readFrontendFile("src/styles/liquid-glass.css")).not.toMatch(/^:root\s*\{/m);
  });

  it("self-hosts Noto Sans SC Variable and carries its license", () => {
    const packageJson = JSON.parse(readFrontendFile("package.json"));
    const mainSource = readFrontendFile("src/main.ts");
    const baseCss = readFrontendFile("src/styles/base.css");
    const fontReadme = readFrontendFile("public/fonts/README.md");
    const fontLicense = readFrontendFile("public/fonts/OFL-NotoSansSC.txt");

    expect(packageJson.dependencies["@fontsource-variable/noto-sans-sc"]).toBe("^5.2.10");
    expect(mainSource).toContain('@fontsource-variable/noto-sans-sc/wght.css');
    expect(baseCss).toContain('"Noto Sans SC Variable"');
    expect(baseCss).toContain('"PingFang SC"');
    expect(baseCss).toContain('"Microsoft YaHei"');
    expect(`${mainSource}\n${baseCss}`).not.toMatch(/fonts\.(?:googleapis|gstatic)\.com|@import\s+url\(https?:\/\//i);
    expect(existsSync(`${frontendRoot}/public/fonts/OFL-NotoSansSC.txt`)).toBe(true);
    expect(existsSync(`${frontendRoot}/public/fonts/README.md`)).toBe(true);
    expect(fontReadme).toContain("@fontsource-variable/noto-sans-sc");
    expect(fontReadme).toContain("5.2.10");
    expect(fontReadme).toContain("https://fontsource.org/fonts/noto-sans-sc");
    expect(fontReadme).toContain("https://www.npmjs.com/package/@fontsource-variable/noto-sans-sc");
    expect(fontLicense).toContain("SIL OPEN FONT LICENSE Version 1.1");
    expect(fontLicense).toContain("Google Inc.");
  });
});
