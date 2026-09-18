import { expect, test } from "@playwright/test";

const betaUrl = process.env.BETA_URL || "https://beta.zephyrmyb.xyz";

test.describe("public beta guest journey", () => {
  test("a guest can enter, create a group, and reach the right resource picker", async ({ page }) => {
    test.setTimeout(90_000);
    await page.goto(betaUrl, { waitUntil: "networkidle" });

    await page.getByRole("button", { name: "立即试用" }).click();
    await expect(page.locator("[data-reference-page='home']")).toBeVisible({ timeout: 20_000 });

    await page.getByRole("button", { name: /学习小组/ }).click();
    await expect(page).toHaveURL(/\/study-groups/);

    const groupName = `beta-journey-${Date.now()}`;
    await page.getByPlaceholder("例如：高数冲刺组").fill(groupName);
    await page.getByRole("button", { name: "创建小组", exact: true }).click();
    await expect(page.getByText("小组已创建。")).toBeVisible();

    await page.getByRole("button", { name: "查看资源" }).click();
    await expect(page.getByText(`当前：${groupName}`)).toBeVisible();
    await page.getByRole("button", { name: "选择题库后共享" }).click();
    await expect(page).toHaveURL(/\/courses\?share_group=\d+&from=study-groups/);

    const courseName = `journey-course-${Date.now()}`;
    await page.locator("[data-create-course]").click();
    await page.getByPlaceholder("如：Java 期末复习").fill(courseName);
    await page.getByRole("button", { name: "创建", exact: true }).click();
    await page.getByText(courseName, { exact: true }).click();
    await expect(page.getByTestId("course-detail-share-group")).toBeVisible();
    await page.getByTestId("course-detail-share-group").click();
    await expect(page.getByText("题库已共享到当前学习小组。")).toBeVisible();
    await page.getByRole("banner").getByRole("button", { name: "返回", exact: true }).click();
    await expect(page).toHaveURL(/\/study-groups/);
    await expect(page.getByText(courseName, { exact: true })).toBeVisible();
  });
});
