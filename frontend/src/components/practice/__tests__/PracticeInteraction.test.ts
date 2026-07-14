import { enableAutoUnmount, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import PracticeActionBar from "../PracticeActionBar.vue";
import PracticeChoiceOptions from "../PracticeChoiceOptions.vue";
import PracticeResultPanel from "../PracticeResultPanel.vue";
import PracticeSummaryModal from "../PracticeSummaryModal.vue";
import PracticeTopBar from "../PracticeTopBar.vue";

enableAutoUnmount(afterEach);

function dispatchKeyboard(key: string, init: KeyboardEventInit = {}) {
  const event = new KeyboardEvent("keydown", {
    key,
    bubbles: true,
    cancelable: true,
    ...init,
  });
  (document.activeElement || document.body).dispatchEvent(event);
  return event;
}

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

  it("omits a denominator and progress track when the mode has no fixed total", () => {
    const wrapper = mount(PracticeTopBar, {
      props: { courseName: "错题强化", answeredCount: 5, totalQuestions: 0 },
    });

    expect(wrapper.find(".practice-topbar__meta").text()).toContain("已答 5");
    expect(wrapper.find(".practice-topbar__meta").text()).not.toContain("/");
    expect(wrapper.find(".practice-topbar__track").exists()).toBe(false);
  });

  it.each(["A,C", "A，C", "A C", "AC", "A/C", '["A","C"]'])(
    "marks every correct multiple-choice key for answer format %s",
    (correctAnswerDisplay) => {
      const wrapper = mount(PracticeChoiceOptions, {
        props: {
          questionType: "multiple_choice",
          options: [
            { key: "A", value: "选项 A" },
            { key: "B", value: "选项 B" },
            { key: "C", value: "选项 C" },
            { key: "D", value: "选项 D" },
          ],
          selectedAnswers: ["A", "B", "C"],
          result: { is_correct: false },
          correctAnswerDisplay,
        },
      });

      const options = wrapper.findAll(".practice-option-card");
      expect(options[0].classes()).toContain("is-correct");
      expect(options[1].classes()).toContain("is-wrong");
      expect(options[2].classes()).toContain("is-correct");
      expect(options[3].classes()).not.toContain("is-correct");
      expect(options[3].classes()).not.toContain("is-wrong");
    },
  );

  it("does not reveal multiple-choice answers before a result exists", () => {
    const wrapper = mount(PracticeChoiceOptions, {
      props: {
        questionType: "multiple_choice",
        options: [
          { key: "A", value: "选项 A" },
          { key: "C", value: "选项 C" },
        ],
        selectedAnswers: ["A"],
        result: null,
        correctAnswerDisplay: "A,C",
      },
    });

    for (const option of wrapper.findAll(".practice-option-card")) {
      expect(option.classes()).not.toContain("is-correct");
      expect(option.classes()).not.toContain("is-wrong");
    }
  });

  it("keeps single-choice and true-false result marking unchanged", () => {
    const single = mount(PracticeChoiceOptions, {
      props: {
        questionType: "single_choice",
        options: [
          { key: "A", value: "选项 A" },
          { key: "B", value: "选项 B" },
          { key: "C", value: "选项 C" },
        ],
        selectedAnswer: "B",
        result: { is_correct: false },
        correctAnswerDisplay: "A",
      },
    });
    const singleOptions = single.findAll(".practice-option-card");
    expect(singleOptions[0].classes()).toContain("is-correct");
    expect(singleOptions[1].classes()).toContain("is-wrong");
    expect(singleOptions[2].classes()).not.toContain("is-wrong");

    const trueFalse = mount(PracticeChoiceOptions, {
      props: {
        questionType: "true_false",
        selectedAnswer: "错误",
        result: { is_correct: false },
        correctAnswerDisplay: "正确",
      },
    });
    const booleanOptions = trueFalse.findAll(".practice-boolean-button");
    expect(booleanOptions[0].classes()).toContain("is-correct");
    expect(booleanOptions[1].classes()).toContain("is-wrong");
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

  it("distinguishes zero values from unavailable summary values", () => {
    const zero = mount(PracticeSummaryModal, {
      props: {
        show: true,
        completed: true,
        answeredCount: 1,
        accuracy: 0,
        durationSeconds: 0,
      },
    });
    expect(zero.get(".practice-summary__ring").text()).toContain("0%");
    expect(zero.get(".practice-summary__duration").text()).toContain("0:00");

    const unavailable = mount(PracticeSummaryModal, {
      props: {
        show: true,
        completed: true,
        answeredCount: 1,
        accuracy: null,
        durationSeconds: null,
      },
    });
    expect(unavailable.get(".practice-summary__ring").text()).toContain("--");
    expect(unavailable.get(".practice-summary__duration").text()).toContain("--");
  });

  it("uses an accessible modal identity and keeps completed sessions open on Escape", async () => {
    const completed = mount(PracticeSummaryModal, {
      attachTo: document.body,
      props: { show: true, completed: true, answeredCount: 2 },
    });
    await nextTick();

    const dialog = completed.get("[role='dialog']");
    expect(dialog.attributes("data-reference-page")).toBe("practice-complete");
    expect(dialog.attributes("aria-modal")).toBe("true");
    expect(dialog.attributes("aria-labelledby")).toBe("practice-summary-title");
    expect(document.activeElement).toBe(completed.get(".practice-primary-button").element);

    const bubbledEscape = vi.fn();
    document.addEventListener("keydown", bubbledEscape);
    const escapeEvent = dispatchKeyboard("Escape");
    expect(completed.emitted("end")).toBeUndefined();
    expect(completed.emitted("continue")).toBeUndefined();
    expect(escapeEvent.defaultPrevented).toBe(true);
    expect(bubbledEscape).not.toHaveBeenCalled();
    completed.unmount();

    const unmountedEscape = dispatchKeyboard("Escape");
    expect(unmountedEscape.defaultPrevented).toBe(false);
    expect(bubbledEscape).toHaveBeenCalledOnce();
    document.removeEventListener("keydown", bubbledEscape);
  });

  it("traps focus, lets an early-exit dialog continue on Escape, and restores focus", async () => {
    const opener = document.createElement("button");
    document.body.appendChild(opener);
    opener.focus();

    const wrapper = mount(PracticeSummaryModal, {
      attachTo: document.body,
      props: { show: false, completed: false, answeredCount: 1, canContinue: true },
    });
    await wrapper.setProps({ show: true });
    await nextTick();

    const buttons = wrapper.findAll("button");
    const first = buttons[0].element as HTMLButtonElement;
    const last = buttons[buttons.length - 1].element as HTMLButtonElement;

    // A script cannot leave focus outside while the modal is visible.
    opener.focus();
    expect(document.activeElement).toBe(first);

    last.focus();
    dispatchKeyboard("Tab");
    expect(document.activeElement).toBe(first);

    first.focus();
    dispatchKeyboard("Tab", { shiftKey: true });
    expect(document.activeElement).toBe(last);

    dispatchKeyboard("Escape");
    expect(wrapper.emitted("continue")).toHaveLength(1);

    await wrapper.setProps({ show: false });
    await nextTick();
    expect(document.activeElement).toBe(opener);

    const hiddenEscape = dispatchKeyboard("Escape");
    expect(hiddenEscape.defaultPrevented).toBe(false);
    expect(wrapper.emitted("continue")).toHaveLength(1);

    wrapper.unmount();
    opener.remove();
  });

  it("keeps the summary scrollable within safe areas down to 320px", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/components/practice/PracticeSummaryModal.vue"),
      "utf8",
    );

    expect(source).toMatch(/max-height:\s*calc\(/);
    expect(source).toMatch(/overflow-y:\s*auto/);
    expect(source).toContain("safe-area-inset-bottom");
    expect(source).toMatch(/@media \(max-width: 360px\)/);
  });
});
