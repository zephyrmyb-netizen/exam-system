import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PracticeActionBar from "../PracticeActionBar.vue";
import PracticeResultPanel from "../PracticeResultPanel.vue";
import PracticeTopBar from "../PracticeTopBar.vue";

describe("practice interaction surfaces", () => {
  it("keeps the top bar focused on the question bank name", () => {
    const wrapper = mount(PracticeTopBar, {
      props: { courseName: "高等数学题库", modeLabel: "章节 · 极限" },
    });

    expect(wrapper.find(".practice-topbar__title").text()).toBe("高等数学题库");
    expect(wrapper.find(".practice-topbar__mode").exists()).toBe(false);
  });

  it("does not reserve a submit bar for single-choice questions", () => {
    const wrapper = mount(PracticeActionBar, {
      props: { showSubmitButton: false },
    });

    expect(wrapper.find(".practice-action-bar").exists()).toBe(false);
  });

  it("shows the swipe hint only after a result is available", () => {
    const wrapper = mount(PracticeResultPanel, {
      props: {
        result: { is_correct: true, analysis: "", wrongbook_recorded: false },
        currentAnswer: "A",
      },
    });

    expect(wrapper.find(".practice-swipe-hint").exists()).toBe(true);
  });
});
