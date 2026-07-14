import { mkdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";

import { expect, prepareSurface, surfaces, test, type SurfaceName } from "./visual-fixture";

const referenceRoot = resolve(process.cwd(), "..", "exam-platform-ui", "pages");
const reviewRoot = resolve(process.cwd(), "test-results", "reference-review");

const referenceFiles: Record<SurfaceName, string> = {
  home: "home.html",
  "course-list": "course-list.html",
  "course-practice": "course-practice.html",
  "ai-import": "ai-import.html",
  "exam-take": "exam-take.html",
  "practice-complete": "practice-complete.html",
  "exam-complete": "exam-complete.html",
  mine: "mine.html",
};

test("capture all reference HTML pages next to their Vue implementation", async ({ mockedPage }) => {
  await mkdir(reviewRoot, { recursive: true });

  for (const surface of surfaces) {
    await mockedPage.setViewportSize({ width: 390, height: 844 });
    await prepareSurface(mockedPage, surface.name);
    const implementation = await mockedPage.screenshot({
      fullPage: false,
      animations: "disabled",
      caret: "hide",
      mask: surface.name === "exam-take" ? [mockedPage.locator("[data-exam-countdown]")] : [],
      maskColor: "#e2e8f0",
    });

    const referencePage = await mockedPage.context().newPage();
    await referencePage.setViewportSize({ width: 390, height: 844 });
    const referenceHtml = await readFile(resolve(referenceRoot, referenceFiles[surface.name]), "utf8");
    await referencePage.setContent(referenceHtml, { waitUntil: "load" });
    await referencePage.addStyleTag({
      content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}",
    });
    await referencePage.evaluate(() => document.fonts.ready);
    const reference = await referencePage.screenshot({ fullPage: false, animations: "disabled", caret: "hide" });
    await referencePage.close();

    const compositePage = await mockedPage.context().newPage();
    await compositePage.setViewportSize({ width: 796, height: 844 });
    const referenceSrc = `data:image/png;base64,${reference.toString("base64")}`;
    const implementationSrc = `data:image/png;base64,${implementation.toString("base64")}`;
    await compositePage.setContent(`
      <!doctype html><html><head><meta charset="utf-8"><style>
        *{box-sizing:border-box}html,body{width:796px;height:844px;margin:0;overflow:hidden;background:#0f172a}
        main{display:grid;grid-template-columns:390px 390px;gap:16px;width:796px;height:844px}
        figure{position:relative;width:390px;height:844px;margin:0;overflow:hidden;background:white}
        img{display:block;width:390px;height:844px;object-fit:cover}
        figcaption{position:absolute;top:8px;left:8px;z-index:2;padding:4px 8px;border-radius:999px;background:rgba(15,23,42,.82);color:white;font:700 11px system-ui}
      </style></head><body><main>
        <figure><figcaption>参考 HTML</figcaption><img alt="参考 HTML" src="${referenceSrc}"></figure>
        <figure><figcaption>Vue 实现</figcaption><img alt="Vue 实现" src="${implementationSrc}"></figure>
      </main></body></html>
    `);
    await expect(compositePage.locator("img")).toHaveCount(2);
    await compositePage.screenshot({ path: resolve(reviewRoot, `${surface.name}.png`) });
    await compositePage.close();
  }
});
