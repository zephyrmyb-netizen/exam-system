import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportQuestions from "../ImportQuestions.vue";
import { confirmImportTask, createImportTask, extractFileText } from "../../api/imports";
import { useAiImportTaskStore } from "../../stores/aiImportTask";
import { ACCEPTED_IMPORT_FILE_TYPES } from "../../utils/importFiles";

const router = { replace: vi.fn() };
const route = { query: {} as Record<string, unknown> };
const courseState = vi.hoisted(() => ({
  courses: [] as Array<{ id: number; name: string; question_count: number }>,
  coursesLoading: false,
  coursesError: "",
  fetchCourses: vi.fn(),
}));
const manualState = vi.hoisted(() => ({
  jsonText: "",
  importLoading: false,
  importMessage: "",
  importError: "",
  jsonResultCourseId: 0,
  importQuestions: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => router,
  useRoute: () => route,
}));

vi.mock("../../composables/useImportCourses", async () => {
  const { ref } = await import("vue");
  return {
    useImportCourses: () => ({
      courses: ref(courseState.courses),
      coursesLoading: ref(courseState.coursesLoading),
      coursesError: ref(courseState.coursesError),
      fetchCourses: courseState.fetchCourses,
    }),
  };
});

vi.mock("../../composables/useManualQuestionImport", async () => {
  const { ref } = await import("vue");
  return {
    useManualQuestionImport: () => ({
      jsonText: ref(manualState.jsonText),
      importLoading: ref(manualState.importLoading),
      importMessage: ref(manualState.importMessage),
      importError: ref(manualState.importError),
      jsonResultCourseId: ref(manualState.jsonResultCourseId),
      importQuestions: manualState.importQuestions,
    }),
  };
});

vi.mock("../../api/imports", () => ({
  AI_IMPORT_FORMAT_ERROR_MESSAGE: "AI 返回格式异常，已跳过异常片段，请尝试重新解析。",
  confirmImport: vi.fn(),
  confirmImportTask: vi.fn(),
  extractFileText: vi.fn(),
  createImportTask: vi.fn(() =>
    Promise.resolve({
      id: "task-1",
      status: "ready",
      source_filename: "test.docx",
      course_id: null,
      course_name: "默认题库",
      progress_current: 1,
      progress_total: 1,
      questions: [],
      suggested_course_name: "默认题库",
      warnings: [],
      total_valid: 0,
      total_invalid: 0,
      timing: null,
      error_message: "",
      created_at: null,
      started_at: null,
      finished_at: null,
    }),
  ),
  getImportTask: vi.fn(),
}));

