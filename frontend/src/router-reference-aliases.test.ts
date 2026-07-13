import { describe, expect, it } from "vitest";

import router from "./router";

describe("reference page route aliases", () => {
  it("keeps the reference practice path mapped to the course practice page", () => {
    expect(router.resolve("/practice/42").name).toBe("course-practice");
  });

  it("keeps the reference exam path mapped to the immersive exam page", () => {
    expect(router.resolve("/exam/42").name).toBe("exam-take");
  });

  it("keeps the reference profile path mapped to the account page", () => {
    expect(router.resolve("/profile").name).toBe("mine");
  });
});
