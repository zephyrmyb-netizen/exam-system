import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import Chat from "../Chat.vue";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  sendChatMessage: vi.fn(),
  streamChatMessage: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace: mocks.replace }),
}));

vi.mock("../../api/chat", () => ({
  sendChatMessage: mocks.sendChatMessage,
  streamChatMessage: mocks.streamChatMessage,
}));

vi.mock("../../stores/theme", () => ({
  useThemeStore: () => ({ mode: "light", toggle: vi.fn() }),
}));

describe("Chat UX polish", () => {
  it("keeps markdown rendered and exposes retry after request failure", async () => {
    mocks.streamChatMessage.mockImplementationOnce((_content: string, _history: unknown, callbacks: { onError: (message: string) => void }) => {
      callbacks.onError("网络错误");
      return { abort: vi.fn() };
    });
    mocks.sendChatMessage.mockRejectedValueOnce(new Error("服务不可用"));

    const wrapper = mount(Chat);
    const input = wrapper.get("textarea");
    await input.setValue("解释这道题");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("AI 回复失败，请稍后重试");
    expect(wrapper.text()).toContain("重试");
    expect(wrapper.text()).not.toContain("**");
  });

  it("uses replace for the chat back action", async () => {
    const wrapper = mount(Chat);
    await wrapper.get('button[aria-label="返回"]').trigger("click");

    expect(mocks.replace).toHaveBeenCalledWith({ name: "home" });
  });
});
