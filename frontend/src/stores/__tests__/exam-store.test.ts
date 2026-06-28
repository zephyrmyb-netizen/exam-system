import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useExamStore } from "../exam";

vi.mock("@/api/exams", () => ({
  getExamDetail: vi.fn(async () => ({
    id: 1,
    title: "Java Exam",
    description: "",
    course_id: 1,
    creator_id: 1,
    time_limit: 60,
    total_score: 100,
    is_shuffle: false,
    is_blind: true,
    status: "published",
    question_count: 1,
    created_at: null,
    questions: [
      {
        id: 10,
        question_id: 20,
        question_type: "single_choice",
        question: "1+1=?",
        options: { A: "1", B: "2" },
        score: 1,
        order_index: 0,
      },
    ],
  })),
  listExams: vi.fn(async () => ({ items: [], total: 0, page: 1, page_size: 20 })),
  listMyExams: vi.fn(async () => ({ items: [], total: 0, page: 1, page_size: 20 })),
  startExam: vi.fn(async () => ({
    id: 2,
    exam_id: 1,
    user_id: 1,
    started_at: null,
    submitted_at: null,
    score: null,
  })),
  submitExam: vi.fn(async () => ({
    exam_id: 1,
    submission_id: 2,
    score: 100,
    total_score: 100,
    correct_count: 1,
    wrong_count: 0,
    accuracy_rate: 100,
    submitted_at: null,
  })),
}));

describe("exam store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("loads exam detail and attempt together", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    expect(store.currentExam?.title).toBe("Java Exam");
    expect(store.currentAttempt?.exam_id).toBe(1);
    expect(store.currentQuestion?.question_id).toBe(20);
  });

  it("tracks answers and submission result", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    store.setAnswer(20, "B");
    const result = await store.submitCurrentExam();
    expect(store.answeredCount).toBe(1);
    expect(result.score).toBe(100);
    expect(store.result?.accuracy_rate).toBe(100);
  });
});
