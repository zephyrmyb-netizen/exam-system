import { mount } from "@vue/test-utils";
import { computed, nextTick, ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Practice from "../Practice.vue";

const { replace, sessionFactory } = vi.hoisted(() => ({
  replace: vi.fn(),
  sessionFactory: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
}));

vi.mock("../../composables/useSwipeNext", () => ({
  useSwipeNext: vi.fn(),
}));

vi.mock("../../composables/usePracticeSession", () => ({
  usePracticeSession: (...args: unknown[]) => sessionFactory(...args),
}));

function makeSession(overrides: Record<string, unknown> = {}) {
  const question = ref({
    id: 42,
    type: "single_choice",
    question: "这是一个足够长的真实题干，用来确认练习页不会截断来自接口的长文本内容。".repeat(3),
    subject: "数据库原理",
    chapter: "关系范式",
    difficulty: "hard",
    options: { A: "第一范式", B: "第二范式" },
  });

  return {
    answerHint: computed(() => "请选择一个选项"),
    answerOptions: computed(() => [
      { key: "A", value: "第一范式" },
      { key: "B", value: "第二范式" },
    ]),
    accuracy: computed(() => 50),
    canSubmit: computed(() => false),
    cancelPendingAdvance: vi.fn(),
    correctAnswerDisplay: computed(() => "B"),
    currentAnswer: computed(() => ""),
    errorMessage: ref(""),
    fetchRandomQuestion: vi.fn(),
    handleTextKeydown: vi.fn(),
    hasAnswerSelected: computed(() => false),
    isTextQuestion: computed(() => false),
    loading: ref(false),
    phase: ref("answering"),
    question,
    result: ref(null),
    selectedAnswer: ref(""),
    selectedAnswers: ref([]),
    sessionComplete: ref(false),
    sessionStats: ref({
      answeredCount: 5,
      correctCount: 3,
      wrongCount: 2,
      startedAt: new Date("2026-07-14T10:00:00+08:00"),
      durationSeconds: null,
    }),
    setSingleAnswer: vi.fn(),
    startSession: vi.fn(),
    streakText: computed(() => "2"),
    submitAnswer: vi.fn(),
    submitting: ref(false),
    textAnswer: ref(""),
    toggleMultipleAnswer: vi.fn(),
    updateTextAnswer: vi.fn(),
    validationMessage: ref(""),
    ...overrides,
  };
}

describe("Practice reference migration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionFactory.mockReturnValue(makeSession());
  });

  it("identifies the reference page and renders only real progress and question metadata", () => {
    const wrapper = mount(Practice, {
      props: {
        courseId: "7",
        courseName: "数据库题库",
        totalQuestions: 20,
      },
    });

    expect(wrapper.find("[data-reference-page='course-practice']").exists()).toBe(true);
    expect(wrapper.get(".practice-topbar__meta").text()).toContain("已答 5 / 20");
    expect(wrapper.get(".practice-topbar__track i").attributes("style")).toContain("25%");
    expect(wrapper.get(".practice-stem__title").text()).toContain("不会截断");
    expect(wrapper.get(".practice-stem__context").text()).toContain("数据库原理 · 关系范式");
    expect(wrapper.get(".practice-stem__difficulty").text()).toBe("困难");
    expect(wrapper.text()).not.toContain("2 分");
  });

  it("does not invent a current question number or answer sheet for random practice", () => {
    const wrapper = mount(Practice, {
      props: {
        courseId: "7",
        courseName: "数据库题库",
        totalQuestions: 20,
      },
    });

    expect(wrapper.text()).not.toContain("第 6 题");
    expect(wrapper.find("[aria-label='答题卡']").exists()).toBe(false);
    expect(wrapper.find(".answer-sheet").exists()).toBe(false);
  });

  it("opens the real in-session completion summary and keeps review navigation source-aware", async () => {
    const sessionComplete = ref(false);
    const session = makeSession({
      sessionComplete,
      accuracy: computed(() => 60),
      sessionStats: ref({
        answeredCount: 5,
        correctCount: 3,
        wrongCount: 2,
        startedAt: new Date("2026-07-14T10:00:00+08:00"),
        durationSeconds: 75,
      }),
    });
    sessionFactory.mockReturnValue(session);
    const wrapper = mount(Practice, {
      props: { courseId: "7", courseName: "数据库题库", totalQuestions: 5 },
      attachTo: document.body,
    });

    expect(wrapper.find("[data-reference-page='practice-complete']").exists()).toBe(false);
    sessionComplete.value = true;
    await nextTick();

    expect(wrapper.get("[data-reference-page='practice-complete']").text()).toContain("练习完成！");
    expect(wrapper.get("[data-reference-page='practice-complete']").text()).toContain("60%");
    expect(replace).not.toHaveBeenCalled();

    await wrapper.get(".practice-primary-button").trigger("click");
    expect(replace).toHaveBeenCalledWith({ name: "wrongbook", query: { from: "practice" } });
    wrapper.unmount();
  });

  it("keeps early exit distinct so the learner can continue the same session", async () => {
    const wrapper = mount(Practice, {
      props: { courseId: "7", courseName: "数据库题库", totalQuestions: 20 },
      attachTo: document.body,
    });

    await wrapper.get("[aria-label='结束练习']").trigger("click");
    const dialog = wrapper.get("[data-reference-page='practice-complete']");
    expect(dialog.text()).toContain("结束练习");
    expect(dialog.text()).not.toContain("练习完成！");

    await wrapper.get(".practice-secondary-button").trigger("click");
    expect(wrapper.find("[data-reference-page='practice-complete']").exists()).toBe(false);
    expect(replace).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it("shows a real empty state for an exhausted course without opening a fake completion", async () => {
    const sessionComplete = ref(false);
    const session = makeSession({
      question: ref(null),
      sessionComplete,
      sessionStats: ref({
        answeredCount: 0,
        correctCount: 0,
        wrongCount: 0,
        startedAt: new Date("2026-07-14T10:00:00+08:00"),
        durationSeconds: 0,
      }),
    });
    sessionFactory.mockReturnValue(session);
    const wrapper = mount(Practice, {
      props: { courseId: "7", courseName: "空题库", mode: "normal" },
    });

    expect(wrapper.text()).not.toContain("当前题库暂无题目");
    sessionComplete.value = true;
    await nextTick();
    expect(wrapper.text()).toContain("当前题库暂无题目");
    expect(wrapper.find("[data-reference-page='practice-complete']").exists()).toBe(false);
  });

  it("keeps loading and request failures actionable", async () => {
    sessionFactory.mockReturnValue(makeSession({ question: ref(null), loading: ref(true) }));
    const loading = mount(Practice, { props: { courseId: "7" } });
    expect(loading.find(".practice-skeleton").exists()).toBe(true);

    const fetchRandomQuestion = vi.fn();
    sessionFactory.mockReturnValue(makeSession({
      question: ref(null),
      errorMessage: ref("网络暂时不可用"),
      fetchRandomQuestion,
    }));
    const failed = mount(Practice, { props: { courseId: "7" } });
    expect(failed.text()).toContain("网络暂时不可用");
    await failed.get(".retry-btn").trigger("click");
    expect(fetchRandomQuestion).toHaveBeenCalledTimes(1);
  });
});
