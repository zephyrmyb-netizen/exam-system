import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { getExamDetail, startExam, submitExam } from "@/api/exams";
import type { ExamAttempt, ExamDetail } from "@/types";
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

function makeExamDetail(id = 1): ExamDetail {
  return {
    id,
    title: `Exam ${id}`,
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
    questions: [{
      id: id * 10,
      question_id: id * 20,
      question_type: "single_choice",
      question: `${id}+${id}=?`,
      options: { A: "1", B: "2" },
      score: 1,
      order_index: 0,
    }],
  };
}

function makeAttempt(examId = 1, id = examId * 2): ExamAttempt {
  return { id, exam_id: examId, user_id: 1, started_at: null, submitted_at: null, score: null };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

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
    vi.mocked(getExamDetail).mockReset().mockResolvedValue(makeExamDetail());
    vi.mocked(startExam).mockReset().mockResolvedValue(makeAttempt());
    vi.mocked(submitExam).mockReset().mockResolvedValue(submittedResult);
  });

  it("loads exam detail and attempt together", async () => {
    const store = useExamStore();
    await store.startAttempt(1);
    expect(store.currentExam?.title).toBe("Exam 1");
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

  it.each([
    "2026-07-14T02:00:00.000000",
    "2026-07-14T02:00:00.000Z",
    "2026-07-14T10:00:00.000+08:00",
  ])("derives remaining time from API start time %s", async (startedAt) => {
    const store = useExamStore();
    await store.startAttempt(1);

    store.currentAttempt!.started_at = startedAt;
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
    expect(store.currentExam?.id).toBe(1);
    expect(store.answers).toEqual({});
    expect(store.error).toBe("");
    expect(store.submissionError).toContain("network down");

    await expect(store.submitCurrentExam()).resolves.toEqual(submittedResult);
    expect(submitExam).toHaveBeenCalledTimes(2);
    expect(store.error).toBe("");
    expect(store.submissionError).toBe("");
  });

  it("does not repopulate a reset store when a slow attempt start resolves", async () => {
    const store = useExamStore();
    const detail = deferred<ExamDetail>();
    const attempt = deferred<ExamAttempt>();
    vi.mocked(getExamDetail).mockReturnValueOnce(detail.promise);
    vi.mocked(startExam).mockReturnValueOnce(attempt.promise);

    const starting = store.startAttempt(1);
    expect(store.loading).toBe(true);
    store.reset();
    expect(store.loading).toBe(false);

    detail.resolve(makeExamDetail(1));
    attempt.resolve(makeAttempt(1, 11));
    await starting;

    expect(store.currentExam).toBeNull();
    expect(store.currentAttempt).toBeNull();
    expect(store.error).toBe("");
    expect(store.loading).toBe(false);
  });

  it("keeps the newest attempt when different exams start out of order", async () => {
    const store = useExamStore();
    const firstDetail = deferred<ExamDetail>();
    const firstAttempt = deferred<ExamAttempt>();
    const secondDetail = deferred<ExamDetail>();
    const secondAttempt = deferred<ExamAttempt>();
    vi.mocked(getExamDetail)
      .mockReturnValueOnce(firstDetail.promise)
      .mockReturnValueOnce(secondDetail.promise);
    vi.mocked(startExam)
      .mockReturnValueOnce(firstAttempt.promise)
      .mockReturnValueOnce(secondAttempt.promise);

    const firstStart = store.startAttempt(1);
    const secondStart = store.startAttempt(2);
    secondDetail.resolve(makeExamDetail(2));
    secondAttempt.resolve(makeAttempt(2, 22));
    await secondStart;
    firstDetail.resolve(makeExamDetail(1));
    firstAttempt.resolve(makeAttempt(1, 11));
    await firstStart;

    expect(store.currentExam?.id).toBe(2);
    expect(store.currentAttempt?.id).toBe(22);
    expect(store.error).toBe("");
    expect(store.loading).toBe(false);
  });

  it("keeps the newest same-exam attempt when starts resolve out of order", async () => {
    const store = useExamStore();
    const firstDetail = deferred<ExamDetail>();
    const firstAttempt = deferred<ExamAttempt>();
    const secondDetail = deferred<ExamDetail>();
    const secondAttempt = deferred<ExamAttempt>();
    vi.mocked(getExamDetail)
      .mockReturnValueOnce(firstDetail.promise)
      .mockReturnValueOnce(secondDetail.promise);
    vi.mocked(startExam)
      .mockReturnValueOnce(firstAttempt.promise)
      .mockReturnValueOnce(secondAttempt.promise);

    const firstStart = store.startAttempt(1);
    const secondStart = store.startAttempt(1);
    secondDetail.resolve(makeExamDetail(1));
    secondAttempt.resolve(makeAttempt(1, 12));
    await secondStart;
    firstDetail.resolve(makeExamDetail(1));
    firstAttempt.resolve(makeAttempt(1, 11));
    await firstStart;

    expect(store.currentExam?.id).toBe(1);
    expect(store.currentAttempt?.id).toBe(12);
  });

  it("ignores stale load errors after a newer exam detail succeeds", async () => {
    const store = useExamStore();
    const firstDetail = deferred<ExamDetail>();
    const secondDetail = deferred<ExamDetail>();
    vi.mocked(getExamDetail)
      .mockReturnValueOnce(firstDetail.promise)
      .mockReturnValueOnce(secondDetail.promise);

    const firstLoad = store.loadExam(1);
    const secondLoad = store.loadExam(2);
    secondDetail.resolve(makeExamDetail(2));
    await secondLoad;
    firstDetail.reject(new Error("stale failure"));
    await expect(firstLoad).rejects.toThrow("stale failure");

    expect(store.currentExam?.id).toBe(2);
    expect(store.error).toBe("");
    expect(store.loading).toBe(false);
  });

  it("keeps the newest exam detail when loads resolve out of order", async () => {
    const store = useExamStore();
    const firstDetail = deferred<ExamDetail>();
    const secondDetail = deferred<ExamDetail>();
    vi.mocked(getExamDetail)
      .mockReturnValueOnce(firstDetail.promise)
      .mockReturnValueOnce(secondDetail.promise);

    const firstLoad = store.loadExam(1);
    const secondLoad = store.loadExam(2);
    secondDetail.resolve(makeExamDetail(2));
    await secondLoad;
    firstDetail.resolve(makeExamDetail(1));
    await firstLoad;

    expect(store.currentExam?.id).toBe(2);
    expect(store.loading).toBe(false);
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
