import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ExamTake from "../ExamTake.vue";

const route = { params: { examId: "7" } };
const router = { replace: vi.fn() };
const confirm = vi.fn();
const firstQuestion = {
  id: 11,
  question_id: 9,
  question: "TCP 第二次握手的标志位是什么？",
  question_type: "single_choice",
  score: 2,
  order_index: 0,
  options: { A: "SYN=1, ACK=0", B: "SYN=1, ACK=1" },
};
const store = {
  loading: false,
  error: "",
  currentExam: {
    id: 7,
    title: "期末考试",
    time_limit: 60,
    questions: [firstQuestion],
  },
  currentQuestion: firstQuestion as typeof firstQuestion | null,
  currentIndex: 0,
  totalQuestions: 1,
  answeredCount: 0,
  progress: 0,
  remainingSeconds: null as number | null,
  answers: {},
  result: null as { exam_id: number } | null,
  submitting: false,
  startAttempt: vi.fn(),
  submitCurrentExam: vi.fn(),
  setAnswer: vi.fn(),
  next: vi.fn(),
  prev: vi.fn(),
  jumpTo: vi.fn(),
  syncRemainingSeconds: vi.fn(),
  reset: vi.fn(),
};

let wrapper: VueWrapper | undefined;

function mountExam(options: Parameters<typeof mount>[1] = {}) {
  wrapper = mount(ExamTake, {
    global: {
      stubs: { ExamQuestionCard: true },
      ...options?.global,
    },
    ...options,
  });
  return wrapper;
}

vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => router,
}));

vi.mock("@/stores/exam", () => ({ useExamStore: () => store }));
vi.mock("@/stores/confirmDialog", () => ({ useConfirmDialog: () => ({ confirm }) }));
vi.mock("@/composables/useKeyboardShortcuts", () => ({ useKeyboardShortcuts: () => ({ bind: vi.fn(), unbind: vi.fn() }) }));
vi.mock("@/composables/useSwipe", () => ({ useSwipe: vi.fn() }));

describe("ExamTake", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    confirm.mockResolvedValue(true);
    store.loading = false;
    store.error = "";
    store.currentExam = { id: 7, title: "期末考试", time_limit: 60, questions: [firstQuestion] };
    store.currentQuestion = firstQuestion;
    store.currentIndex = 0;
    store.totalQuestions = 1;
    store.answeredCount = 0;
    store.progress = 0;
    store.remainingSeconds = null;
    store.answers = {};
    store.result = null;
    store.submitting = false;
    store.startAttempt.mockResolvedValue(undefined);
    store.submitCurrentExam.mockImplementation(async () => {
      const result = { exam_id: 7 };
      store.result = result;
      return result;
    });
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = undefined;
    vi.useRealTimers();
  });

  it("declares the exam-take reference surface and renders only real exam metadata", () => {
    const mounted = mountExam({ global: { stubs: {} } });

    expect(mounted.attributes("data-reference-page")).toBe("exam-take");
    expect(mounted.text()).toContain("期末考试");
    expect(mounted.text()).toContain("TCP 第二次握手的标志位是什么？");
    expect(mounted.text()).toContain("单选题");
    expect(mounted.text()).toContain("2 分");
    expect(mounted.text()).not.toContain("中等");
    expect(mounted.text()).not.toContain("计算机网络");
  });

  it("keeps loading and API error states explicit", async () => {
    store.loading = true;
    let mounted = mountExam();
    expect(mounted.text()).toContain("正在进入考试");
    expect(mounted.find(".exam-topbar").exists()).toBe(false);

    mounted.unmount();
    store.loading = false;
    store.error = "考试开始失败";
    mounted = mountExam();
    expect(mounted.text()).toContain("考试开始失败");
    await mounted.get(".back-btn").trigger("click");
    expect(router.replace).toHaveBeenCalledWith({ name: "exams" });
  });

  it("confirms and leaves an in-progress exam without forcing submission", async () => {
    const wrapper = mountExam();

    await wrapper.find('[aria-label="退出考试"]').trigger("click");

    expect(confirm).toHaveBeenCalledWith(expect.objectContaining({ title: "退出考试", confirmText: "退出" }));
    expect(store.reset).toHaveBeenCalledOnce();
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-detail", params: { examId: 7 } });
  });

  it("opens the answer card on demand and jumps to a selected question", async () => {
    const wrapper = mountExam();

    expect(wrapper.find("[data-exam-answer-sheet]").exists()).toBe(false);
    await wrapper.get('[aria-label="打开答题卡"]').trigger("click");
    expect(wrapper.find("[data-exam-answer-sheet]").exists()).toBe(true);
    await wrapper.get("[data-exam-answer-sheet] .answer-map button").trigger("click");
    expect(store.jumpTo).toHaveBeenCalledWith(0);
  });

  it("shows a real countdown when the attempt has a server start time", async () => {
    store.remainingSeconds = 2730;
    const wrapper = mountExam();

    expect(wrapper.find("[data-exam-countdown]").text()).toBe("45:30");
  });

  it("builds the answer sheet from every exam question", async () => {
    const secondQuestion = { ...firstQuestion, id: 12, question_id: 2, question: "第二题", order_index: 1 };
    store.currentExam.questions = [firstQuestion, secondQuestion];
    store.totalQuestions = 2;
    store.answers = { "9": "A" };
    const wrapper = mountExam();

    await wrapper.get('[aria-label="打开答题卡"]').trigger("click");

    expect(wrapper.findAll("[data-exam-answer-sheet] .answer-map button")).toHaveLength(2);
    expect(wrapper.findAll("[data-exam-answer-sheet] .answer-map button")[0].classes()).toContain("answered");
    expect(wrapper.findAll("[data-exam-answer-sheet] .answer-map button").map((button) => button.attributes("data-question-id"))).toEqual(["9", "2"]);
  });

  it("uses the shared accessible bottom sheet for the answer card", async () => {
    const wrapper = mountExam();
    await wrapper.get('[aria-label="打开答题卡"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="dialog"]').attributes("aria-modal")).toBe("true");
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(wrapper.find("[data-exam-answer-sheet]").exists()).toBe(false);
  });

  it("automatically submits an expired attempt exactly once", async () => {
    vi.useFakeTimers();
    store.remainingSeconds = 0;
    const wrapper = mountExam();

    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledOnce();
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-result", params: { examId: 7 } });

    await vi.advanceTimersByTimeAsync(3_000);
    expect(store.submitCurrentExam).toHaveBeenCalledOnce();
    wrapper.unmount();
  });

  it("retries an expired attempt after a failed automatic submission", async () => {
    vi.useFakeTimers();
    store.remainingSeconds = 0;
    store.submitCurrentExam
      .mockRejectedValueOnce(new Error("network down"))
      .mockImplementationOnce(async () => {
        const result = { exam_id: 7 };
        store.result = result;
        return result;
      });
    mountExam();

    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledOnce();

    await vi.advanceTimersByTimeAsync(1_000);
    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledTimes(2);
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-result", params: { examId: 7 } });
  });

  it("shows an honest empty state when the real paper contains no questions", async () => {
    store.currentExam = { id: 7, title: "空试卷", time_limit: 60, questions: [] };
    store.currentQuestion = null;
    store.totalQuestions = 0;
    const wrapper = mountExam();

    await flushPromises();
    expect(wrapper.text()).toContain("暂无可作答题目");
    expect(wrapper.text()).not.toContain("第 1");
  });
});
