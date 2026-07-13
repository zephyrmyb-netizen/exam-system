import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ExamResult from "../ExamResult.vue";

const router = { replace: vi.fn() };
const store = {
  currentExam: {
    id: 7,
    title: "期末考试",
    questions: [
      { question_id: 1, question: "题目一", question_type: "single_choice", score: 2, options: { A: "答案" } },
    ],
  },
  answers: { "1": "A" },
  result: {
    exam_id: 7,
    submission_id: 9,
    score: 80,
    total_score: 100,
    correct_count: 8,
    wrong_count: 2,
    accuracy_rate: 80,
    submitted_at: "2026-07-14T02:30:00.000Z",
  },
  reset: vi.fn(),
};

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { examId: "7" } }),
  useRouter: () => router,
}));

vi.mock("@/stores/exam", () => ({ useExamStore: () => store }));

describe("ExamResult", () => {
  it("renders actual summary data and placeholders for unavailable result fields", () => {
    const wrapper = mount(ExamResult);

    expect(wrapper.text()).toContain("80");
    expect(wrapper.text()).toContain("100");
    expect(wrapper.text()).toContain("答对");
    expect(wrapper.text()).toContain("8");
    expect(wrapper.text()).toContain("--");
    expect(wrapper.text()).toContain("题目一");
    expect(wrapper.text()).toContain("A");
  });

  it("returns to the exam list without changing submission data", async () => {
    const wrapper = mount(ExamResult);

    await wrapper.get('[data-exam-result-action="back"]') .trigger("click");

    expect(store.reset).toHaveBeenCalledOnce();
    expect(router.replace).toHaveBeenCalledWith({ name: "exams" });
  });
});
