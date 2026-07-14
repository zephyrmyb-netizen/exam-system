import { expect, prepareSurface, test } from "./visual-fixture";

async function readLayout(page: Parameters<typeof prepareSurface>[0]) {
  return page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
    shellWidth: document.querySelector<HTMLElement>(".app-shell")?.getBoundingClientRect().width ?? 0,
    pageWidth: document.querySelector<HTMLElement>("[data-reference-page='import']")?.getBoundingClientRect().width ?? 0,
    constrainedSurfaces: [
      ".import-file-card",
      ".import-file-card__summary",
      ".import-file-card__actions",
      ".opt-panel",
      ".hero-cta",
      ".adv-section",
      ".import-guide",
    ].map(
      (selector) => {
        const rect = document.querySelector<HTMLElement>(selector)?.getBoundingClientRect();
        return { selector, left: rect?.left ?? 0, right: rect?.right ?? 0, width: rect?.width ?? 0 };
      },
    ),
    finalGuideItemRight:
      document.querySelector<HTMLElement>(".import-guide li:last-child")?.getBoundingClientRect().right ?? 0,
    fileNameBottom:
      document.querySelector<HTMLElement>(".hero-drop-selected")?.getBoundingClientRect().bottom ?? 0,
    fileHintTop:
      document.querySelector<HTMLElement>(".import-file-card__summary .hero-drop-hint")?.getBoundingClientRect().top ?? 0,
  }));
}

for (const viewport of [
  { width: 320, height: 720 },
  { width: 390, height: 844 },
  { width: 420, height: 900 },
]) {
  test(`selecting a file keeps the import layout stable at ${viewport.width}px`, async ({ mockedPage }) => {
    await mockedPage.setViewportSize(viewport);
    await mockedPage.route("**/courses/mine", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify([
          {
            id: 99,
            owner_id: 42,
            name: "这是一个用于验证题库选择框不会把移动端导入页面撑开的超长题库名称",
            description: "",
            subject: "机器学习",
            visibility: "private",
            created_at: "2026-07-15T00:00:00+08:00",
            question_count: 12,
          },
        ]),
      });
    });
    await prepareSurface(mockedPage, "ai-import");

    const before = await readLayout(mockedPage);
    await mockedPage.locator("#import-file-input").setInputFiles({
      name: "机器学习课程复习资料-包含一个用于验证超长文件名不会撑开页面的说明.docx",
      mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      buffer: Buffer.from("test document"),
    });
    await expect(mockedPage.locator(".import-file-card.has-file")).toBeVisible();

    const after = await readLayout(mockedPage);
    expect(after.documentWidth).toBeLessThanOrEqual(after.clientWidth);
    expect(after.bodyWidth).toBeLessThanOrEqual(after.clientWidth);
    expect(after.shellWidth).toBeCloseTo(before.shellWidth, 0);
    expect(after.pageWidth).toBeCloseTo(before.pageWidth, 0);
    for (const surface of after.constrainedSurfaces) {
      expect(surface.left, `${surface.selector} must stay inside the left edge`).toBeGreaterThanOrEqual(0);
      expect(surface.right, `${surface.selector} must stay inside the right edge`).toBeLessThanOrEqual(after.clientWidth);
      expect(surface.width, `${surface.selector} must not exceed the viewport`).toBeLessThanOrEqual(after.clientWidth);
    }
    expect(after.finalGuideItemRight, "the third import step must remain visible").toBeLessThanOrEqual(after.clientWidth);
    expect(after.fileNameBottom, "file name and metadata must not overlap").toBeLessThanOrEqual(after.fileHintTop);
  });
}

test("parsed preview keeps the course selector and source file within the mobile viewport", async ({ mockedPage }) => {
  await mockedPage.setViewportSize({ width: 390, height: 844 });
  await prepareSurface(mockedPage, "ai-import");

  await mockedPage.locator("#import-file-input").setInputFiles({
    name: "very-long-source-file-name-for-mobile-import-layout-check.docx",
    mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    buffer: Buffer.from("test document"),
  });
  await mockedPage.locator(".hero-cta").click();
  await expect(mockedPage.locator(".preview-root")).toBeVisible();

  const layout = await mockedPage.evaluate(() => {
    const clientWidth = document.documentElement.clientWidth;
    const surfaces = [".preview-root", ".preview-head-text", ".course-section", ".course-row", ".course-input", ".course-select"].map(
      (selector) => {
        const rect = document.querySelector<HTMLElement>(selector)?.getBoundingClientRect();
        return { selector, left: rect?.left ?? 0, right: rect?.right ?? 0, width: rect?.width ?? 0 };
      },
    );
    return {
      clientWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      surfaces,
    };
  });

  expect(layout.documentWidth).toBeLessThanOrEqual(layout.clientWidth);
  expect(layout.bodyWidth).toBeLessThanOrEqual(layout.clientWidth);
  for (const surface of layout.surfaces) {
    expect(surface.left, `${surface.selector} must stay inside the left edge`).toBeGreaterThanOrEqual(0);
    expect(surface.right, `${surface.selector} must stay inside the right edge`).toBeLessThanOrEqual(layout.clientWidth);
    expect(surface.width, `${surface.selector} must not exceed the viewport`).toBeLessThanOrEqual(layout.clientWidth);
  }
});
