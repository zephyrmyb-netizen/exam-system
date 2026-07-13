import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { submitExam } from "@/api/exams";
import { useExamStore } from "../exam";

const submittedResult = {
  exam_id: 1,
  submission_id: 2,
  score: 100,
  total_score: 100,
  correct_count: 1,
  wrong_count: 0,
  accuracy_rate: 100,
  submitted_at: "2026-07-14T03:00:00.000Z",
};

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
  getExamLeaderboard: vi.fn(async () => ({
    exam_id: 1,
    total: 1,
    entries: [
      {
        rank: 1,
        user_id: 1,
        username: "student",
        score: 100,
        total_score: 100,
        submitted_at: null,
      },
    ],
  })),
  startExam: vi.fn(async () => ({
    id: 2,
    exam_id: 1,
    user_id: 1,
    started_at: null,
    submitted_at: null,
    score: null,
  })),
  submitExam: vi.fn(),
}));

describe("exam store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(submitExam).mockReset().mockResolvedValue(submittedResult);
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

  it("derives remaining time from the attempt start time", async () => {
    const store = useExamStore();
    await store.startAttempt(1);

    store.currentAttempt!.started_at = "2026-07-14T02:00:00.000Z";
    store.syncRemainingSeconds(Date.parse("2026-07-14T02:12:34.000Z"));

    expect(store.remainingSeconds).toBe(47 * 60 + 26);
  });

  it("does not invent a countdown when the server did not provide a start time", async () => {
    const store = useExamStore();
    await store.startAttempt(1);

    expect(store.remainingSeconds).toBeNull();
  });

  it("does not expose NaN when the server start time is invalid", async () => {
    const store = useExamStore();
    await store.startAttempt(1);

    store.currentAttempt!.started_at = "not-a-timestamp";
    store.syncRemainingSeconds(Date.parse("2026-07-14T02:12:34.000Z"));

    expect(store.remainingSeconds).toBeNull();
  });

  it("shares one in-flight submission across concurrent manual and timer calls", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    store.setAnswer(20, "B");

    let resolveSubmission!: (value: typeof submittedResult) => void;
    vi.mocked(submitExam).mockImplementationOnce(() => new Promise((resolve) => {
      resolveSubmission = resolve;
    }));

    const manualSubmission = store.submitCurrentExam();
    const timerSubmission = store.submitCurrentExam();

    expect(submitExam).toHaveBeenCalledOnce();
    expect(store.submitting).toBe(true);

    resolveSubmission(submittedResult);
    await expect(Promise.all([manualSubmission, timerSubmission])).resolves.toEqual([submittedResult, submittedResult]);
    expect(store.submitting).toBe(false);
    expect(store.result).toEqual(submittedResult);
  });

  it("clears the in-flight guard after failure so a safe retry can submit", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    vi.mocked(submitExam)
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce(submittedResult);

    await expect(store.submitCurrentExam()).rejects.toThrow("network down");
    expect(store.submitting).toBe(false);

    await expect(store.submitCurrentExam()).resolves.toEqual(submittedResult);
    expect(submitExam).toHaveBeenCalledTimes(2);
    expect(store.error).toBe("");
  });

  it("ignores an old completion after a new attempt starts for the same exam", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    let resolveOldSubmission!: (value: typeof submittedResult) => void;
    vi.mocked(submitExam).mockImplementationOnce(() => new Promise((resolve) => {
      resolveOldSubmission = resolve;
    }));

    const oldSubmission = store.submitCurrentExam();
    await store.startAttempt(1);
    resolveOldSubmission(submittedResult);
    await oldSubmission;

    expect(store.result).toBeNull();
    expect(store.error).toBe("");
    expect(store.submitting).toBe(false);
  });

  it("loads exam leaderboard", async () => {
    const store = useExamStore();
    const leaderboard = await store.fetchLeaderboard(1);
    expect(leaderboard.total).toBe(1);
    expect(store.leaderboard?.entries[0].rank).toBe(1);
  });
});
