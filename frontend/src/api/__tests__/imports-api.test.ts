import { beforeEach, describe, expect, it, vi } from "vitest";

import { createImportTask, previewFile } from "../imports";
import request from "../request.ts";

vi.mock("../request.ts", () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ data: { questions: [], warnings: [] } })),
  },
}));

describe("imports api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uploads image previews through the existing preview endpoint with a long timeout", async () => {
    const file = new File(["image"], "question.png", { type: "image/png" });

    await previewFile(file, { course_name: "图片题目" });

    expect(request.post).toHaveBeenCalledWith(
      "/imports/file/preview",
      expect.any(FormData),
      expect.objectContaining({
        params: { course_name: "图片题目" },
        timeout: 420000,
      }),
    );
  });

  it("allows enough time for a large mobile upload to create its background task", async () => {
    const file = new File(["large"], "long-review.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });

    await createImportTask(file, { course_name: "期末复习" });

    expect(request.post).toHaveBeenCalledWith(
      "/imports/tasks",
      expect.any(FormData),
      expect.objectContaining({
        params: { course_name: "期末复习" },
        timeout: 120000,
      }),
    );
  });

  it("turns a malformed preview response into a recoverable parsing message", async () => {
    vi.mocked(request.post).mockResolvedValueOnce({ data: "not-json" } as never);

    await expect(previewFile(new File(["bad"], "broken.docx"))).rejects.toMatchObject({
      userMessage: "AI 返回格式异常，已跳过异常片段，请尝试重新解析。",
    });
  });

  it("normalizes an AI non-JSON warning returned by the preview API", async () => {
    vi.mocked(request.post).mockResolvedValueOnce({
      data: {
        questions: [{ type: "fill_blank", question: "Q", answer: "A" }],
        suggested_course_name: "测试题库",
        warnings: ["AI 返回了非 JSON 格式内容，已忽略此分块（Unexpected token）"],
        total_parsed: 1,
        total_valid: 1,
        total_invalid: 0,
        timing: null,
      },
    } as never);

    const result = await previewFile(new File(["partial"], "partial.docx"));

    expect(result.warnings).toContain("AI 返回格式异常，已跳过异常片段，请尝试重新解析。");
  });
});
