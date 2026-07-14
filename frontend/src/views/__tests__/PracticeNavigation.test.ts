import { mount } from "@vue/test-utils";
import { computed, ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Practice from "../Practice.vue";
import PracticeTopBar from "../../components/practice/PracticeTopBar.vue";

const router = {
  push: vi.fn(),
  replace: vi.fn(),
};

vi.mock("vue-router", () => ({
  useRouter: () => router,
}));

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: vi.fn() }),
}));

vi.mock("../../composables/usePracticeSession", () => ({
  usePracticeSession: () => ({
    answerHint: computed(() => "请选择正确或错误"),
    answerOptions: computed(() => []),
    accuracy: computed(() => null),
    canSubmit: computed(() => false),
    correctAnswerDisplay: computed(() => ""),
    currentAnswer: computed(() => ""),
    errorMessage: ref(""),
    fetchRandomQuestion: vi.fn(),
    handleTextKeydown: vi.fn(),
    hasAnswerSelected: computed(() => false),
    isTextQuestion: computed(() => false),
    loading: ref(false),
    question: ref(null),
    result: ref(null),
    selectedAnswer: ref(""),
    selectedAnswers: ref([]),
    sessionComplete: ref(false),
    sessionStats: ref({ answeredCount: 0, correctCount: 0, wrongCount: 0 }),
    setSingleAnswer: vi.fn(),
    startSession: vi.fn(),
    streakText: computed(() => ""),
    submitAnswer: vi.fn(),
    submitting: ref(false),
    textAnswer: ref(""),
    toggleMultipleAnswer: vi.fn(),
    updateTextAnswer: vi.fn(),
    validationMessage: ref(""),
  }),
}));

describe("Practice navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns to the course with router.replace when a course id exists", async () => {
    const wrapper = mount(Practice, {
      props: { courseId: "7", courseName: "高数", mode: "normal" },
    });

    await wrapper.getComponent(PracticeTopBar).vm.$emit("back");

    expect(router.replace).toHaveBeenCalledWith("/courses/7");
    expect(router.push).not.toHaveBeenCalled();
  });

  it("returns review modes to the practice hub with router.replace", async () => {
    const wrapper = mount(Practice, {
      props: { mode: "wrong_review" },
    });

    await wrapper.getComponent(PracticeTopBar).vm.$emit("back");

    expect(router.replace).toHaveBeenCalledWith({ name: "practice" });
    expect(router.push).not.toHaveBeenCalled();
  });
});
