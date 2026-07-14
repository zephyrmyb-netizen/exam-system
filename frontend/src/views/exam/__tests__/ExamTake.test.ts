import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { reactive } from "vue";
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
const store = reactive({
  loading: false,
  error: "",
  submissionError: "",
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
  answers: {} as Record<string, string>,
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
});

let shortcutHandlers: {
  next?: () => void;
  prev?: () => void;
  selectOption?: (index: number) => void;
} = {};
let swipeHandlers: { onSwipeLeft?: () => void; onSwipeRight?: () => void } = {};
const shortcutBind = vi.fn();
const shortcutUnbind = vi.fn();

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
vi.mock("@/composables/useKeyboardShortcuts", () => ({
  useKeyboardShortcuts: (handlers: typeof shortcutHandlers) => {
    shortcutHandlers = handlers;
    return { bind: shortcutBind, unbind: shortcutUnbind };
  },
}));
vi.mock("@/composables/useSwipe", () => ({
  useSwipe: (_target: unknown, handlers: typeof swipeHandlers) => {
    swipeHandlers = handlers;
  },
}));

describe("ExamTake", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    confirm.mockResolvedValue(true);
    store.loading = false;
    store.error = "";
    store.submissionError = "";
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
    store.setAnswer.mockImplementation((questionId: number, value: string) => {
      store.answers[String(questionId)] = value;
    });
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

  it("does not sync or start a timer after a slow start resolves post-unmount", async () => {
    vi.useFakeTimers();
    let resolveStart!: () => void;
    store.startAttempt.mockImplementationOnce(() => new Promise<void>((resolve) => {
      resolveStart = resolve;
    }));
    const mounted = mountExam();

    mounted.unmount();
    resolveStart();
    await flushPromises();
    await vi.advanceTimersByTimeAsync(2_000);

    expect(store.syncRemainingSeconds).not.toHaveBeenCalled();
    expect(store.submitCurrentExam).not.toHaveBeenCalled();
  });

  it("toggles normalized multiple-choice answers from number shortcuts", () => {
    const multipleQuestion = { ...firstQuestion, question_type: "multiple_choice" };
    store.currentExam.questions = [multipleQuestion];
    store.currentQuestion = multipleQuestion;
    store.answers = { "9": "B" };
    mountExam();

    shortcutHandlers.selectOption?.(0);
    expect(store.setAnswer).toHaveBeenLastCalledWith(9, "A,B");
    shortcutHandlers.selectOption?.(1);
    expect(store.setAnswer).toHaveBeenLastCalledWith(9, "A");
  });

  it("keeps single-choice number shortcuts replacing the answer", () => {
    store.answers = { "9": "A" };
    mountExam();

    shortcutHandlers.selectOption?.(1);
    expect(store.setAnswer).toHaveBeenLastCalledWith(9, "B");
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

  it("attempts an expired submission once automatically and waits for manual retry after failure", async () => {
    vi.useFakeTimers();
    store.remainingSeconds = 0;
    store.submitCurrentExam
      .mockImplementationOnce(async () => {
        store.submissionError = "网络异常，请手动重试交卷";
        throw new Error("network down");
      })
      .mockImplementationOnce(async () => {
        store.submissionError = "";
        const result = { exam_id: 7 };
        store.result = result;
        return result;
      });
    const mounted = mountExam();

    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledOnce();

    await vi.advanceTimersByTimeAsync(5_000);
    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledOnce();
    expect(mounted.get("[data-exam-submit-error]").text()).toContain("请手动重试");

    await mounted.get("[data-exam-submit-retry]").trigger("click");
    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledTimes(2);
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-result", params: { examId: 7 } });
  });

  it("does not let background shortcuts or swipes change the paper while the answer card is open", async () => {
    const mounted = mountExam();
    await mounted.get('[aria-label="打开答题卡"]').trigger("click");

    shortcutHandlers.next?.();
    shortcutHandlers.prev?.();
    shortcutHandlers.selectOption?.(0);
    swipeHandlers.onSwipeLeft?.();
    swipeHandlers.onSwipeRight?.();

    expect(store.next).not.toHaveBeenCalled();
    expect(store.prev).not.toHaveBeenCalled();
    expect(store.setAnswer).not.toHaveBeenCalled();
  });

  it("disables and blocks exit while a submission is pending", async () => {
    let resolveSubmission!: () => void;
    store.submitCurrentExam.mockImplementationOnce(() => {
      store.submitting = true;
      return new Promise((resolve) => {
        resolveSubmission = () => {
          const result = { exam_id: 7 };
          store.result = result;
          store.submitting = false;
          resolve(result);
        };
      });
    });
    const mounted = mountExam();

    void mounted.get(".submit-button").trigger("click");
    await flushPromises();
    const exitButton = mounted.get('[aria-label="退出考试"]');
    expect(exitButton.attributes("disabled")).toBeDefined();
    expect(exitButton.attributes("aria-disabled")).toBe("true");

    await exitButton.trigger("click");
    expect(confirm).not.toHaveBeenCalled();
    expect(store.reset).not.toHaveBeenCalled();
    expect(router.replace).not.toHaveBeenCalled();

    resolveSubmission();
    await flushPromises();
  });

  it("keeps the paper and answers visible after manual submit failure and retries in place", async () => {
    store.answers = { "9": "A" };
    store.submitCurrentExam
      .mockImplementationOnce(async () => {
        store.submissionError = "网络异常，请重试交卷";
        throw new Error("network down");
      })
      .mockImplementationOnce(async () => {
        store.submissionError = "";
        const result = { exam_id: 7 };
        store.result = result;
        return result;
      });
    const mounted = mountExam();

    await mounted.get(".submit-button").trigger("click");
    await flushPromises();
    expect(mounted.find(".exam-topbar").exists()).toBe(true);
    expect(store.currentExam?.id).toBe(7);
    expect(store.answers).toEqual({ "9": "A" });
    expect(mounted.get("[data-exam-submit-error]").text()).toContain("网络异常，请重试交卷");

    await mounted.get("[data-exam-submit-retry]").trigger("click");
    await flushPromises();
    expect(store.submitCurrentExam).toHaveBeenCalledTimes(2);
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-result", params: { examId: 7 } });
  });

  it("hands a successful current-session result to the result route even before Pinia state reflects it", async () => {
    const response = { exam_id: 7 };
    store.result = null;
    store.submitCurrentExam.mockResolvedValueOnce(response);
    const mounted = mountExam();

    await mounted.get(".submit-button").trigger("click");
    await flushPromises();

    expect(store.result).toEqual(response);
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
