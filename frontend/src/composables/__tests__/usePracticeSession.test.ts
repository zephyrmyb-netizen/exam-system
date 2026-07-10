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

function wrongResult(): SubmitResponse {
  return {
    is_correct: false,
    correct_answer: "B",
    analysis: "答案解析",
    wrongbook_recorded: true,
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

  it("does not show a duplicate question when the backend ignores exclusions", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });

    getRandomPracticeQuestion
      .mockResolvedValueOnce(makeQuestion(1))
      .mockResolvedValueOnce(makeQuestion(1))
      .mockResolvedValueOnce(makeQuestion(2));
    submitPracticeAnswer.mockResolvedValue(correctResult());

    await session.startSession();
    await flushPromises();
    expect(session.question.value?.id).toBe(1);

    session.setSingleAnswer("A");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(650);
    await flushPromises();

    expect(session.question.value?.id).toBe(2);
    expect(getRandomPracticeQuestion).toHaveBeenCalledTimes(3);
  });

  it("enters the completed state when there are no questions to practice", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });

    getRandomPracticeQuestion.mockResolvedValueOnce(null);

    session.startSession();
    await flushPromises();

    expect(session.question.value).toBeNull();
    expect(session.sessionComplete.value).toBe(true);
    expect(session.errorMessage.value).toBe("");
  });

  it("moves to the next question after a correct single-choice answer", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });

    getRandomPracticeQuestion
      .mockResolvedValueOnce(makeQuestion(1))
      .mockResolvedValueOnce(makeQuestion(2));
    submitPracticeAnswer.mockResolvedValueOnce(correctResult());

    session.startSession();
    await flushPromises();
    session.setSingleAnswer("A");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(650);
    await flushPromises();

    expect(session.question.value?.id).toBe(2);
    expect(session.sessionStats.value.answeredCount).toBe(1);
  });

  it("keeps the current question and analysis visible after a wrong answer", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });

    getRandomPracticeQuestion.mockResolvedValueOnce(makeQuestion(1));
    submitPracticeAnswer.mockResolvedValueOnce(wrongResult());

    session.startSession();
    await flushPromises();
    session.setSingleAnswer("B");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(2_000);

    expect(session.question.value?.id).toBe(1);
    expect(session.result.value?.is_correct).toBe(false);
    expect(session.result.value?.analysis).toBe("答案解析");
    expect(getRandomPracticeQuestion).toHaveBeenCalledTimes(1);
  });

  it("does not auto-submit a multiple-choice question while selecting options", async () => {
    const { usePracticeSession } = await import("../usePracticeSession");
    const session = usePracticeSession({ courseId: 9 });
    const multipleQuestion = { ...makeQuestion(1), type: "multiple_choice" } as Question;

    getRandomPracticeQuestion.mockResolvedValueOnce(multipleQuestion);

    session.startSession();
    await flushPromises();
    session.toggleMultipleAnswer("A");
    session.toggleMultipleAnswer("B");
    await flushPromises();

    expect(session.selectedAnswers.value).toEqual(["A", "B"]);
    expect(submitPracticeAnswer).not.toHaveBeenCalled();
    expect(session.canSubmit.value).toBe(true);
  });
});
