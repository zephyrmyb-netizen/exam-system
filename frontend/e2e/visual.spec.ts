import { expect, prepareSurface, surfaces, test, type SurfaceName } from "./visual-fixture";

function dynamicMasks(page: Parameters<typeof prepareSurface>[0], surface: SurfaceName) {
  return surface === "exam-take" ? [page.locator("[data-exam-countdown]")] : [];
}

test.describe("390x844 reference UI baselines", () => {
  for (const surface of surfaces) {
    test(surface.name, async ({ mockedPage }) => {
      await prepareSurface(mockedPage, surface.name);
      await expect(mockedPage).toHaveScreenshot(`${surface.name}.png`, {
        fullPage: false,
        mask: dynamicMasks(mockedPage, surface.name),
        maskColor: "#e2e8f0",
      });
    });
  }
});

test.describe("responsive overflow and safe bottom content", () => {
  for (const viewport of [{ width: 320, height: 720 }, { width: 420, height: 900 }]) {
    for (const surface of surfaces) {
      test(`${surface.name} at ${viewport.width}x${viewport.height}`, async ({ mockedPage }) => {
        await mockedPage.setViewportSize(viewport);
        await prepareSurface(mockedPage, surface.name);

        const overflow = await mockedPage.evaluate(() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: document.documentElement.clientWidth,
          bodyWidth: document.body.scrollWidth,
        }));
        expect(overflow.documentWidth, "document must not overflow horizontally").toBeLessThanOrEqual(overflow.viewportWidth);
        expect(overflow.bodyWidth, "body must not overflow horizontally").toBeLessThanOrEqual(overflow.viewportWidth);

        await mockedPage.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await mockedPage.waitForTimeout(30);
        const nav = mockedPage.locator(".bottom-nav");
        if (await nav.isVisible()) {
          const navBox = await nav.boundingBox();
          const pageId = surfaces.find((item) => item.name === surface.name)?.referencePage;
          const pageBox = pageId
            ? await mockedPage.locator(`[data-reference-page='${pageId}']`).boundingBox()
            : null;
          if (navBox && pageBox) {
            expect(pageBox.y + pageBox.height, "scrolled content must end above the bottom nav")
              .toBeLessThanOrEqual(navBox.y - 2);
          }
        }
      });
    }
  }
});

test.describe("dark mode smoke baselines", () => {
  for (const [surface, path] of [
    ["home", "/"],
    ["course-list", "/courses"],
    ["ai-import", "/import"],
    ["mine", "/mine"],
  ] as const) {
    test(`${surface} dark`, async ({ mockedPage }) => {
      await mockedPage.addInitScript(() => window.localStorage.setItem("xuexibao-theme", "dark"));
      await mockedPage.goto(path);
      const pageId = surfaces.find((item) => item.name === surface)?.referencePage;
      await expect(mockedPage.locator(`[data-reference-page='${pageId}']`)).toBeVisible();
      await mockedPage.evaluate(() => document.fonts.ready);
      await mockedPage.addStyleTag({
        content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}",
      });
      await expect(mockedPage.locator("html")).toHaveClass(/dark/);
      await expect(mockedPage).toHaveScreenshot(`${surface}-dark.png`, { fullPage: false });
    });
  }
});