function mountPage() {
  return mount(ImportQuestions, {
    global: {
      stubs: {
        ImportTaskMonitor: { template: "<div class='task-monitor'><slot />{{ title }} {{ detail }}</div>", props: ["title", "detail"] },
        ImportCapabilityStrip: true,
        ImportPreview: {
          template: `
            <div class="preview-stub" :data-confirming="String(confirming)">
              <span>预览解析结果</span>
              <button class="preview-confirm" type="button" @click="$emit('confirm', { course_id: 9, course_name: '数学', questions: [] })">
                确认导入
              </button>
            </div>
          `,
          props: ["confirming"],
          emits: ["confirm"],
        },
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

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((next) => {
    resolve = next;
  });
  return { promise, resolve };
}

function previewQuestion() {
  return {
    id: 1,
    owner_id: 1,
    course_id: null,
    visibility: "private" as const,
    source: "import" as const,
    created_at: null,
    subject: "数学",
    chapter: "",
    type: "single_choice" as const,
    question: "1 + 1 = ?",
    options: { A: "1", B: "2" },
    answer: "B",
    analysis: "",
    difficulty: "easy" as const,
  };
}

describe("ImportQuestions file import behavior", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    route.query = {};
    courseState.courses = [];
    courseState.coursesLoading = false;
    courseState.coursesError = "";
    manualState.importLoading = false;
    manualState.importMessage = "";
    manualState.importError = "";
  });

  it("renders the reference page identity, compact title, upload formats, disclosure, and three-step guide", () => {
    const wrapper = mountPage();

    expect(wrapper.get("[data-reference-page='import']").attributes("data-reference-page")).toBe("import");
    expect(wrapper.findAll("input[type='file']")).toHaveLength(1);
    expect(wrapper.find("input[type='file']").attributes("accept")).toBe(ACCEPTED_IMPORT_FILE_TYPES);
    expect(wrapper.get(".import-page__head h2").text()).toBe("AI 导入");
    expect(wrapper.get(".import-page__head p").text()).toBe("智能解析 · 一键导入题目");
    expect(wrapper.get(".hero-drop-text").text()).toContain("点击或拖拽上传文件");
    expect(wrapper.get(".hero-drop-hint").text()).toContain("AI 自动解析题干、选项和答案");
    expect(wrapper.get(".hero-drop-zone").attributes("for")).toBe("import-file-input");
    expect(wrapper.get(".import-file-limits").text()).toContain("单个文件最大 10MB");
    expect(wrapper.findAll(".format-tag").map((tag) => tag.text())).toEqual(["Word", "PPT", "PDF", "图片", "文本"]);
    expect(wrapper.get("details.adv-section").attributes("open")).toBeUndefined();
    expect(wrapper.get("summary.adv-summary").text()).toContain("JSON / 其他导入方式");
    expect(wrapper.findAll(".import-guide li")).toHaveLength(3);
  });

  it("accepts a dropped file through the same validation path and preserves long names safely", async () => {
    const wrapper = mountPage();
    const name = `${"很长的试题文件名".repeat(8)}.docx`;
    const file = new File(["x"], name);
    const zone = wrapper.get(".hero-drop-zone");

    await zone.trigger("dragenter", { dataTransfer: { files: [file] } });
    expect(zone.classes()).toContain("is-dragging");
    await zone.trigger("drop", { dataTransfer: { files: [file] } });

    expect(zone.classes()).not.toContain("is-dragging");
    expect((wrapper.get(".opt-input").element as HTMLInputElement).value).toBe(name.slice(0, -5));
    expect(wrapper.get(".hero-drop-selected").attributes("title")).toBe(name);
    expect(wrapper.get(".hero-drop-selected").classes()).toContain("truncate-file-name");
  });

  it("rejects an oversized dropped file before starting an AI task", async () => {
    const wrapper = mountPage();
    const file = new File([new Uint8Array(10 * 1024 * 1024 + 1)], "too-large.pdf");

    await wrapper.get(".hero-drop-zone").trigger("drop", { dataTransfer: { files: [file] } });

    expect(wrapper.text()).toContain("文件过大");
    expect(wrapper.get(".hero-cta").attributes("disabled")).toBeDefined();
    expect(createImportTask).not.toHaveBeenCalled();
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

  it("restores parsing as a compact progress state after returning", async () => {
    const store = useAiImportTaskStore();
    store.status = "running";
    store.fileName = "slides.pptx";
    store.startedAt = Date.now() - 2_000;

    const wrapper = mountPage();

    expect(wrapper.find(".task-monitor").exists()).toBe(true);
    expect(wrapper.find(".import-running-state").exists()).toBe(true);
    expect(wrapper.find(".hero-drop-zone").exists()).toBe(false);
    expect(wrapper.find(".opt-panel").exists()).toBe(false);
    expect(wrapper.text()).toContain("AI 正在解析，请稍候，通常需要 30 秒左右");
  });

  it("announces resumed chunk progress with the real remote counts", () => {
    const store = useAiImportTaskStore();
    store.status = "running";
    store.fileName = "chapter.pdf";
    store.progressCurrent = 2;
    store.progressTotal = 5;

    const wrapper = mountPage();

    expect(wrapper.get(".import-running-state").attributes("aria-live")).toBe("polite");
    expect(wrapper.get(".task-monitor").text()).toContain("已处理 2 / 5 个分块");
  });

  it("honors course_id from the route and exposes loading, failure, and retry states", async () => {
    route.query = { course_id: "7" };
    courseState.courses = [{ id: 7, name: "数据结构", question_count: 42 }];
    courseState.coursesError = "获取题库列表失败";
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "exam.docx"));

    expect((wrapper.get("select.opt-input").element as HTMLSelectElement).value).toBe("7");
    expect(wrapper.text()).toContain("数据结构");
    expect(wrapper.text()).toContain("获取题库列表失败");
    await wrapper.get(".inline-warning button").trigger("click");
    expect(courseState.fetchCourses).toHaveBeenCalledTimes(2);
  });

  it("keeps the course picker usable while the real course list is loading", async () => {
    courseState.coursesLoading = true;
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "exam.docx"));

    expect(wrapper.get("select.opt-input").text()).toContain("加载中");
    expect(wrapper.get("select.opt-input").attributes("disabled")).toBeUndefined();
  });

  it("keeps repeated submit actions disabled while work is already in progress", async () => {
    manualState.importLoading = true;
    const wrapper = mountPage();

    expect(wrapper.get(".hero-cta").attributes("disabled")).toBeDefined();
    await wrapper.get("summary.adv-summary").trigger("click");
    await wrapper.vm.$nextTick();
    const jsonButton = wrapper.findAll("button").find((button) => button.text().includes("导入中"));
    expect(jsonButton?.attributes("disabled")).toBeDefined();
  });

  it("preserves JSON import plus complete long-text extraction and clipboard copying inside the disclosure", async () => {
    const longText = [
      `第一段：${"题目内容".repeat(160)}`,
      `第二段：${"答案解析".repeat(160)}`,
      `第三段：${"补充说明".repeat(160)}`,
    ].join("\n\n");
    const copyText = vi.fn();
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: copyText },
      configurable: true,
    });
    vi.mocked(extractFileText).mockResolvedValueOnce({
      text: longText,
      filename: "math.docx",
      suggested_course_name: "math",
      timing: null,
    });
    const wrapper = mountPage();
    await chooseFile(wrapper, new File(["x"], "math.docx"));
    const details = wrapper.get("details.adv-section");
    (details.element as HTMLDetailsElement).open = true;
    await details.trigger("toggle");
    expect(details.attributes("open")).toBeDefined();

    const jsonButton = wrapper.findAll("button").find((button) => button.text().includes("导入 JSON"));
    await jsonButton?.trigger("click");
    expect(manualState.importQuestions).toHaveBeenCalledTimes(1);

    const extractButton = wrapper.findAll("button").find((button) => button.text() === "提取文本");
    await extractButton?.trigger("click");
    await flushPromises();
    expect(extractFileText).toHaveBeenCalledWith(expect.any(File), { course_id: 0 });
    expect(wrapper.get(".adv-extracted pre").text()).toBe(longText);

    await wrapper.get(".adv-extracted button").trigger("click");
    expect(copyText).toHaveBeenCalledWith(`请把下面的试题文本整理成标准 JSON 数组，只输出 JSON，不要解释：\n\n${longText}`);
  });

  it("guards task preview confirmation from duplicate submits and transitions with the real result", async () => {
    const pendingConfirm = deferred<{ imported_count: number; course_id: number; course_name: string }>();
    vi.mocked(confirmImportTask).mockReturnValueOnce(pendingConfirm.promise);
    const store = useAiImportTaskStore();
    store.status = "success";
    store.taskId = "task-42";
    store.fileName = "math.docx";
    store.previewData = {
      questions: [previewQuestion()],
      suggested_course_name: "数学",
      warnings: [],
      total_parsed: 1,
      total_valid: 1,
      total_invalid: 0,
      timing: null,
    };
    const wrapper = mountPage();

    await wrapper.get(".preview-confirm").trigger("click");
    await wrapper.get(".preview-confirm").trigger("click");

    expect(confirmImportTask).toHaveBeenCalledTimes(1);
    expect(confirmImportTask).toHaveBeenCalledWith("task-42", expect.objectContaining({ course_id: 9 }));
    expect(wrapper.get(".preview-stub").attributes("data-confirming")).toBe("true");

    pendingConfirm.resolve({ imported_count: 3, course_id: 9, course_name: "数学" });
    await flushPromises();

    expect(wrapper.text()).toContain("导入成功");
    expect(wrapper.text()).toContain("3");
    expect(wrapper.text()).toContain("数学");
  });

  it("renders the real preview phase before confirmation", () => {
    const store = useAiImportTaskStore();
    store.status = "success";
    store.previewData = {
      questions: [previewQuestion()],
      suggested_course_name: "数学",
      warnings: [],
      total_parsed: 1,
      total_valid: 1,
      total_invalid: 0,
      timing: null,
    };

    const wrapper = mountPage();

    expect(wrapper.get(".preview-stub").text()).toContain("预览解析结果");
    expect(wrapper.find(".hero-drop-zone").exists()).toBe(false);
  });

  it("keeps narrow-screen overflow contracts in CSS; browser viewport acceptance is Playwright", () => {
    const source = readFileSync(resolve(process.cwd(), "src/views/ImportQuestions.vue"), "utf8");

    expect(source).toMatch(/\.import-page\s*\{[^}]*min-width:\s*0[^}]*max-width:\s*100%[^}]*overflow-x:\s*clip/s);
    expect(source).toMatch(/\.truncate-file-name\s*\{[^}]*max-width:\s*100%[^}]*min-width:\s*0[^}]*overflow:\s*hidden/s);
    expect(source).toMatch(/\.import-format-tags\s*\{[^}]*min-width:\s*0[^}]*overflow-x:\s*auto/s);
    expect(source).toMatch(/\.adv-extracted pre\s*\{[^}]*min-width:\s*0[^}]*max-width:\s*100%[^}]*max-height:\s*180px[^}]*overflow:\s*auto[^}]*overflow-wrap:\s*anywhere/s);
  });

  it("shows an already imported task as a completion state after returning", async () => {
    const store = useAiImportTaskStore();
    store.status = "success";
    store.imported = true;
    store.importedCount = 8;
    store.resultCourseId = 3;
    store.resultCourseName = "Java 复习";

    const wrapper = mountPage();

    expect(wrapper.text()).toContain("导入成功");
    expect(wrapper.text()).toContain("8");
    expect(wrapper.text()).not.toContain("预览解析结果");
  });

  it("shows the AI-specific timeout guidance", async () => {
    vi.mocked(createImportTask).mockRejectedValueOnce({ code: "ECONNABORTED" });
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "slow.docx"));
    await wrapper.get(".hero-cta").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("文件上传或 AI 解析耗时较长，请在稳定网络下重试；大文件最多可等待 2 分钟。");
    expect(wrapper.get(".hero-cta").text()).toContain("重新解析");
  });

  it("normalizes the backend non-JSON parsing failure message", async () => {
    vi.mocked(createImportTask).mockRejectedValueOnce({
      response: { status: 400, data: { detail: "AI 未能解析出题目，请换一个文件或稍后重试。" } },
    });
    const wrapper = mountPage();

    await chooseFile(wrapper, new File(["x"], "broken.docx"));
    await wrapper.get(".hero-cta").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("AI 返回格式异常，已跳过异常片段，请尝试重新解析。");
  });
});
