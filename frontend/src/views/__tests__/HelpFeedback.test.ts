import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HelpFeedback from "../HelpFeedback.vue";

const submitFeedback = vi.hoisted(() => vi.fn());

vi.mock("@/api/feedback", () => ({ submitFeedback }));
vi.mock("@/api/request", () => ({ getErrorMessage: () => "提交失败" }));

describe("HelpFeedback", () => {
  beforeEach(() => {
    submitFeedback
      .mockReset()
      .mockResolvedValue({ id: 23, category: "suggestion", content: "内容", contact: "", created_at: null });
  });

  it("submits persisted feedback and shows its tracking number", async () => {
    const wrapper = mount(HelpFeedback);

    await wrapper.get('[data-testid="feedback-content"]').setValue("希望增加错题筛选功能");
    await wrapper.get('[data-testid="feedback-contact"]').setValue("user@example.com");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(submitFeedback).toHaveBeenCalledWith({
      category: "suggestion",
      content: "希望增加错题筛选功能",
      contact: "user@example.com",
    });
    expect(wrapper.text()).toContain("反馈编号：#23");
  });
});
