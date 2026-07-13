import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExamTake from "../ExamTake.vue";

const route = { params: { examId: "7" } };
const router = { replace: vi.fn() };
const confirm = vi.fn();
const store = {
  loading: false,
  error: "",
  currentExam: {
    id: 7,
    title: "期末考试",
    questions: [{ question_id: 1, question: "题目", question_type: "single_choice", score: 1, options: { A: "答案" } }],
  },
  currentQuestion: { question_id: 1, question: "题目", question_type: "single_choice", score: 1, options: { A: "答案" } },
  currentIndex: 0,
  totalQuestions: 1,
  answeredCount: 0,
  progress: 0,
  answers: {},
  submitting: false,
  startAttempt: vi.fn(),
  submitCurrentExam: vi.fn(),
  setAnswer: vi.fn(),
  next: vi.fn(),
  prev: vi.fn(),
  jumpTo: vi.fn(),
  reset: vi.fn(),
};

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
  });

  it("confirms and leaves an in-progress exam without forcing submission", async () => {
    const wrapper = mount(ExamTake, {
      global: {
        stubs: { ExamQuestionCard: true },
      },
    });

    await wrapper.find('[aria-label="退出考试"]').trigger("click");

    expect(confirm).toHaveBeenCalledWith(expect.objectContaining({ title: "退出考试", confirmText: "退出" }));
    expect(store.reset).toHaveBeenCalledOnce();
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-detail", params: { examId: 7 } });
  });
});
