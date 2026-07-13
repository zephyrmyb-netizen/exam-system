import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { ExamQuestion } from "@/types";
import ExamQuestionCard from "../ExamQuestionCard.vue";

function makeQuestion(type: string): ExamQuestion {
  return {
    id: 11,
    question_id: 9,
    question: "请选择答案",
    question_type: type,
    score: 2,
    order_index: 0,
    options: { A: "选项 A", B: "选项 B", C: "选项 C" },
  };
}

describe("ExamQuestionCard", () => {
  it("toggles normalized sorted answers for a multiple-choice question", async () => {
    const wrapper = mount(ExamQuestionCard, {
      props: { question: makeQuestion("multiple_choice"), answer: "B，A", index: 0, total: 1 },
    });
    const options = wrapper.findAll(".option-button");

    expect(options[0].attributes("aria-pressed")).toBe("true");
    expect(options[1].attributes("aria-pressed")).toBe("true");
    await options[2].trigger("click");
    expect(wrapper.emitted("answer")?.[0]).toEqual(["A,B,C"]);

    await options[0].trigger("click");
    expect(wrapper.emitted("answer")?.[1]).toEqual(["B"]);
  });

  it("keeps single-choice selection replacing the previous answer", async () => {
    const wrapper = mount(ExamQuestionCard, {
      props: { question: makeQuestion("single_choice"), answer: "A", index: 0, total: 1 },
    });
    const options = wrapper.findAll(".option-button");

    expect(options[0].attributes("aria-pressed")).toBe("true");
    expect(options[1].attributes("aria-pressed")).toBe("false");
    await options[1].trigger("click");
    expect(wrapper.emitted("answer")?.[0]).toEqual(["B"]);
  });
});
