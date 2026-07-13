import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FilterTabs from "../FilterTabs.vue";
import Button from "../button/Button.vue";

describe("FilterTabs", () => {
  const items = [
    { value: "all", label: "全部" },
    { value: "private", label: "私有" },
    { value: "published", label: "已发布", disabled: true },
  ];

  it("renders an accessible single-select tab list", () => {
    const wrapper = mount(FilterTabs, { props: { modelValue: "all", items, label: "题库筛选" } });

    expect(wrapper.get('[role="tablist"]').attributes("aria-label")).toBe("题库筛选");
    const tabs = wrapper.findAll('[role="tab"]');
    expect(tabs).toHaveLength(3);
    expect(tabs[0].attributes("aria-selected")).toBe("true");
    expect(tabs[1].attributes("aria-selected")).toBe("false");
    expect(tabs[2].attributes("disabled")).toBeDefined();
    expect(tabs.map((tab) => tab.attributes("tabindex"))).toEqual(["0", "-1", "-1"]);
    expect(wrapper.findAllComponents(Button)).toHaveLength(3);
  });

  it("emits the selected value without re-emitting the active or disabled tab", async () => {
    const wrapper = mount(FilterTabs, { props: { modelValue: "all", items } });
    const tabs = wrapper.findAll('[role="tab"]');

    await tabs[0].trigger("click");
    await tabs[2].trigger("click");
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();

    await tabs[1].trigger("click");
    expect(wrapper.emitted("update:modelValue")).toEqual([["private"]]);
    expect(wrapper.emitted("change")).toEqual([["private"]]);
  });

  it("moves focus and selection with arrow keys while skipping disabled tabs", async () => {
    const wrapper = mount(FilterTabs, {
      props: { modelValue: "all", items },
      attachTo: document.body,
    });
    const tabs = wrapper.findAll<HTMLButtonElement>('[role="tab"]');
    tabs[0].element.focus();

    await tabs[0].trigger("keydown", { key: "ArrowLeft" });
    expect(document.activeElement).toBe(tabs[1].element);
    expect(wrapper.emitted("update:modelValue")).toEqual([["private"]]);

    await wrapper.setProps({ modelValue: "private" });
    await tabs[1].trigger("keydown", { key: "ArrowRight" });
    expect(document.activeElement).toBe(tabs[0].element);
    expect(wrapper.emitted("update:modelValue")).toEqual([["private"], ["all"]]);
    wrapper.unmount();
  });

  it("uses the first enabled item when modelValue is disabled or missing", async () => {
    const wrapper = mount(FilterTabs, { props: { modelValue: "published", items } });
    let tabs = wrapper.findAll('[role="tab"]');

    expect(tabs.map((tab) => tab.classes().includes("filter-tabs__tab--active"))).toEqual([true, false, false]);
    expect(tabs.map((tab) => tab.attributes("aria-selected"))).toEqual(["true", "false", "false"]);
    expect(tabs.map((tab) => tab.attributes("tabindex"))).toEqual(["0", "-1", "-1"]);

    await wrapper.setProps({ modelValue: "missing" });
    tabs = wrapper.findAll('[role="tab"]');
    expect(tabs.map((tab) => tab.classes().includes("filter-tabs__tab--active"))).toEqual([true, false, false]);
    expect(tabs.map((tab) => tab.attributes("aria-selected"))).toEqual(["true", "false", "false"]);
    expect(tabs.map((tab) => tab.attributes("tabindex"))).toEqual(["0", "-1", "-1"]);
  });

  it("keeps an empty string value active when it belongs to an enabled item", () => {
    const wrapper = mount(FilterTabs, {
      props: {
        modelValue: "",
        items: [
          { value: "all", label: "全部" },
          { value: "", label: "未分类" },
          { value: "disabled", label: "停用", disabled: true },
        ],
      },
    });
    const tabs = wrapper.findAll('[role="tab"]');

    expect(tabs.map((tab) => tab.classes().includes("filter-tabs__tab--active"))).toEqual([false, true, false]);
    expect(tabs.map((tab) => tab.attributes("aria-selected"))).toEqual(["false", "true", "false"]);
    expect(tabs.map((tab) => tab.attributes("tabindex"))).toEqual(["-1", "0", "-1"]);
  });
});
