import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course } from "../../types";

const replace = vi.fn();
const courses = ref<Course[]>([]);
const authUser = ref({ username: "student" });
const loading = ref(false);
const errorMessage = ref("");

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({ user: authUser }),
}));

vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats: ref({
      todayCount: null,
      totalCount: null,
      correctCount: null,
      wrongCount: null,
      accuracyRate: null,
      recentCount7d: null,
      coursesCount: null,
    }),
    loading,
    errorMessage,
    fetchAll: vi.fn(),
  }),
}));

vi.mock("../../api/courses", () => ({
  getMyCourses: () => Promise.resolve(courses.value),
}));

function course(id: number, name: string): Course {
  return {
    id,
    owner_id: 1,
    name,
    description: "",
    subject: "公共课",
    visibility: "private",
    created_at: `2026-06-${id.toString().padStart(2, "0")}`,
    question_count: 12,
    last_practiced_at: `2026-06-${id.toString().padStart(2, "0")}`,
  };
}

describe("Home UX polish", () => {
  beforeEach(() => {
    replace.mockClear();
    courses.value = [];
    authUser.value = { username: "student" };
    loading.value = false;
    errorMessage.value = "";
  });

  it("keeps long greetings contained and the search entry visibly styled", () => {
    authUser.value = { username: "accept_v235_mobile_u3_178361" };

    const wrapper = mount(Home);
    const greeting = wrapper.get("[data-home-greeting]");
    const searchEntry = wrapper.get("[data-home-search]");

    expect(greeting.classes()).toContain("truncate");
    expect(greeting.attributes("title")).toContain("accept_v235_mobile_u3_178361");
    expect(searchEntry.classes()).toContain("home-search-entry");
  });

  it("renders four same-size core entries without decorative copy", () => {
    const wrapper = mount(Home);

    expect(wrapper.text()).toContain("AI 导入");
    expect(wrapper.text()).toContain("开始练习");
    expect(wrapper.text()).toContain("正式考试");
    expect(wrapper.text()).toContain("学习概览");
    expect(wrapper.findAll(".quick")).toHaveLength(4);
    expect(wrapper.find(".hero-banner").exists()).toBe(false);
  });

  it("enters study overview with replace and an explicit home source", async () => {
    const wrapper = mount(Home);
    const overviewButton = wrapper.findAll("button").find((button) => button.text().includes("学习概览"));

    await overviewButton?.trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "study-overview", query: { from: "home" } });
  });

  it("shows at most three recent courses", async () => {
    courses.value = [
      course(1, "题库一"),
      course(2, "题库二"),
      course(3, "题库三"),
      course(4, "题库四"),
    ];

    const wrapper = mount(Home);
    await flushPromises();

    expect(wrapper.text()).toContain("题库四");
    expect(wrapper.text()).toContain("题库三");
    expect(wrapper.text()).toContain("题库二");
    expect(wrapper.text()).not.toContain("题库一");
  });

  it("does not break when stats are loading or failed", () => {
    loading.value = true;
    const loadingWrapper = mount(Home);
    expect(loadingWrapper.text()).toContain("学习数据加载中");

    loading.value = false;
    errorMessage.value = "学习数据暂时不可用";
    const errorWrapper = mount(Home);
    expect(errorWrapper.text()).toContain("学习数据暂时不可用");
    expect(errorWrapper.find(".overview-surface").exists()).toBe(true);
  });

  it("keeps the recent course title separate from its practice action", async () => {
    courses.value = [course(1, "很长的移动端复习题库名称")];

    const wrapper = mount(Home);
    await flushPromises();

    const practiceButton = wrapper.find('button[aria-label="开始练习：很长的移动端复习题库名称"]');
    expect(practiceButton.exists()).toBe(true);
    expect(practiceButton.text()).toBe("开始练习");
  });
});
