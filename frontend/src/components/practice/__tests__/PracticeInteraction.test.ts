import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PracticeActionBar from "../PracticeActionBar.vue";
import PracticeResultPanel from "../PracticeResultPanel.vue";
import PracticeSummaryModal from "../PracticeSummaryModal.vue";
import PracticeTopBar from "../PracticeTopBar.vue";

describe("practice interaction surfaces", () => {
  it("keeps the top bar focused on the question bank name", () => {
    const wrapper = mount(PracticeTopBar, {
      props: { courseName: "高等数学题库", modeLabel: "章节 · 极限" },
    });

    expect(wrapper.find(".practice-topbar__title").text()).toBe("高等数学题库");
    expect(wrapper.find(".practice-topbar__mode").exists()).toBe(false);
  });

  it("labels random-practice progress as answered questions instead of a fake sequence", () => {
    const wrapper = mount(PracticeTopBar, {
      props: { courseName: "高等数学题库", answeredCount: 5, totalQuestions: 20 },
    });

    expect(wrapper.find(".practice-topbar__meta").text()).toContain("已答 5 / 20");
  });

  it("does not reserve a submit bar for single-choice questions", () => {
    const wrapper = mount(PracticeActionBar, {
      props: { showSubmitButton: false },
    });

    expect(wrapper.find(".practice-action-bar").exists()).toBe(false);
  });

  it("shows the swipe hint after a wrong answer needs manual continuation", () => {
    const wrapper = mount(PracticeResultPanel, {
      props: {
        result: { is_correct: false, analysis: "答案解析", wrongbook_recorded: true },
        currentAnswer: "B",
        correctAnswerDisplay: "A",
      },
    });

    expect(wrapper.find(".practice-swipe-hint").exists()).toBe(true);
  });

  it("announces an answer result without relying on color alone", () => {
    const wrapper = mount(PracticeResultPanel, {
      props: {
        result: { is_correct: false, analysis: "答案解析", wrongbook_recorded: true },
        currentAnswer: "B",
        correctAnswerDisplay: "A",
      },
    });

    const announcement = wrapper.get("[role='status']");
    expect(announcement.attributes("aria-live")).toBe("polite");
    expect(announcement.text()).toContain("答错了");
  });

  it("shows the real session duration and an em dash when duration is unavailable", () => {
    const completed = mount(PracticeSummaryModal, {
      props: {
        show: true,
        completed: true,
        courseName: "高等数学",
        modeLabel: "顺序练习",
        answeredCount: 2,
        correctCount: 1,
        wrongCount: 1,
        accuracy: 50,
        durationSeconds: 65,
      },
    });
    expect(completed.get(".practice-summary__title").text()).toBe("练习完成！");
    expect(completed.get(".practice-summary__subtitle").text()).toContain("高等数学");
    expect(completed.find(".practice-summary__duration").text()).toContain("1:05");
    expect(completed.get(".practice-primary-button").text()).toContain("查看错题详情");
    expect(completed.get(".practice-secondary-button").text()).toContain("返回题库");

    const unavailable = mount(PracticeSummaryModal, {
      props: { show: true, completed: true, answeredCount: 0, durationSeconds: null },
    });
    expect(unavailable.find(".practice-summary__duration").text()).toContain("--");
  });
});
