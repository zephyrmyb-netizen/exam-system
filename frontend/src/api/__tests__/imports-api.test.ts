import { beforeEach, describe, expect, it, vi } from "vitest";

import { previewFile } from "../imports";
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
});
