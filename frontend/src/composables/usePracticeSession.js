import { computed, ref } from "vue";
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

function createSessionStats() {
  return {
    answeredCount: 0,
    correctCount: 0,
    wrongCount: 0,
    streak: 0,
    startedAt: null,
  };
}

export function usePracticeSession(props) {
  const question = ref(null);
  const selectedAnswer = ref("");
  const selectedAnswers = ref([]);
  const textAnswer = ref("");
  const result = ref(null);
  const loading = ref(false);
  const submitting = ref(false);
  const errorMessage = ref("");
  const validationMessage = ref("");
  const sessionStats = ref(createSessionStats());

  const accuracy = computed(() => {
    const answered = sessionStats.value.answeredCount;
    if (answered === 0) return null;
    return Math.round((sessionStats.value.correctCount / answered) * 100);
  });

  const streakText = computed(() => {
    const streak = sessionStats.value.streak;
    if (streak === 0) return "0";
    if (streak >= 5) return `🔥 ${streak}`;
    if (streak >= 3) return `⭐ ${streak}`;
    return `✓ ${streak}`;
  });

  const isTextQuestion = computed(() => isTextQuestionType(question.value?.type));

  const currentAnswer = computed(() => {
    if (!question.value) return "";
    if (question.value.type === "multiple_choice") {
      return [...selectedAnswers.value].sort().join(",");
    }
    if (isTextQuestion.value) return textAnswer.value.trim();
    return selectedAnswer.value;
  });

  const answerOptions = computed(() => {
    if (!question.value) return [];
    if (question.value.type === "true_false") return TRUE_FALSE_OPTIONS;

    const options = formatOptions(question.value.options);
    return options.length > 0
      ? options
      : ["A", "B", "C", "D"].map((key) => ({ key, value: key }));
  });

  const hasAnswerSelected = computed(() => {
    if (!question.value) return false;
    if (question.value.type === "multiple_choice") {
      return selectedAnswers.value.length > 0;
    }
    if (isTextQuestion.value) return textAnswer.value.trim().length > 0;
    return selectedAnswer.value.length > 0;
  });

  const canSubmit = computed(() => hasAnswerSelected.value && !submitting.value);

  const answerHint = computed(() => getQuestionAnswerHint(question.value?.type));

  const correctAnswerDisplay = computed(() =>
    getResultCorrectAnswer(question.value?.type, result.value?.correct_answer),
  );

  function resetAnswerState() {
    selectedAnswer.value = "";
    selectedAnswers.value = [];
    textAnswer.value = "";
    result.value = null;
    validationMessage.value = "";
  }

  async function fetchRandomQuestion() {
    loading.value = true;
    errorMessage.value = "";
    validationMessage.value = "";
    resetAnswerState();

    try {
      const params = {};
      if (props.courseId) params.course_id = props.courseId;

      let data;
      if (props.mode === "wrong_review") {
        data = await getReviewWrongQuestion(params);
      } else if (props.mode === "due_review") {
        data = await getReviewDueQuestion(params);
      } else {
        if (props.mode === "type_practice") params.type = props.modeParam;
        if (props.mode === "chapter_practice") params.chapter = props.modeParam;
        data = await getRandomPracticeQuestion(params);
      }

      question.value = data;
    } catch (error) {
      question.value = null;
      errorMessage.value = getErrorMessage(error, "获取题目失败");
    } finally {
      loading.value = false;
    }
  }

  function setSingleAnswer(value) {
    if (result.value) return;
    selectedAnswer.value = value;
    validationMessage.value = "";
  }

  function toggleMultipleAnswer(key) {
    if (result.value) return;
    if (selectedAnswers.value.includes(key)) {
      selectedAnswers.value = selectedAnswers.value.filter((item) => item !== key);
    } else {
      selectedAnswers.value = [...selectedAnswers.value, key];
    }
    validationMessage.value = "";
  }

  function updateTextAnswer(value) {
    textAnswer.value = value;
    validationMessage.value = "";
  }

  async function submitAnswer() {
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
    } catch (error) {
      errorMessage.value = getErrorMessage(error, "提交答案失败");
    } finally {
      submitting.value = false;
    }
  }

  function handleTextKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!result.value && !submitting.value) {
        submitAnswer();
      }
    }
  }

  function startSession() {
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
