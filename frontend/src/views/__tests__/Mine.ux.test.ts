import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";

const replace = vi.fn();
const logout = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({
    user: ref({ username: "同学", role: "user" }),
    logout,
  }),
}));

vi.mock("../../stores/theme", () => ({
  useThemeStore: () => ({ mode: "light", setMode: vi.fn() }),
}));

vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats: ref({ todayCount: null, totalCount: null, accuracyRate: null, recentCount7d: null, wrongCount: null }),
    loading: ref(false),
    errorMessage: ref(""),
    fetchAll: vi.fn(),
  }),
}));

describe("Mine UX polish", () => {
  beforeEach(() => {
    replace.mockClear();
    logout.mockClear();
  });

  it("does not repeat global course or AI entry points", () => {
    const wrapper = mount(Mine);

    expect(wrapper.text()).not.toContain("题库");
    expect(wrapper.text()).not.toContain("AI 导入");
    expect(wrapper.text()).not.toContain("AI 对话");
    expect(wrapper.text()).toContain("收藏题目");
    expect(wrapper.text()).toContain("设置");
  });

  it("enters study overview with replace and an explicit mine source", async () => {
    const wrapper = mount(Mine);
    const overviewButton = wrapper.findAll("button").find((button) => button.text().includes("学习概览"));

    await overviewButton?.trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "study-overview", query: { from: "mine" } });
  });

  it("logs out and replaces the route with login", async () => {
    const wrapper = mount(Mine);
    const logoutButton = wrapper.findAll("button").at(-1);

    await logoutButton?.trigger("click");

    expect(logout).toHaveBeenCalled();
    expect(replace).toHaveBeenCalledWith({ name: "login" });
  });
});
