import { expect, test, prepareSurface } from "./visual-fixture";

for (const width of [390, 412, 820]) {
  test(`adaptive learning surfaces at ${width}px`, async ({ mockedPage: page }) => {
    await page.setViewportSize({ width, height: 900 });
    await prepareSurface(page, "home");
    await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `test-results/apple-home-${width}.png`, fullPage: true });

    await page.route("**/study-groups/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      await route.fulfill({
        json: path.endsWith("/mine")
          ? [{ id: 1, owner_id: 42, name: "期末复习小组", member_count: 8, invite_code: "ABCD1234" }]
          : { group_id: 1, courses: [{ id: 9, name: "计算机网络期末复习", question_count: 36 }], exams: [] },
      });
    });
    await page.goto("/study-groups");
    await page.getByRole("button", { name: "查看资源", exact: true }).click();
    await expect(page.getByRole("link", { name: /计算机网络期末复习/ })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `test-results/apple-groups-${width}.png`, fullPage: true });
    await page.getByPlaceholder("例如：高数冲刺组").focus();
    await expect(page.getByRole("navigation", { name: "主导航" })).toHaveCount(0);
    await page.getByPlaceholder("例如：高数冲刺组").blur();
    await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  });
}

test("dark appearance and reduced motion preserve navigation", async ({ mockedPage: page }) => {
  await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
  await prepareSurface(page, "home");
  await page.evaluate(() => document.documentElement.classList.add("dark"));
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await page.screenshot({ path: "test-results/apple-home-dark.png", fullPage: true });
});
