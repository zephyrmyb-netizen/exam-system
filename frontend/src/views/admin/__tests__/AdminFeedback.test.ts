import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminFeedback from "../AdminFeedback.vue";

const { listAdminFeedback, updateAdminFeedback } = vi.hoisted(() => ({
  listAdminFeedback: vi.fn(),
  updateAdminFeedback: vi.fn(),
}));

vi.mock("@/api/admin", () => ({ listAdminFeedback, updateAdminFeedback }));
vi.mock("@/api/request", () => ({ getErrorMessage: () => "请求失败" }));

describe("AdminFeedback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listAdminFeedback.mockResolvedValue({
      items: [
        {
          id: 8,
          user_id: 3,
          username: "guest_3",
          display_name: "小明",
          category: "bug",
          content: "提交后页面没有提示",
          contact: "",
          status: "new",
          admin_reply: "",
          created_at: "2026-07-17T10:00:00+00:00",
          updated_at: "2026-07-17T10:00:00+00:00",
        },
      ],
      total: 1,
    });
  });

  it("loads feedback and persists a status and reply through the admin API", async () => {
    updateAdminFeedback.mockResolvedValue({
      id: 8,
      user_id: 3,
      username: "guest_3",
      display_name: "小明",
      category: "bug",
      content: "提交后页面没有提示",
      contact: "",
      status: "resolved",
      admin_reply: "已修复，请刷新页面后重试。",
      created_at: "2026-07-17T10:00:00+00:00",
      updated_at: "2026-07-17T10:02:00+00:00",
    });
    const wrapper = mount(AdminFeedback);
    await flushPromises();

    expect(listAdminFeedback).toHaveBeenCalledWith(undefined);
    await wrapper.get('[data-testid="admin-feedback-status-8"]').setValue("resolved");
    await wrapper.get('[data-testid="admin-feedback-reply-8"]').setValue("已修复，请刷新页面后重试。");
    await wrapper.get('[data-testid="admin-feedback-save-8"]').trigger("click");
    await flushPromises();

    expect(updateAdminFeedback).toHaveBeenCalledWith(8, {
      status: "resolved",
      admin_reply: "已修复，请刷新页面后重试。",
    });
    expect(wrapper.text()).toContain("反馈 #8 已保存");
  });
});
