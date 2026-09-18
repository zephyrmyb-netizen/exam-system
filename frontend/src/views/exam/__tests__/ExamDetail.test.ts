import { flushPromises, mount } from "@vue/test-utils";
import { reactive } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExamDetail from "../ExamDetail.vue";

const api = vi.hoisted(() => ({ publishExam: vi.fn() }));
const clipboard = vi.hoisted(() => ({ writeText: vi.fn() }));
const route = { params: { examId: "7" }, query: {} };
const router = { replace: vi.fn() };
const store = reactive({
  loading: false,
  error: "",
  currentExam: {
    id: 7,
    title: "草稿考试",
    description: "",
    creator_id: 3,
    status: "draft",
    question_count: 1,
    total_score: 10,
    time_limit: 30,
    questions: [{ id: 1 }],
  },
  loadExam: vi.fn(),
});

vi.mock("vue-router", () => ({ useRoute: () => route, useRouter: () => router }));
vi.mock("@/stores/exam", () => ({ useExamStore: () => store }));
vi.mock("@/stores/auth", () => ({ useAuthStore: () => ({ user: { id: 3 } }) }));
vi.mock("@/api/exams", () => api);
vi.mock("@/api/request", () => ({ default: { post: vi.fn() }, getErrorMessage: () => "发布失败" }));

describe("ExamDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    store.currentExam.status = "draft";
    store.currentExam.creator_id = 3;
    api.publishExam.mockResolvedValue({ id: 7, status: "published" });
    clipboard.writeText.mockResolvedValue(undefined);
  });

  it("lets the draft creator publish as a standard account", async () => {
    const wrapper = mount(ExamDetail);
    await flushPromises();

    await wrapper.get('[data-testid="exam-detail-publish"]').trigger("click");
    await flushPromises();

    expect(api.publishExam).toHaveBeenCalledWith(7);
    expect(store.loadExam).toHaveBeenCalledWith(7);
  });

  it("copies a published exam's real detail URL", async () => {
    store.currentExam.status = "published";
    vi.stubGlobal("navigator", { clipboard });

    const wrapper = mount(ExamDetail);
    await flushPromises();

    await wrapper.get('[data-testid="exam-detail-share"]').trigger("click");
    await flushPromises();

    expect(clipboard.writeText).toHaveBeenCalledWith(expect.stringMatching(/\/exams\/7$/));
    expect(wrapper.text()).toContain("考试链接已复制");
    vi.unstubAllGlobals();
  });
});
