import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";
import StatGrid from "../../components/ui/StatGrid.vue";

const replace = vi.fn();
const logout = vi.fn();
const setMode = vi.fn();
const user = ref<{ id: number; username: string; role: string } | null>({ id: 7, username: "Student", role: "student" });
const stats = ref({ todayCount: 2, totalCount: 42, accuracyRate: 0.75, recentCount7d: 9, wrongCount: 5 });
const streak = ref({ current_streak: 5, longest_streak: 11, last_practiced_date: "2026-07-14" });
const streakAvailable = ref<boolean | null>(true);

vi.mock("vue-router", () => ({ useRouter: () => ({ replace }), useRoute: () => ({ query: {} }) }));
vi.mock("../../stores/auth", () => ({ useAuth: () => ({ user, logout }) }));
vi.mock("../../stores/theme", () => ({ useThemeStore: () => ({ mode: "light", setMode }) }));
vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats,
    streak,
    streakAvailable,
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
    user.value = { id: 7, username: "Student", role: "student" };
    stats.value = { todayCount: 2, totalCount: 42, accuracyRate: 0.75, recentCount7d: 9, wrongCount: 5 };
    streak.value = { current_streak: 5, longest_streak: 11, last_practiced_date: "2026-07-14" };
    streakAvailable.value = true;
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
    expect(wrapper.findComponent(StatGrid).exists()).toBe(true);
    expect(wrapper.findAll(".stat-grid__item")).toHaveLength(4);
    expect(wrapper.get("[data-stat-streak]").text()).toContain("连续打卡");
    expect(wrapper.get("[data-stat-badges]").text()).toContain("徽章");
    expect(wrapper.find(".profile-card--centered").exists()).toBe(true);
    expect(wrapper.text()).toContain("Student");
    expect(wrapper.get("[data-stat-streak]").text()).toContain("5");
    expect(wrapper.get("[data-stat-badges]").text()).toContain("--");
  });

  it("uses the real empty account state without inventing profile data", () => {
    user.value = null;
    const wrapper = mount(Mine);

    expect(wrapper.get(".profile-name").text()).toBe("未登录");
    expect(wrapper.get(".avatar").text()).toBe("未");
    expect(wrapper.get(".profile-tag").text()).toContain("未登录");
    expect(wrapper.get("[data-stat-badges]").text()).toContain("--");
  });

  it("shows an unavailable streak placeholder after only the streak request fails", () => {
    streak.value.current_streak = 88;
    streakAvailable.value = false;
    const wrapper = mount(Mine);

    expect(wrapper.get("[data-stat-streak]").text()).toContain("--");
    expect(wrapper.get("[data-stat-streak]").text()).not.toContain("88");
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
