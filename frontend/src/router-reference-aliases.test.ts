import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import router from "./router";

describe("reference page route aliases", () => {
  it("keeps the public login screen in the entry bundle while lazy-loading the authenticated shell", () => {
    const routerSource = readFileSync("src/router.ts", "utf8");

    expect(routerSource).not.toMatch(/import AppLayout from/);
    expect(routerSource).toContain('import AuthLayout from "./layouts/AuthLayout.vue"');
    expect(routerSource).toContain('import LoginView from "./views/auth/LoginView.vue"');
    expect(routerSource).toContain('component: () => import("./layouts/AppLayout.vue")');
    expect(routerSource).toContain("component: AuthLayout");
    expect(routerSource).toContain("component: LoginView");
  });

  it("keeps the reference practice path mapped to the course practice page", () => {
    expect(router.resolve("/practice/42").name).toBe("course-practice");
  });

  it("keeps the reference exam path mapped to the immersive exam page", () => {
    expect(router.resolve("/exam/42").name).toBe("exam-take");
  });

  it("keeps the reference profile path mapped to the account page", () => {
    expect(router.resolve("/profile").name).toBe("mine");
  });

  it("marks only the four primary tabs for component persistence", () => {
    for (const path of ["/", "/courses", "/import", "/mine"]) {
      expect(router.resolve(path).meta.keepAlive, path).toBe(true);
    }

    for (const path of ["/courses/42", "/practice/42", "/study-overview"]) {
      expect(router.resolve(path).meta.keepAlive, path).not.toBe(true);
    }
  });
});
