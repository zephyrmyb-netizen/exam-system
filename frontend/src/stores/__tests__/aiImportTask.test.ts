import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const { getImportTask } = vi.hoisted(() => ({ getImportTask: vi.fn() }));

vi.mock("../../api/imports", () => ({
  AI_IMPORT_FORMAT_ERROR_MESSAGE: "AI 返回格式异常，已跳过异常片段，请尝试重新解析。",
  createImportTask: vi.fn(),
  getImportTask,
}));

import { useAiImportTaskStore } from "../aiImportTask";

describe("ai import task persistence", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it("restores a ready task after the import page has been reloaded", async () => {
    window.localStorage.setItem("xuexibao:active-import-task", "task-resume");
    getImportTask.mockResolvedValue({
      id: "task-resume",
      status: "ready",
      source_filename: "复习题.docx",
      course_id: null,
      course_name: "复习题",
      progress_current: 2,
      progress_total: 2,
      questions: [{ type: "fill_blank", question: "题目", answer: "答案" }],
      suggested_course_name: "复习题",
      warnings: [],
      total_valid: 1,
      total_invalid: 0,
      timing: null,
      error_message: "",
      created_at: null,
      started_at: null,
      finished_at: null,
    });

    const store = useAiImportTaskStore();
    await store.resume();

    expect(store.status).toBe("success");
    expect(store.fileName).toBe("复习题.docx");
    expect(store.previewData?.questions).toHaveLength(1);
  });
});
