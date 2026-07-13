import { computed, getCurrentScope, onScopeDispose, ref, type ComputedRef, type Ref } from "vue";
import { createActor } from "xstate";

import { getErrorMessage } from "../api/request";
import {
  getRandomPracticeQuestion,
  getReviewDueQuestion,
  getReviewWrongQuestion,
  submitPracticeAnswer,
} from "../api/practice";
import {
  formatOptions,
  getQuestionAnswerHint,
  getResultCorrectAnswer,
  isTextQuestionType,
  TRUE_FALSE_OPTIONS,
} from "../utils/question";
import {
  practiceSessionMachine,
  type PracticeSessionPhase,
} from "../features/practice/practiceSessionMachine";
import type { OptionItem, Question, SubmitResponse } from "../types";

interface SessionStats {
  answeredCount: number;
  correctCount: number;
  wrongCount: number;
  streak: number;
  startedAt: Date | null;
}

const CORRECT_AUTO_NEXT_DELAY_MS = 650;
const MAX_DUPLICATE_FETCH_ATTEMPTS = 8;

export interface UsePracticeSessionProps {
  courseId?: number | null;
  mode?: string;
  modeParam?: string;
}

export interface UsePracticeSessionReturn {
  answerHint: ComputedRef<string>;
  answerOptions: ComputedRef<OptionItem[]>;
  accuracy: ComputedRef<number | null>;
  canSubmit: ComputedRef<boolean>;
  cancelPendingAdvance: () => void;
  correctAnswerDisplay: ComputedRef<string>;
  currentAnswer: ComputedRef<string>;
  errorMessage: Ref<string>;
  fetchRandomQuestion: () => Promise<void>;
  handleTextKeydown: (event: KeyboardEvent) => void;
  hasAnswerSelected: ComputedRef<boolean>;
  isTextQuestion: ComputedRef<boolean>;
  loading: Ref<boolean>;
  phase: Ref<PracticeSessionPhase>;
  question: Ref<Question | null>;
  result: Ref<SubmitResponse | null>;
  selectedAnswer: Ref<string>;
  selectedAnswers: Ref<string[]>;
  sessionComplete: Ref<boolean>;
  sessionStats: Ref<SessionStats>;
  setSingleAnswer: (value: string) => void;
  startSession: () => void;
  streakText: ComputedRef<string>;
  submitAnswer: () => Promise<void>;
  submitting: Ref<boolean>;
  textAnswer: Ref<string>;
  toggleMultipleAnswer: (key: string) => void;
  updateTextAnswer: (value: string) => void;
  validationMessage: Ref<string>;
}

function createSessionStats(): SessionStats {
  return {
    answeredCount: 0,
    correctCount: 0,
    wrongCount: 0,
    streak: 0,
    startedAt: null,
  };
}

function isQuestionLike(value: unknown): value is Question {
  return typeof value === "object" && value !== null && typeof (value as { id?: unknown }).id === "number";
}

function extractDueReviewQuestion(value: unknown): Question | null {
  if (isQuestionLike(value)) return value;
  if (typeof value !== "object" || value === null) return null;

  const payload = value as { question?: unknown; items?: Array<{ question?: unknown }> };
  if (isQuestionLike(payload.question)) return payload.question;
  const item = payload.items?.find((entry) => isQuestionLike(entry.question));
  return isQuestionLike(item?.question) ? item.question : null;
}

