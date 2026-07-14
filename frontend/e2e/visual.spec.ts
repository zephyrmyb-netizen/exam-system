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

test("home shell semantics remain available to visual review", async ({ mockedPage }) => {
  await prepareSurface(mockedPage, "home");

  await expect(mockedPage.locator("[data-testid='app-shell'][data-layout='tabbed']")).toBeVisible();
  await expect(mockedPage.locator("[data-testid='bottom-tab-home']")).toBeVisible();
});

test("course management buttons stay fixed to the trailing edge", async ({ mockedPage }) => {
  await prepareSurface(mockedPage, "course-list");

  const offsets = await mockedPage.locator(".course-row").evaluateAll((rows) =>
    rows.map((row) => {
      const rowRect = row.getBoundingClientRect();
      const buttonRect = row.querySelector<HTMLElement>(".more-btn")?.getBoundingClientRect();
      return {
        rightGap: buttonRect ? rowRect.right - buttonRect.right : Number.POSITIVE_INFINITY,
        centerDelta: buttonRect
          ? Math.abs(rowRect.top + rowRect.height / 2 - (buttonRect.top + buttonRect.height / 2))
          : Number.POSITIVE_INFINITY,
      };
    }),
  );

  for (const offset of offsets) {
    expect(offset.rightGap).toBeGreaterThanOrEqual(8);
    expect(offset.rightGap).toBeLessThanOrEqual(16);
    expect(offset.centerDelta).toBeLessThanOrEqual(1);
  }
});

test("home recent courses expose a trailing management button", async ({ mockedPage }) => {
  await prepareSurface(mockedPage, "home");

  const offset = await mockedPage.locator(".home-course-list .course-item").first().evaluate((row) => {
    const rowRect = row.getBoundingClientRect();
    const buttonRect = row.querySelector<HTMLElement>("[data-home-course-more]")?.getBoundingClientRect();
    return buttonRect ? rowRect.right - buttonRect.right : Number.POSITIVE_INFINITY;
  });

  await expect(mockedPage.locator("[data-home-course-more]").first()).toBeVisible();
  expect(offset).toBeGreaterThanOrEqual(8);
  expect(offset).toBeLessThanOrEqual(16);

  await mockedPage.locator("[data-home-course-more]").first().click();
  const menuOptions = mockedPage.locator(".home-course-item--menu-open .home-course-menu .home-menu-option");
  await expect(menuOptions).toHaveCount(5);
  await expect(mockedPage.locator(".home-course-list")).toHaveClass(/home-course-list--menu-open/);
  await expect(mockedPage.locator(".home-course-list")).toHaveCSS("overflow", "visible");
});

test("course menu remains fully visible above other course cards", async ({ mockedPage }) => {
  await prepareSurface(mockedPage, "course-list");
  await mockedPage.locator(".course-row .more-btn").first().click();

  const courseList = mockedPage.locator("[data-testid='course-list']");
  await expect(courseList).toHaveClass(/course-list--menu-open/);
  await expect(courseList).toHaveCSS("overflow", "visible");
  const options = mockedPage.locator(".course-row--menu-open .course-menu .menu-option");
  await expect(options).toHaveCount(5);

  const details = await options.evaluateAll((items) =>
    items.map((item) => {
      const rect = item.getBoundingClientRect();
      const hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
      return {
        left: rect.left,
        right: rect.right,
        top: rect.top,
        bottom: rect.bottom,
        visible: hit === item || item.contains(hit),
      };
    }),
  );

  for (const item of details) {
    expect(item.left).toBeGreaterThanOrEqual(0);
    expect(item.right).toBeLessThanOrEqual(390);
    expect(item.top).toBeGreaterThanOrEqual(0);
    expect(item.bottom).toBeLessThanOrEqual(844);
    expect(item.visible).toBe(true);
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
