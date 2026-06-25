import { describe, it, expect } from "vitest";
import {
  formatOptions,
  isTextQuestionType,
  getQuestionAnswerHint,
  typeLabel,
  TRUE_FALSE_TRUE,
  TRUE_FALSE_FALSE,
} from "../question.ts";

describe("formatOptions", () => {
  it("returns empty array for null/undefined", () => {
    expect(formatOptions(null)).toEqual([]);
    expect(formatOptions(undefined)).toEqual([]);
  });

  it("formats array into A/B/C/D keys", () => {
    const result = formatOptions(["苹果", "香蕉", "橙子"]);
    expect(result).toEqual([
      { key: "A", value: "苹果" },
      { key: "B", value: "香蕉" },
      { key: "C", value: "橙子" },
    ]);
  });

  it("formats object with sorted keys", () => {
    const result = formatOptions({ B: "选项B", A: "选项A" });
    expect(result).toEqual([
      { key: "A", value: "选项A" },
      { key: "B", value: "选项B" },
    ]);
  });
});

describe("isTextQuestionType", () => {
  it("returns true for fill_blank and short_answer", () => {
    expect(isTextQuestionType("fill_blank")).toBe(true);
    expect(isTextQuestionType("short_answer")).toBe(true);
  });

  it("returns false for choice types", () => {
    expect(isTextQuestionType("single_choice")).toBe(false);
    expect(isTextQuestionType("multiple_choice")).toBe(false);
    expect(isTextQuestionType("true_false")).toBe(false);
  });
});

describe("getQuestionAnswerHint", () => {
  it("returns correct hint for each type", () => {
    expect(getQuestionAnswerHint("single_choice")).toBe("请选择一个选项");
    expect(getQuestionAnswerHint("multiple_choice")).toBe("请选择所有正确选项");
    expect(getQuestionAnswerHint("true_false")).toBe("请选择正确或错误");
    expect(getQuestionAnswerHint("fill_blank")).toBe("请输入你的答案");
  });

  it("returns empty string for unknown type", () => {
    expect(getQuestionAnswerHint("unknown")).toBe("");
  });
});

describe("typeLabel", () => {
  it("returns Chinese label", () => {
    expect(typeLabel("single_choice")).toBe("单选题");
    expect(typeLabel("true_false")).toBe("判断题");
  });

  it("returns original string for unknown type", () => {
    expect(typeLabel("custom_type")).toBe("custom_type");
  });
});