export function usePracticeSession(props: UsePracticeSessionProps = {}): UsePracticeSessionReturn {
  const question = ref<Question | null>(null);
  const selectedAnswer = ref("");
  const selectedAnswers = ref<string[]>([]);
  const textAnswer = ref("");
  const result = ref<SubmitResponse | null>(null);
  const loading = ref(false);
  const submitting = ref(false);
  const errorMessage = ref("");
  const validationMessage = ref("");
  const sessionComplete = ref(false);
  const sessionStats = ref<SessionStats>(createSessionStats());
  const phase = ref<PracticeSessionPhase>("idle");
  const answeredQuestionIds = new Set<number>();
  const actor = createActor(practiceSessionMachine);
  const subscription = actor.subscribe((snapshot) => {
    phase.value = snapshot.value as PracticeSessionPhase;
  });
  let correctAutoNextTimer: ReturnType<typeof setTimeout> | null = null;
  let requestVersion = 0;

  actor.start();

  if (getCurrentScope()) {
    onScopeDispose(() => {
      clearCorrectAutoNextTimer();
      requestVersion += 1;
      subscription.unsubscribe();
      actor.stop();
    });
  }

  function clearCorrectAutoNextTimer(): void {
    if (correctAutoNextTimer) {
      clearTimeout(correctAutoNextTimer);
      correctAutoNextTimer = null;
    }
  }

  /** Stop a pending correct-answer advance before a summary or route exit. */
  function cancelPendingAdvance(): void {
    clearCorrectAutoNextTimer();
    requestVersion += 1;
  }

  const accuracy = computed<number | null>(() => {
    const answered = sessionStats.value.answeredCount;
    return answered ? Math.round((sessionStats.value.correctCount / answered) * 100) : null;
  });

  const streakText = computed(() => {
    const streak = sessionStats.value.streak;
    if (!streak) return "0";
    if (streak >= 5) return `🔥 ${streak}`;
    if (streak >= 3) return `⭐ ${streak}`;
    return `✓ ${streak}`;
  });

  const isTextQuestion = computed(() => isTextQuestionType(question.value?.type ?? ""));
  const currentAnswer = computed(() => {
    if (!question.value) return "";
    if (question.value.type === "multiple_choice") return [...selectedAnswers.value].sort().join(",");
    if (isTextQuestion.value) return textAnswer.value.trim();
    return selectedAnswer.value;
  });
  const answerOptions = computed<OptionItem[]>(() => {
    if (!question.value) return [];
    if (question.value.type === "true_false") return TRUE_FALSE_OPTIONS;
    const options = formatOptions(question.value.options);
    return options.length ? options : ["A", "B", "C", "D"].map((key) => ({ key, value: key }));
  });
  const hasAnswerSelected = computed(() => {
    if (!question.value) return false;
    if (question.value.type === "multiple_choice") return selectedAnswers.value.length > 0;
    if (isTextQuestion.value) return textAnswer.value.trim().length > 0;
    return selectedAnswer.value.length > 0;
  });
  const canSubmit = computed(() => hasAnswerSelected.value && phase.value === "answering" && !submitting.value);
  const answerHint = computed(() => getQuestionAnswerHint(question.value?.type ?? ""));
  const correctAnswerDisplay = computed(() =>
    getResultCorrectAnswer(question.value?.type ?? "", result.value?.correct_answer ?? ""),
  );

  function resetAnswerState(): void {
    selectedAnswer.value = "";
    selectedAnswers.value = [];
    textAnswer.value = "";
    result.value = null;
    validationMessage.value = "";
  }

  function enterLoading(allowSessionRestart = false): boolean {
    if (phase.value === "idle") {
      actor.send({ type: "START" });
      return true;
    }
    if (phase.value === "completed") {
      if (!allowSessionRestart) return false;
      actor.send({ type: "START" });
      return true;
    }
    if (phase.value === "correct" || phase.value === "wrong") {
      actor.send({ type: "NEXT" });
      return true;
    }
    if (phase.value === "error") {
      actor.send({ type: "RETRY" });
      return true;
    }
    return false;
  }

  function completeSession(): void {
    clearCorrectAutoNextTimer();
    question.value = null;
    resetAnswerState();
    sessionComplete.value = true;
    if (phase.value !== "completed") actor.send({ type: "NO_MORE_QUESTIONS" });
  }

  async function fetchRandomQuestion(allowSessionRestart = false): Promise<void> {
    if (loading.value || !enterLoading(allowSessionRestart)) return;

    clearCorrectAutoNextTimer();
    const currentRequest = ++requestVersion;
    loading.value = true;
    errorMessage.value = "";
    validationMessage.value = "";
    resetAnswerState();

    try {
      const params: Record<string, string | number> = {};
      if (props.courseId) params.course_id = props.courseId;
      if (answeredQuestionIds.size) params.exclude_ids = Array.from(answeredQuestionIds).join(",");
      if (props.mode === "type_practice" && props.modeParam) params.type = props.modeParam;
      if (props.mode === "chapter_practice" && props.modeParam) params.chapter = props.modeParam;

      let data: Question | null = null;
      for (let attempt = 0; attempt < MAX_DUPLICATE_FETCH_ATTEMPTS; attempt += 1) {
        if (props.mode === "wrong_review") {
          data = await getReviewWrongQuestion(params);
        } else if (props.mode === "due_review") {
          data = extractDueReviewQuestion(await getReviewDueQuestion(params));
        } else {
          data = await getRandomPracticeQuestion(params);
        }

        if (!data) break;
        if (!answeredQuestionIds.has(data.id)) break;
        data = null;
      }

      if (currentRequest !== requestVersion) return;
      if (!data) {
        completeSession();
        return;
      }

      question.value = data;
      sessionComplete.value = false;
      actor.send({ type: "QUESTION_READY" });
    } catch (error: unknown) {
      if (currentRequest !== requestVersion) return;
      question.value = null;
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        completeSession();
      } else {
        errorMessage.value = getErrorMessage(error, "获取题目失败");
        actor.send({ type: "LOAD_FAILED" });
      }
    } finally {
      if (currentRequest === requestVersion) loading.value = false;
    }
  }

  function setSingleAnswer(value: string): void {
    if (phase.value !== "answering" || result.value || submitting.value) return;
    selectedAnswer.value = value;
    validationMessage.value = "";
    void submitAnswer();
  }

  function toggleMultipleAnswer(key: string): void {
    if (phase.value !== "answering" || result.value || submitting.value) return;
    selectedAnswers.value = selectedAnswers.value.includes(key)
      ? selectedAnswers.value.filter((item) => item !== key)
      : [...selectedAnswers.value, key];
    validationMessage.value = "";
  }

  function updateTextAnswer(value: string): void {
    if (phase.value !== "answering") return;
    textAnswer.value = value;
    validationMessage.value = "";
  }

  async function submitAnswer(): Promise<void> {
    if (!question.value || phase.value !== "answering" || result.value) return;
    if (!currentAnswer.value) {
      validationMessage.value = isTextQuestion.value ? "请先填写你的答案。" : "请选择一个选项";
      return;
    }

    const questionId = question.value.id;
    actor.send({ type: "SUBMIT" });
    submitting.value = true;
    errorMessage.value = "";
    validationMessage.value = "";

    try {
      const data = await submitPracticeAnswer({ question_id: questionId, user_answer: currentAnswer.value });
      if (question.value?.id !== questionId) return;

      result.value = data;
      sessionStats.value.answeredCount += 1;
      answeredQuestionIds.add(questionId);

      if (data.is_correct) {
        sessionStats.value.correctCount += 1;
        sessionStats.value.streak += 1;
        actor.send({ type: "ANSWER_CORRECT" });
        correctAutoNextTimer = setTimeout(() => {
          correctAutoNextTimer = null;
          void fetchRandomQuestion();
        }, CORRECT_AUTO_NEXT_DELAY_MS);
      } else {
        sessionStats.value.wrongCount += 1;
        sessionStats.value.streak = 0;
        actor.send({ type: "ANSWER_WRONG" });
      }
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "提交答案失败");
      actor.send({ type: "SUBMIT_FAILED" });
    } finally {
      submitting.value = false;
    }
  }

  function handleTextKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitAnswer();
    }
  }

  function startSession(): void {
    cancelPendingAdvance();
    answeredQuestionIds.clear();
    sessionComplete.value = false;
    sessionStats.value = { ...createSessionStats(), startedAt: new Date() };
    resetAnswerState();
    if (phase.value !== "idle" && phase.value !== "completed") {
      question.value = null;
    }
    void fetchRandomQuestion(true);
  }

  return {
    answerHint,
    answerOptions,
    accuracy,
    canSubmit,
    cancelPendingAdvance,
    correctAnswerDisplay,
    currentAnswer,
    errorMessage,
    fetchRandomQuestion,
    handleTextKeydown,
    hasAnswerSelected,
    isTextQuestion,
    loading,
    phase,
    question,
    result,
    selectedAnswer,
    selectedAnswers,
    sessionComplete,
    sessionStats,
    setSingleAnswer,
    startSession,
    streakText,
    submitAnswer,
    submitting,
    textAnswer,
    toggleMultipleAnswer,
    updateTextAnswer,
    validationMessage,
  };
}
