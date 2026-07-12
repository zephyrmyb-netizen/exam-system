import { mount } from "@vue/test-utils";
import { ref } from "vue";
import { describe, expect, it, vi } from "vitest";

import Mine from "../Mine.vue";

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({
    user: ref({ username: "同学", role: "user" }),
    logout: vi.fn(),
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
  it("does not repeat global course or AI entry points", () => {
    const wrapper = mount(Mine);

    expect(wrapper.text()).not.toContain("题库");
    expect(wrapper.text()).not.toContain("AI 导入");
    expect(wrapper.text()).not.toContain("AI 对话");
    expect(wrapper.text()).toContain("收藏题目");
    expect(wrapper.text()).toContain("设置");
  });
});
