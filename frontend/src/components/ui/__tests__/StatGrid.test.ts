import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import StatGrid from "../StatGrid.vue";
import Card from "../card/Card.vue";

describe("StatGrid", () => {
  it("renders labelled values as a semantic list", () => {
    const wrapper = mount(StatGrid, {
      props: {
        label: "学习统计",
        items: [
          { label: "累计学习", value: 18, detail: "天" },
          { label: "连续学习", value: "7 天", tone: "primary" },
        ],
      },
    });

    expect(wrapper.get('[role="list"]').attributes("aria-label")).toBe("学习统计");
    expect(wrapper.findAll('[role="listitem"]')).toHaveLength(2);
    expect(wrapper.text()).toContain("累计学习");
    expect(wrapper.text()).toContain("18");
    expect(wrapper.text()).toContain("天");
    expect(wrapper.find(".stat-grid__item--primary").exists()).toBe(true);
    expect(wrapper.findAllComponents(Card)).toHaveLength(2);
  });

  it("shows the real empty placeholder for unavailable values", () => {
    const wrapper = mount(StatGrid, {
      props: { items: [{ label: "等级", value: null }] },
    });

    expect(wrapper.get(".stat-grid__value").text()).toBe("--");
  });

  it("places data keys on the exact stat item instead of the whole grid", () => {
    const wrapper = mount(StatGrid, {
      props: {
        items: [
          { label: "连续学习", value: "5天", dataKey: "streak" },
          { label: "徽章", value: null, dataKey: "badges" },
        ],
      },
    });

    expect(wrapper.get("[data-stat-streak]").text()).toContain("连续学习");
    expect(wrapper.get("[data-stat-streak]").text()).not.toContain("徽章");
    expect(wrapper.get("[data-stat-badges]").text()).toContain("徽章");
    expect(wrapper.get("[data-stat-badges]").text()).not.toContain("连续学习");
  });
});
