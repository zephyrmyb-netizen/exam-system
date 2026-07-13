import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { describe, expect, it } from "vitest";

import BottomSheet from "../BottomSheet.vue";
import Button from "../button/Button.vue";
import Card from "../card/Card.vue";

describe("BottomSheet", () => {
  it("exposes a labelled modal dialog and closes from its close button", async () => {
    const wrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "选择练习方式" },
      slots: { default: "<button>顺序练习</button>" },
    });

    const dialog = wrapper.get('[role="dialog"]');
    expect(dialog.attributes("aria-modal")).toBe("true");
    expect(dialog.attributes("aria-labelledby")).toBeTruthy();
    expect(wrapper.get("h2").text()).toBe("选择练习方式");
    expect(wrapper.text()).toContain("顺序练习");
    expect(wrapper.findComponent(Card).exists()).toBe(true);
    expect(wrapper.findComponent(Button).attributes("aria-label")).toBe("关闭选择练习方式");

    await wrapper.get('[aria-label="关闭选择练习方式"]').trigger("click");
    expect(wrapper.emitted("update:modelValue")).toEqual([[false]]);
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("closes when Escape is pressed and ignores backdrop clicks from the panel", async () => {
    const wrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "筛选" },
      attachTo: document.body,
    });

    await wrapper.get(".bottom-sheet__panel").trigger("click");
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(wrapper.emitted("update:modelValue")).toEqual([[false]]);
    wrapper.unmount();
  });

  it("does not close when content has already consumed Escape", async () => {
    const wrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "筛选" },
      slots: { default: "<button class='escape-consumer' @keydown.esc.prevent>编辑条件</button>" },
      attachTo: document.body,
    });
    await nextTick();

    await wrapper.get(".escape-consumer").trigger("keydown", { key: "Escape" });
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    expect(wrapper.emitted("close")).toBeUndefined();
    wrapper.unmount();
  });

  it("moves focus inside, traps Tab in both directions, and restores the opener", async () => {
    const opener = document.createElement("button");
    opener.textContent = "打开筛选";
    document.body.appendChild(opener);
    opener.focus();

    const wrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "筛选" },
      slots: { default: "<button class='sheet-action'>应用筛选</button>" },
      attachTo: document.body,
    });
    await nextTick();

    const dialog = wrapper.get<HTMLElement>('[role="dialog"]');
    const closeButton = wrapper.get<HTMLButtonElement>('[aria-label="关闭筛选"]');
    const actionButton = wrapper.get<HTMLButtonElement>(".sheet-action");
    expect(dialog.element.contains(document.activeElement)).toBe(true);
    expect(document.activeElement).toBe(closeButton.element);

    actionButton.element.focus();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
    expect(document.activeElement).toBe(closeButton.element);

    closeButton.element.focus();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true }));
    expect(document.activeElement).toBe(actionButton.element);

    await closeButton.trigger("click");
    await nextTick();
    expect(dialog.element.contains(document.activeElement)).toBe(true);

    await wrapper.setProps({ modelValue: false });
    await nextTick();
    expect(document.activeElement).toBe(opener);

    wrapper.unmount();
    opener.remove();
  });

  it("restores focus after Escape and remains safe when unmounted while open", async () => {
    const opener = document.createElement("button");
    document.body.appendChild(opener);
    opener.focus();

    const wrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "筛选" },
      attachTo: document.body,
    });
    await nextTick();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await nextTick();
    expect(wrapper.get('[role="dialog"]').element.contains(document.activeElement)).toBe(true);

    await wrapper.setProps({ modelValue: false });
    await nextTick();
    expect(document.activeElement).toBe(opener);

    wrapper.unmount();
    expect(() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab" }))).not.toThrow();
    expect(document.activeElement).toBe(opener);

    opener.focus();
    const openWrapper = mount(BottomSheet, {
      props: { modelValue: true, title: "筛选" },
      attachTo: document.body,
    });
    await nextTick();
    expect(openWrapper.get('[role="dialog"]').element.contains(document.activeElement)).toBe(true);
    openWrapper.unmount();
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });
});
