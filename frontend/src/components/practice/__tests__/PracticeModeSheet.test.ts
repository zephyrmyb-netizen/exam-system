import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PracticeModeSheet from "../PracticeModeSheet.vue";

const course = {
  id: 1,
  owner_id: 1,
  name: "机器学习",
  description: "",
  subject: "",
  visibility: "private" as const,
  created_at: null,
  question_count: 12,
};

describe("PracticeModeSheet", () => {
  it("provides the four shared modes and emits the selected mode", async () => {
    const wrapper = mount(PracticeModeSheet, { props: { modelValue: true, course } });

    expect(wrapper.findAll("[data-practice-mode]")).toHaveLength(4);
    await wrapper.get("[data-practice-mode='random']").trigger("click");
    expect(wrapper.emitted("select")).toEqual([["random"]]);
  });

  it("keeps question-based modes unavailable for an empty course", () => {
    const wrapper = mount(PracticeModeSheet, { props: { modelValue: true, course: { ...course, question_count: 0 } } });

    expect(wrapper.get("[data-practice-mode='sequential']").attributes("disabled")).toBeDefined();
    expect(wrapper.get("[data-practice-mode='random']").attributes("disabled")).toBeDefined();
  });
});
