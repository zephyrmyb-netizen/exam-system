import { flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import type { Question, SubmitResponse } from "../../types";

const getRandomPracticeQuestion = vi.fn();
const submitPracticeAnswer = vi.fn();

vi.mock("../../api/practice", () => ({
  getRandomPracticeQuestion,
  getReviewDueQuestion: vi.fn(),
  getReviewWrongQuestion: vi.fn(),
  submitPracticeAnswer,
}));

function makeQuestion(id: number): Question {
  return {
    id,
    owner_id: 1,
    course_id: 9,
    visibility: "private",
    source: "manual",
    created_at: null,
    subject: "",
    chapter: "",
    type: "single_choice",
    question: `Q${id}?`,
    options: { A: "A", B: "B" },
    answer: "A",
    analysis: "",
    difficulty: "normal",
  };
}

function correctResult(): SubmitResponse {
  return {
    is_correct: true,
    correct_answer: "A",
    analysis: "",
    wrongbook_recorded: false,
  };
}

describe("usePracticeSession", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("excludes answered questions and completes the session instead of looping", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });

    getRandomPracticeQuestion
      .mockResolvedValueOnce(makeQuestion(1))
      .mockResolvedValueOnce(makeQuestion(2))
      .mockRejectedValueOnce({ response: { status: 404, data: { detail: "本轮题目已完成" } } });
    submitPracticeAnswer.mockResolvedValue(correctResult());

    await session.startSession();
    await flushPromises();
    expect(session.question.value?.id).toBe(1);
    expect(getRandomPracticeQuestion).toHaveBeenLastCalledWith({ course_id: 9 });

    session.setSingleAnswer("A");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(650);
    await flushPromises();

    expect(session.question.value?.id).toBe(2);
    expect(getRandomPracticeQuestion).toHaveBeenLastCalledWith({ course_id: 9, exclude_ids: "1" });

    session.setSingleAnswer("A");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(650);
    await flushPromises();

    expect(getRandomPracticeQuestion).toHaveBeenLastCalledWith({ course_id: 9, exclude_ids: "1,2" });
    expect(session.question.value).toBeNull();
    expect(session.sessionComplete.value).toBe(true);
    expect(session.errorMessage.value).toBe("");
  });
});
