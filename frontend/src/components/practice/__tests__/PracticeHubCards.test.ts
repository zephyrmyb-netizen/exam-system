import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { Library } from "@lucide/vue";

import PracticeModeCard from "../PracticeModeCard.vue";
import PracticeOverviewCard from "../PracticeOverviewCard.vue";

describe("practice hub cards", () => {
  it("renders overview stats without leaking empty zeros", () => {
    const wrapper = mount(PracticeOverviewCard, {
      props: {
        title: "开始一次练习",
        description: "先选择题库，再进入专业练习界面。",
        todayCount: null,
        totalCount: 12,
        wrongCount: 3,
        dueCount: null,
      },
    });

    expect(wrapper.text()).toContain("开始一次练习");
    expect(wrapper.text()).toContain("--");
    expect(wrapper.text()).toContain("12");
    expect(wrapper.text()).toContain("3");
  });

  it("emits select from a mode card", async () => {
    const wrapper = mount(PracticeModeCard, {
      props: {
        icon: Library,
        title: "选择题库练习",
        description: "按题库进入练习设置",
      },
    });

    await wrapper.get("button").trigger("click");

    expect(wrapper.emitted("select")).toHaveLength(1);
  });
});
