import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";
import StatGrid from "../../components/ui/StatGrid.vue";

const replace = vi.fn();
const logout = vi.fn();
const clearGuestData = vi.fn();
const setMode = vi.fn();
const user = ref<{ id: number; username: string; role: string; is_guest?: boolean; permissions?: string[] } | null>({
  id: 7,
  username: "Student",
  role: "student",
  permissions: [],
});
const stats = ref({ todayCount: 2, totalCount: 42, accuracyRate: 0.75, recentCount7d: 9, wrongCount: 5 });
const streak = ref({ current_streak: 5, longest_streak: 11, last_practiced_date: "2026-07-14" });
const streakAvailable = ref<boolean | null>(true);
const overviewLoading = ref(false);

vi.mock("vue-router", () => ({ useRouter: () => ({ replace }), useRoute: () => ({ query: {} }) }));
vi.mock("../../stores/auth", () => ({
  useAuth: () => ({
    user,
    logout,
    clearGuestData,
    can: (permission: string) => (user.value?.permissions || []).includes(permission),
  }),
}));
vi.mock("../../stores/theme", () => ({ useThemeStore: () => ({ mode: "light", setMode }) }));
vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats,
    streak,
    streakAvailable,
    loading: overviewLoading,
    errorMessage: ref(""),
    fetchAll: vi.fn(),
  }),
}));

describe("Mine UX polish", () => {
  beforeEach(() => {
    replace.mockClear();
    logout.mockClear();
    clearGuestData.mockReset().mockResolvedValue(true);
    setMode.mockClear();
    user.value = { id: 7, username: "Student", role: "student", permissions: [] };
    stats.value = { todayCount: 2, totalCount: 42, accuracyRate: 0.75, recentCount7d: 9, wrongCount: 5 };
    streak.value = { current_streak: 5, longest_streak: 11, last_practiced_date: "2026-07-14" };
    streakAvailable.value = true;
    overviewLoading.value = false;
  });

  it("keeps existing statistics visible without a loading sentence during a background refresh", () => {
    overviewLoading.value = true;

    const wrapper = mount(Mine);

    expect(wrapper.find(".status-banner--info").exists()).toBe(false);
    expect(wrapper.get("[data-stat-today]").text()).toContain("2");
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
    expect(wrapper.get("[data-stat-today]").text()).toContain("今日练习");
    expect(wrapper.find(".profile-card--centered").exists()).toBe(true);
    expect(wrapper.text()).toContain("Student");
    expect(wrapper.get(".profile-id").text()).toContain("UID: 7");
    expect(wrapper.findAll(".mine-quick")).toHaveLength(4);
    expect(wrapper.get("[data-stat-streak]").text()).toContain("5");
    expect(wrapper.get("[data-stat-today]").text()).toContain("2");
  });

  it("uses the real empty account state without inventing profile data", () => {
    user.value = null;
    const wrapper = mount(Mine);

    expect(wrapper.get(".profile-name").text()).toBe("未登录");
    expect(wrapper.get(".avatar").text()).toBe("未");
    expect(wrapper.get(".profile-id").text()).toContain("UID: --");
    expect(wrapper.get("[data-stat-today]").text()).toContain("2");
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

  it("opens the dedicated help and feedback page instead of announcements", async () => {
    const wrapper = mount(Mine);

    await wrapper.get('[data-testid="mine-help-feedback"]').trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "help-feedback", query: { from: "mine" } });
  });

  it("shows the management entry only to administrators", async () => {
    const studentWrapper = mount(Mine);
    expect(studentWrapper.find('[data-testid="mine-admin-dashboard"]').exists()).toBe(false);

    user.value = { id: 1, username: "Admin", role: "admin", permissions: ["stats:view_global", "user:manage"] };
    const adminWrapper = mount(Mine);
    await adminWrapper.get('[data-testid="mine-admin-dashboard"]').trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "admin-dashboard", query: { from: "mine" } });
  });

  it("keeps the update announcement action separate from help and feedback", async () => {
    const wrapper = mount(Mine);

    await wrapper.get('[data-testid="mine-announcements"]').trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "announcements", query: { from: "mine" } });
  });

  it("logs out and replaces the route with login", async () => {
    const wrapper = mount(Mine);
    await wrapper.findAll("button").at(-1)?.trigger("click");
    expect(logout).toHaveBeenCalled();
    expect(replace).toHaveBeenCalledWith({ name: "login" });
  });

  it("returns a guest to login immediately while their data is being deleted", async () => {
    user.value = { id: 7, username: "Guest", role: "student", is_guest: true };
    clearGuestData.mockImplementationOnce(() => new Promise<boolean>(() => undefined));
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
    const wrapper = mount(Mine);

    await wrapper.findAll(".menu-item").at(-2)?.trigger("click");

    expect(clearGuestData).toHaveBeenCalledOnce();
    expect(replace).toHaveBeenCalledWith({ name: "login" });
    vi.unstubAllGlobals();
  });
});
