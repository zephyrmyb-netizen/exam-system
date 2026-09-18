import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PracticeAnswerSheet from "../PracticeAnswerSheet.vue";
import type { PracticeSessionQuestion } from "../../../composables/usePracticeSession";

const items: PracticeSessionQuestion[] = [
  {
    question: {
      id: 1,
      owner_id: 1,
      course_id: 1,
      visibility: "private",
      source: "manual",
      created_at: null,
      subject: "Test",
      chapter: "Chapter",
      type: "single_choice",
      question: "First question",
      options: { A: "A", B: "B" },
      answer: "A",
      analysis: "",
      difficulty: "normal",
    },
    sessionOrder: 1,
    answer: "A",
    result: { is_correct: true, correct_answer: "A", analysis: "", wrongbook_recorded: false },
    marked: false,
  },
  {
    question: {
      id: 2,
      owner_id: 1,
      course_id: 1,
      visibility: "private",
      source: "manual",
      created_at: null,
      subject: "Test",
      chapter: "Chapter",
      type: "single_choice",
      question: "Second question",
      options: { A: "A", B: "B" },
      answer: "B",
      analysis: "",
      difficulty: "normal",
    },
    sessionOrder: 2,
    answer: "",
    result: null,
    marked: true,
  },
];

describe("PracticeAnswerSheet", () => {
  it("shows the supplied session questions and jumps immediately after a selection", async () => {
    const wrapper = mount(PracticeAnswerSheet, {
      props: { modelValue: true, items, currentIndex: 1, totalQuestions: 20 },
      attachTo: document.body,
    });

    expect(wrapper.get("[aria-label='答题卡进度']").text()).toContain("已答 1");
    expect(wrapper.findAll("[data-session-question]")).toHaveLength(2);
    expect(wrapper.get("[data-session-question='1']").classes()).toContain("practice-answer-sheet__number--current");

    await wrapper.get("[data-session-question='0']").trigger("click");
    expect(wrapper.emitted("jump")).toEqual([[0]]);
    expect(wrapper.emitted("update:modelValue")).toEqual([[false]]);
    wrapper.unmount();
  });

  it("filters the grid to questions that are still unanswered", async () => {
    const wrapper = mount(PracticeAnswerSheet, {
      props: { modelValue: true, items, currentIndex: 1 },
      attachTo: document.body,
    });

    await wrapper.get(".practice-answer-sheet__filter input").setValue(true);
    expect(wrapper.findAll("[data-session-question]")).toHaveLength(1);
    expect(wrapper.get("[data-session-question='1']").find(".practice-answer-sheet__mark").exists()).toBe(true);
    wrapper.unmount();
  });
});
