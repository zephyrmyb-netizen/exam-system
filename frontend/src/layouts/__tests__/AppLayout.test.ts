import { mount } from "@vue/test-utils";
import { reactive } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import AppLayout from "../AppLayout.vue";

const route = reactive({
  name: "home" as string,
  path: "/",
  fullPath: "/",
  params: {},
  query: {},
  meta: { navKey: "home" } as Record<string, unknown>,
});

const router = {
  push: vi.fn(),
  replace: vi.fn(),
};

vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => router,
}));

vi.mock("../../api/request", () => ({
  getAuthEventName: () => "auth-change",
  getToken: () => "token",
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({ fetchProfile: vi.fn() }),
}));

vi.mock("../../stores/theme", () => ({
  useThemeStore: () => ({ mode: "light", toggle: vi.fn() }),
}));

describe("AppLayout immersive routes", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    route.name = "home";
    route.path = "/";
    route.fullPath = "/";
    route.params = {};
    route.query = {};
    route.meta = { navKey: "home" };
    vi.clearAllMocks();
  });

  it("keeps normal pages with header and bottom navigation", () => {
    route.name = "courses";
    route.path = "/courses";
    route.meta = { title: "题库", navKey: "list" };

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    expect(wrapper.find(".app-shell").classes()).not.toContain("app-shell--immersive");
    expect(wrapper.find(".app-header").exists()).toBe(true);
    expect(wrapper.find(".bottom-nav").exists()).toBe(true);
  });

  it("hides the shell header and bottom navigation on immersive routes", () => {
    route.name = "course-practice";
    route.path = "/courses/1/practice";
    route.meta = { title: "题库练习", navKey: "list", parent: "course-detail" };

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    expect(wrapper.find(".app-shell").classes()).toContain("app-shell--immersive");
    expect(wrapper.find(".app-header").exists()).toBe(false);
    expect(wrapper.find(".bottom-nav").exists()).toBe(false);
  });
});
