import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportQuestions from "../ImportQuestions.vue";
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

  it("accepts Word, PDF, PPTX, and image upload formats", () => {
    const wrapper = mountPage();

    expect(wrapper.find("input[type='file']").attributes("accept")).toBe(ACCEPTED_IMPORT_FILE_TYPES);
  });

  it("rejects legacy .ppt before upload with a save-as-PPTX message", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "legacy.ppt"));

    expect(wrapper.text()).toContain("暂不支持旧版 .ppt，请在 PowerPoint/WPS 中另存为 .pptx 后上传。");
  });

  it("rejects unsupported formats with the supported family names", async () => {
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "notes.txt"));

    expect(wrapper.text()).toContain("不支持 .txt 格式，目前支持 Word、PDF、PPTX、PNG、JPG、WEBP。");
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

  it("keeps the running task monitor visible and disables replacement actions", async () => {
    const store = useAiImportTaskStore();
    store.status = "running";
    store.fileName = "slides.pptx";

    const wrapper = mountPage();

    expect(wrapper.find(".task-monitor").exists()).toBe(true);
    expect(wrapper.find("input[type='file']").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("AI 正在解析，请等待，不要重复上传。");
  });
});
