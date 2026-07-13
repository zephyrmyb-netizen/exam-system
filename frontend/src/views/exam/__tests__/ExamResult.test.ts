import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExamResult from "../ExamResult.vue";

const router = { replace: vi.fn() };
const baseResult = () => ({
  exam_id: 7,
  submission_id: 9,
  score: 80,
  total_score: 100,
  correct_count: 8,
  wrong_count: 2,
  accuracy_rate: 80,
  submitted_at: "2026-07-14T02:30:00.000Z",
});
const store = {
  currentExam: {
    id: 7,
    title: "期末考试",
    questions: [
      { id: 10, question_id: 1, question: "一段很长但必须完整展示的真实题目文本", question_type: "single_choice", score: 2, order_index: 0, options: { A: "答案" } },
    ],
  },
  currentAttempt: {
    id: 3,
    exam_id: 7,
    user_id: 1,
    started_at: "2026-07-14T02:00:00.000Z",
    submitted_at: null,
    score: null,
  },
  answers: { "1": "A" },
  result: baseResult() as Record<string, unknown> | null,
  reset: vi.fn(),
};

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { examId: "7" } }),
  useRouter: () => router,
}));

vi.mock("@/stores/exam", () => ({ useExamStore: () => store }));

describe("ExamResult", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    store.result = baseResult();
    store.currentAttempt.started_at = "2026-07-14T02:00:00.000Z";
    store.answers = { "1": "A" };
  });

  it("renders actual summary data and placeholders for unavailable result fields", () => {
    const wrapper = mount(ExamResult);

    expect(wrapper.attributes("data-reference-page")).toBe("exam-complete");
    expect(wrapper.text()).toContain("80");
    expect(wrapper.text()).toContain("100");
    expect(wrapper.text()).toContain("答对");
    expect(wrapper.text()).toContain("8");
    expect(wrapper.text()).toContain("--");
    expect(wrapper.text()).toContain("一段很长但必须完整展示的真实题目文本");
    expect(wrapper.text()).toContain("A");
    expect(wrapper.get("[data-exam-result-pass]").text()).toBe("--");
    expect(wrapper.get("[data-question-status]").text()).toBe("--");
  });

  it.each([
    "2026-07-14T02:00:00.000000",
    "2026-07-14T02:00:00.000Z",
    "2026-07-14T10:00:00.000+08:00",
  ])("derives duration from API start time %s", (startedAt) => {
    store.currentAttempt.started_at = startedAt;
    const wrapper = mount(ExamResult);

    expect(wrapper.get("[data-exam-result-duration]").text()).toBe("30分0秒");
  });

  it("prefers a provided duration and rejects missing or invalid timestamps", () => {
    store.result = { ...baseResult(), duration_seconds: 125 };
    let wrapper = mount(ExamResult);
    expect(wrapper.get("[data-exam-result-duration]").text()).toBe("2分5秒");

    wrapper.unmount();
    store.result = { ...baseResult(), submitted_at: "not-a-timestamp" };
    wrapper = mount(ExamResult);
    expect(wrapper.get("[data-exam-result-duration]").text()).toBe("--");

    wrapper.unmount();
    store.result = { ...baseResult(), submitted_at: null };
    wrapper = mount(ExamResult);
    expect(wrapper.get("[data-exam-result-duration]").text()).toBe("--");

    wrapper.unmount();
    store.currentAttempt.started_at = "2026-07-14T03:00:00.000Z";
    store.result = baseResult();
    wrapper = mount(ExamResult);
    expect(wrapper.get("[data-exam-result-duration]").text()).toBe("--");
  });

  it("shows correctness only when the response actually provides it", async () => {
    store.result = {
      ...baseResult(),
      passed: false,
      question_results: { "1": { correct: false, answer: "B" } },
    };
    const wrapper = mount(ExamResult);

    expect(wrapper.get("[data-exam-result-pass]").text()).toBe("未通过");
    expect(wrapper.get("[data-question-status]").text()).toBe("错误");
    expect(wrapper.get("[data-question-answer]").text()).toContain("B");
    expect(wrapper.text()).toContain("单选题");
    expect(wrapper.text()).toContain("2 分");
  });

  it("returns to the exam list without changing submission data", async () => {
    const wrapper = mount(ExamResult);

    await wrapper.get('[data-exam-result-action="back"]') .trigger("click");

    expect(store.reset).toHaveBeenCalledOnce();
    expect(router.replace).toHaveBeenCalledWith({ name: "exams" });
  });

  it("keeps leaderboard and retake navigation on their existing named routes", async () => {
    const wrapper = mount(ExamResult);

    await wrapper.get('[data-exam-result-action="leaderboard"]').trigger("click");
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-leaderboard", params: { examId: 7 } });

    await wrapper.get('[data-exam-result-action="retake"]').trigger("click");
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-take", params: { examId: 7 } });
  });

  it("renders a real empty state without inventing a result", () => {
    store.result = null;
    const wrapper = mount(ExamResult);

    expect(wrapper.text()).toContain("暂无考试结果");
    expect(wrapper.text()).not.toContain("80");
  });
});
