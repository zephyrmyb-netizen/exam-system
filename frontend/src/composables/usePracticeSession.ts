import { computed, ref, type Ref, type ComputedRef } from "vue";
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
import type { Question, SubmitResponse, OptionItem } from "../types";

interface SessionStats {
  answeredCount: number;
  correctCount: number;
  wrongCount: number;
  streak: number;
  startedAt: Date | null;
}

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
  correctAnswerDisplay: ComputedRef<string>;
  currentAnswer: ComputedRef<string>;
  errorMessage: Ref<string>;
  fetchRandomQuestion: () => Promise<void>;
  handleTextKeydown: (event: KeyboardEvent) => void;
  hasAnswerSelected: ComputedRef<boolean>;
  isTextQuestion: ComputedRef<boolean>;
  loading: Ref<boolean>;
  question: Ref<Question | null>;
  result: Ref<SubmitResponse | null>;
  selectedAnswer: Ref<string>;
  selectedAnswers: Ref<string[]>;
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

export function usePracticeSession(props: UsePracticeSessionProps = {}): UsePracticeSessionReturn {
  const question = ref<Question | null>(null);
  const selectedAnswer = ref<string>("");
  const selectedAnswers = ref<string[]>([]);
  const textAnswer = ref<string>("");
  const result = ref<SubmitResponse | null>(null);
  const loading = ref<boolean>(false);
  const submitting = ref<boolean>(false);
  const errorMessage = ref<string>("");
  const validationMessage = ref<string>("");
  const sessionStats = ref<SessionStats>(createSessionStats());

  const accuracy = computed<number | null>(() => {
    const answered = sessionStats.value.answeredCount;
    if (answered === 0) return null;
    return Math.round((sessionStats.value.correctCount / answered) * 100);
  });

  const streakText = computed<string>(() => {
    const streak = sessionStats.value.streak;
    if (streak === 0) return "0";
    if (streak >= 5) return `🔥 ${streak}`;
    if (streak >= 3) return `⭐ ${streak}`;
    return `✓ ${streak}`;
  });

  const isTextQuestion = computed<boolean>(() => isTextQuestionType(question.value?.type ?? ""));

  const currentAnswer = computed<string>(() => {
    if (!question.value) return "";
    if (question.value.type === "multiple_choice") {
      return [...selectedAnswers.value].sort().join(",");
    }
    if (isTextQuestion.value) return textAnswer.value.trim();
    return selectedAnswer.value;
  });

  const answerOptions = computed<OptionItem[]>(() => {
    if (!question.value) return [];
    if (question.value.type === "true_false") return TRUE_FALSE_OPTIONS;

    const options = formatOptions(question.value.options);
    return options.length > 0
      ? options
      : ["A", "B", "C", "D"].map((key) => ({ key, value: key }));
  });

  const hasAnswerSelected = computed<boolean>(() => {
    if (!question.value) return false;
    if (question.value.type === "multiple_choice") {
      return selectedAnswers.value.length > 0;
    }
    if (isTextQuestion.value) return textAnswer.value.trim().length > 0;
    return selectedAnswer.value.length > 0;
  });

  const canSubmit = computed<boolean>(() => hasAnswerSelected.value && !submitting.value);

  const answerHint = computed<string>(() => getQuestionAnswerHint(question.value?.type ?? ""));

  const correctAnswerDisplay = computed<string>(() =>
    getResultCorrectAnswer(question.value?.type ?? "", result.value?.correct_answer ?? ""),
  );

  function resetAnswerState(): void {
    selectedAnswer.value = "";
    selectedAnswers.value = [];
    textAnswer.value = "";
    result.value = null;
    validationMessage.value = "";
  }

  async function fetchRandomQuestion(): Promise<void> {
    loading.value = true;
    errorMessage.value = "";
    validationMessage.value = "";
    resetAnswerState();

    try {
      const params: Record<string, string | number> = {};
      if (props.courseId) params.course_id = props.courseId;

      let data: Question;
      if (props.mode === "wrong_review") {
        data = await getReviewWrongQuestion(params);
      } else if (props.mode === "due_review") {
        data = await getReviewDueQuestion(params);
      } else {
        if (props.mode === "type_practice" && props.modeParam) params.type = props.modeParam;
        if (props.mode === "chapter_practice" && props.modeParam) params.chapter = props.modeParam;
        data = await getRandomPracticeQuestion(params);
      }

      question.value = data;
    } catch (error: unknown) {
      question.value = null;
      errorMessage.value = getErrorMessage(error, "获取题目失败");
    } finally {
      loading.value = false;
    }
  }

  function setSingleAnswer(value: string): void {
    if (result.value) return;
    selectedAnswer.value = value;
    validationMessage.value = "";
  }

  function toggleMultipleAnswer(key: string): void {
    if (result.value) return;
    if (selectedAnswers.value.includes(key)) {
      selectedAnswers.value = selectedAnswers.value.filter((item) => item !== key);
    } else {
      selectedAnswers.value = [...selectedAnswers.value, key];
    }
    validationMessage.value = "";
  }

  function updateTextAnswer(value: string): void {
    textAnswer.value = value;
    validationMessage.value = "";
  }

  async function submitAnswer(): Promise<void> {
    if (!question.value) return;

    if (question.value.type === "multiple_choice" && selectedAnswers.value.length === 0) {
      validationMessage.value = "请至少选择一个选项。";
      return;
    }

    if (!currentAnswer.value) {
      validationMessage.value = isTextQuestion.value
        ? "请先填写你的答案。"
        : "请先选择一个选项。";
      return;
    }

    submitting.value = true;
    errorMessage.value = "";
    validationMessage.value = "";

    try {
      const data = await submitPracticeAnswer({
        question_id: question.value.id,
        user_answer: currentAnswer.value,
      });

      result.value = data;
      sessionStats.value.answeredCount += 1;
      if (data.is_correct) {
        sessionStats.value.correctCount += 1;
        sessionStats.value.streak += 1;
      } else {
        sessionStats.value.wrongCount += 1;
        sessionStats.value.streak = 0;
      }
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "提交答案失败");
    } finally {
      submitting.value = false;
    }
  }

  function handleTextKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!result.value && !submitting.value) {
        submitAnswer();
      }
    }
  }

  function startSession(): void {
    sessionStats.value = {
      ...createSessionStats(),
      startedAt: new Date(),
    };
    fetchRandomQuestion();
  }

  return {
    answerHint,
    answerOptions,
    accuracy,
    canSubmit,
    correctAnswerDisplay,
    currentAnswer,
    errorMessage,
    fetchRandomQuestion,
    handleTextKeydown,
    hasAnswerSelected,
    isTextQuestion,
    loading,
    question,
    result,
    selectedAnswer,
    selectedAnswers,
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
