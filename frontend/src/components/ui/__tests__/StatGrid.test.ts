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
});
