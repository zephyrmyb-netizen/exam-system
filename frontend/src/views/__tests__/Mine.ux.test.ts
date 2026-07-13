import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";

const replace = vi.fn();
const logout = vi.fn();
const setMode = vi.fn();

vi.mock("vue-router", () => ({ useRouter: () => ({ replace }), useRoute: () => ({ query: {} }) }));
vi.mock("../../stores/auth", () => ({ useAuth: () => ({ user: ref({ username: "Student", role: "user" }), logout }) }));
vi.mock("../../stores/theme", () => ({ useThemeStore: () => ({ mode: "light", setMode }) }));
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
    setMode.mockClear();
  });

  it("keeps the study overview and service menu available", () => {
    const wrapper = mount(Mine);
    expect(wrapper.find("[data-reference-page='mine']").exists()).toBe(true);
    expect(wrapper.find(".stat-link").exists()).toBe(true);
    expect(wrapper.text()).toContain("错题本");
    expect(wrapper.text()).toContain("练习记录");
    expect(wrapper.text()).toContain("收藏题目");
    expect(wrapper.text()).toContain("更新公告");
    expect(wrapper.text()).toContain("主题");
    expect(wrapper.findAll(".stat-cell")).toHaveLength(4);
    expect(wrapper.get("[data-stat-streak]").text()).toContain("连续打卡");
    expect(wrapper.get("[data-stat-badges]").text()).toContain("徽章");
    expect(wrapper.find(".profile-card--centered").exists()).toBe(true);
    expect(wrapper.get("[data-stat-streak]").text()).toContain("--");
  });

  it("keeps the theme setting usable", async () => {
    const wrapper = mount(Mine);
    await wrapper.get("[data-theme-toggle]").trigger("click");
    expect(setMode).toHaveBeenCalledWith("dark");
  });

  it("enters study overview with replace and an explicit mine source", async () => {
    const wrapper = mount(Mine);
    await wrapper.get(".stat-link").trigger("click");
    expect(replace).toHaveBeenCalledWith({ name: "study-overview", query: { from: "mine" } });
  });

  it("logs out and replaces the route with login", async () => {
    const wrapper = mount(Mine);
    await wrapper.findAll("button").at(-1)?.trigger("click");
    expect(logout).toHaveBeenCalled();
    expect(replace).toHaveBeenCalledWith({ name: "login" });
  });
});
