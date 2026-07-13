import { mount } from "@vue/test-utils";
import { computed, reactive, ref } from "vue";
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

const offlineIsOnline = ref(true);
const offlinePendingCount = ref(0);
vi.mock("../../composables/useOfflineSync", () => ({
  useOfflineSync: () => ({
    isOnline: computed(() => offlineIsOnline.value),
    pendingCount: offlinePendingCount,
    refreshPendingCount: vi.fn(),
  }),
}));

vi.mock("../../api/practice", () => ({ flushPendingPracticeSubmissions: vi.fn() }));

describe("AppLayout immersive routes", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    route.name = "home";
    route.path = "/";
    route.fullPath = "/";
    route.params = {};
    route.query = {};
    route.meta = { navKey: "home" };
    offlineIsOnline.value = true;
    offlinePendingCount.value = 0;
    vi.clearAllMocks();
  });

  it("keeps the course tab focused on its page content with bottom navigation", () => {
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
    expect(wrapper.find(".app-header").exists()).toBe(false);
    expect(wrapper.find(".bottom-nav").exists()).toBe(true);
  });

  it("renders the four learning tabs in order and replaces the current route", async () => {
    route.name = "home";
    route.path = "/";
    route.meta = { navKey: "home" };

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    expect(wrapper.findAll(".nav-label").map((item) => item.text())).toEqual(["首页", "题库", "导入", "我的"]);
    await wrapper.findAll(".nav-button")[1].trigger("click");

    expect(router.replace).toHaveBeenCalledWith({ path: "/courses" });
    expect(router.push).not.toHaveBeenCalled();
  });

  it("does not navigate when the current tab is clicked again", async () => {
    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    await wrapper.findAll(".nav-button")[0].trigger("click");

    expect(router.replace).not.toHaveBeenCalled();
    expect(router.push).not.toHaveBeenCalled();
  });

  it("returns a source-aware detail page with replace", async () => {
    route.name = "study-overview";
    route.path = "/study-overview";
    route.query = { from: "home" };
    route.meta = { title: "学习概览", navKey: "mine", parent: "mine" };

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    await wrapper.find(".layout-back-button").trigger("click");

    expect(router.replace).toHaveBeenCalledWith({ name: "home" });
    expect(router.push).not.toHaveBeenCalled();
  });

  it("returns a source-aware page back to mine", async () => {
    route.name = "study-overview";
    route.path = "/study-overview";
    route.query = { from: "mine" };
    route.meta = { title: "学习概览", navKey: "mine", parent: "mine" };

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    await wrapper.find(".layout-back-button").trigger("click");

    expect(router.replace).toHaveBeenCalledWith({ name: "mine" });
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

  it("hides the bottom navigation while an editable field is focused", async () => {
    route.name = "chat";
    route.path = "/chat";
    route.meta = { title: "AI 对话练习", navKey: "ai", parent: "home" };

    const wrapper = mount(AppLayout, {
      attachTo: document.body,
      global: {
        stubs: {
          RouterView: { template: "<textarea class='chat-input'></textarea>" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    expect(wrapper.find(".bottom-nav").exists()).toBe(true);

    await wrapper.find(".chat-input").trigger("focusin");

    expect(wrapper.find(".bottom-nav").exists()).toBe(false);
    wrapper.unmount();
  });

  it("shows an offline sync status when practice records are waiting", () => {
    offlineIsOnline.value = true;
    offlinePendingCount.value = 2;

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: { template: "<div />" },
          ConfirmDialog: true,
          GlobalSearch: true,
        },
      },
    });

    expect(wrapper.find(".offline-sync-banner").text()).toContain("2 条练习记录待同步");
  });
});
