import { expect, prepareSurface, test } from "./visual-fixture";

async function readLayout(page: Parameters<typeof prepareSurface>[0]) {
  return page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
    shellWidth: document.querySelector<HTMLElement>(".app-shell")?.getBoundingClientRect().width ?? 0,
    pageWidth: document.querySelector<HTMLElement>("[data-reference-page='import']")?.getBoundingClientRect().width ?? 0,
  }));
}

for (const viewport of [
  { width: 320, height: 720 },
  { width: 390, height: 844 },
  { width: 420, height: 900 },
]) {
  test(`selecting a file keeps the import layout stable at ${viewport.width}px`, async ({ mockedPage }) => {
    await mockedPage.setViewportSize(viewport);
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
  });
}
