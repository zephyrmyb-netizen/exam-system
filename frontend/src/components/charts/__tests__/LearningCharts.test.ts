import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ActivityTrendChart from "../ActivityTrendChart.vue";
import TagMasteryChart from "../TagMasteryChart.vue";
import TypeAccuracyChart from "../TypeAccuracyChart.vue";

describe("phase4 learning charts", () => {
  it("renders daily activity data points", () => {
    const wrapper = mount(ActivityTrendChart, {
      props: {
        items: [
          { date: "2026-06-28", count: 2 },
          { date: "2026-06-29", count: 5 },
        ],
      },
    });

    expect(wrapper.text()).toContain("06-29");
    expect(wrapper.text()).toContain("5");
    expect(wrapper.findAll("[data-test='activity-bar']")).toHaveLength(2);
  });

  it("renders type accuracy rows", () => {
    const wrapper = mount(TypeAccuracyChart, {
      props: {
        items: [
          { question_type: "single_choice", total_count: 10, correct_count: 8, wrong_count: 2, accuracy_rate: 0.8 },
        ],
      },
    });

    expect(wrapper.text()).toContain("单选题");
    expect(wrapper.text()).toContain("80%");
    expect(wrapper.find("[data-test='type-row']").exists()).toBe(true);
  });

  it("renders tag mastery rows", () => {
    const wrapper = mount(TagMasteryChart, {
      props: {
        items: [
          { tag_id: 1, tag_name: "JVM", total_count: 4, correct_count: 3, accuracy_rate: 0.75 },
        ],
      },
    });

    expect(wrapper.text()).toContain("JVM");
    expect(wrapper.text()).toContain("75%");
    expect(wrapper.find("[data-test='tag-row']").exists()).toBe(true);
  });
});
