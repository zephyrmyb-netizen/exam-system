import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import BookmarkList from "../BookmarkList.vue";

vi.mock("@/api/bookmark", () => ({
  listBookmarks: vi.fn(async () => ({
    items: [
      {
        id: 1,
        question_id: 9,
        folder_name: "重点",
        note: "复盘",
        created_at: "2026-06-29T00:00:00Z",
        question: {
          id: 9,
          course_id: 3,
          question: "JVM 是什么？",
          type: "short_answer",
        },
      },
    ],
    total: 1,
    folders: ["重点"],
  })),
  removeBookmark: vi.fn(async () => undefined),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("BookmarkList", () => {
  it("renders bookmark items and folder chips", async () => {
    const wrapper = mount(BookmarkList);
    await new Promise((resolve) => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("我的收藏");
    expect(wrapper.text()).toContain("重点");
    expect(wrapper.text()).toContain("JVM 是什么？");
  });
});
