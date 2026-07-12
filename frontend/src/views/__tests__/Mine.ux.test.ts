import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";

const replace = vi.fn();
const logout = vi.fn();

vi.mock("vue-router", () => ({ useRouter: () => ({ replace }), useRoute: () => ({ query: {} }) }));
vi.mock("../../stores/auth", () => ({ useAuth: () => ({ user: ref({ username: "Student", role: "user" }), logout }) }));
vi.mock("../../stores/theme", () => ({ useThemeStore: () => ({ mode: "light", setMode: vi.fn() }) }));
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

  it("keeps the study overview and service menu available", () => {
    const wrapper = mount(Mine);
    expect(wrapper.find(".stat-link").exists()).toBe(true);
    expect(wrapper.findAll(".menu-item").length).toBeGreaterThan(0);
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
