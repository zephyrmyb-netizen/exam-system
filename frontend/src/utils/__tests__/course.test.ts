import { describe, expect, it } from "vitest";
import { getCourseDisplayName, isPracticeReadyCourse } from "../course";

describe("course utilities", () => {
  it("treats courses with questions as practice ready", () => {
    expect(isPracticeReadyCourse({ id: 1, name: "Java 复习", question_count: 3 })).toBe(true);
  });

  it("hides empty placeholder courses from recent practice entries", () => {
    expect(isPracticeReadyCourse({ id: 2, name: "未命名题库", question_count: 0 })).toBe(false);
    expect(isPracticeReadyCourse({ id: 3, name: "", question_count: 0 })).toBe(false);
  });

  it("normalizes empty course names for display", () => {
    expect(getCourseDisplayName({ name: "  " })).toBe("未命名题库");
    expect(getCourseDisplayName({ name: " 数据结构 " })).toBe("数据结构");
  });
});
