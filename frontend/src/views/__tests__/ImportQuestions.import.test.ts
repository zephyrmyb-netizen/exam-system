import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportQuestions from "../ImportQuestions.vue";
import { previewFile } from "../../api/imports";
import { useAiImportTaskStore } from "../../stores/aiImportTask";
import { ACCEPTED_IMPORT_FILE_TYPES } from "../../utils/importFiles";

const router = { push: vi.fn() };
const route = { query: {} };

vi.mock("vue-router", () => ({
  useRouter: () => router,
  useRoute: () => route,
}));

vi.mock("../../composables/useImportCourses", () => ({
  useImportCourses: () => ({
    courses: { value: [] },
    coursesLoading: { value: false },
    coursesError: { value: "" },
    fetchCourses: vi.fn(),
  }),
}));

vi.mock("../../composables/useManualQuestionImport", () => ({
  useManualQuestionImport: () => ({
    jsonText: { value: "" },
    importLoading: { value: false },
    importMessage: { value: "" },
    importError: { value: "" },
    jsonResultCourseId: { value: 0 },
    importQuestions: vi.fn(),
  }),
}));

vi.mock("../../api/imports", () => ({
  AI_IMPORT_FORMAT_ERROR_MESSAGE: "AI 返回格式异常，已跳过异常片段，请尝试重新解析。",
  confirmImport: vi.fn(),
  extractFileText: vi.fn(),
  previewFile: vi.fn(() =>
    Promise.resolve({
      questions: [],
      suggested_course_name: "默认题库",
      warnings: [],
      total_parsed: 0,
      total_valid: 0,
      total_invalid: 0,
      timing: null,
    }),
  ),
}));

function mountPage() {
  return mount(ImportQuestions, {
    global: {
      stubs: {
        ImportTaskMonitor: { template: "<div class='task-monitor'><slot />{{ title }} {{ detail }}</div>", props: ["title", "detail"] },
        ImportCapabilityStrip: true,
        ImportPreview: true,
      },
    },
  });
}

async function chooseFile(wrapper: ReturnType<typeof mount>, file: File) {
  const input = wrapper.find("input[type='file']");
  Object.defineProperty(input.element, "files", {
    value: [file],
    configurable: true,
  });
  await input.trigger("change");
}

describe("ImportQuestions file import behavior", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("accepts Word, PDF, PPT, image, and TXT upload formats", () => {
    const wrapper = mountPage();

    expect(wrapper.find("input[type='file']").attributes("accept")).toBe(ACCEPTED_IMPORT_FILE_TYPES);
    expect(wrapper.text()).toContain("文件选择支持 Word / PDF / PPT / 图片 / TXT");
    expect(wrapper.text()).toContain("AI 可直接解析 DOCX / PDF / PPTX / PNG / JPG / JPEG / WEBP");
  });

  it("rejects legacy .ppt before upload with a save-as-PPTX message", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "legacy.ppt"));

    expect(wrapper.text()).toContain("暂不支持旧版 .ppt，请在 PowerPoint/WPS 中另存为 .pptx 后上传。");
  });

  it("rejects unsupported formats with the supported family names", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "notes.txt"));

    expect(wrapper.text()).toContain("当前 AI 文件解析请先转换为 .docx 后上传");
  });

  it("derives the default course name from the selected file name", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "Java复习题.docx"));

    expect((wrapper.get(".opt-input").element as HTMLInputElement).value).toBe("Java复习题");
  });

  it("shows file name, type, and size after selecting an image", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x".repeat(1024)], "long-question-image-name.png", { type: "image/png" }));

    expect(wrapper.text()).toContain("long-question-image-name.png");
    expect(wrapper.text()).toContain("图片题目");
    expect(wrapper.text()).toContain("1.0KB");
  });

  it("disables text extraction for image files before the user can click it", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "question.webp", { type: "image/webp" }));

    const button = wrapper.findAll("button").find((item) => item.text().includes("图片需使用 AI 解析"));
    expect(button?.attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("图片文件没有可直接提取的文本，请使用 AI 解析。");
  });

  it("restores the running parsing status and disables replacement actions after returning", async () => {
    const store = useAiImportTaskStore();
    store.status = "running";
    store.fileName = "slides.pptx";
    store.startedAt = Date.now() - 2_000;

    const wrapper = mountPage();

    expect(wrapper.find(".task-monitor").exists()).toBe(true);
    expect(wrapper.find("input[type='file']").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("AI 正在解析，请稍候，通常需要 30 秒左右");
  });

  it("shows the AI-specific timeout guidance", async () => {
    vi.mocked(previewFile).mockRejectedValueOnce({ code: "ECONNABORTED" });
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "slow.docx"));
    await wrapper.get(".hero-cta").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("AI 解析时间较长，请稍后重试或换一个更小的文件。");
    expect(wrapper.get(".hero-cta").text()).toContain("重新解析");
  });

  it("normalizes the backend non-JSON parsing failure message", async () => {
    vi.mocked(previewFile).mockRejectedValueOnce({
      response: { status: 400, data: { detail: "AI 未能解析出题目，请换一个文件或稍后重试。" } },
    });
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "broken.docx"));
    await wrapper.get(".hero-cta").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("AI 返回格式异常，已跳过异常片段，请尝试重新解析。");
  });
});
