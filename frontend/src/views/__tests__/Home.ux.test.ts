import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course } from "../../types";

const replace = vi.fn();
const courses = ref<Course[]>([]);
const loading = ref(false);
const errorMessage = ref("");

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
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
    loading.value = false;
    errorMessage.value = "";
  });

  it("starts with a compact greeting header and the search entry", () => {
    const wrapper = mount(Home);
    const searchEntry = wrapper.get("[data-home-search]");

    expect(wrapper.find(".home-hero").exists()).toBe(true);
    expect(wrapper.find("[data-reference-page='home']").exists()).toBe(true);
    expect(wrapper.text()).toContain("同学");
    expect(wrapper.text()).toContain("从一小步开始");
    expect(searchEntry.classes()).toContain("home-search-entry");
  });

  it("renders four same-size core entries below the compact header", () => {
    const wrapper = mount(Home);

    expect(wrapper.text()).toContain("AI 导入");
    expect(wrapper.text()).toContain("开始练习");
    expect(wrapper.text()).toContain("正式考试");
    expect(wrapper.text()).toContain("学习概览");
    expect(wrapper.findAll(".quick")).toHaveLength(4);
    expect(wrapper.find(".quick-grid").attributes("aria-label")).toBe("快捷操作");
    expect(wrapper.find(".home-hero").exists()).toBe(true);
  });

  it("uses the reference page order: core actions, study overview, recent courses, then a daily recommendation", async () => {
    const wrapper = mount(Home);

    expect(wrapper.find("[data-home-ai-chat]").exists()).toBe(false);
    expect(wrapper.find("[data-home-recommendation]").exists()).toBe(true);
    expect(wrapper.find(".home-recommendation__tag").text()).toContain("每日一练");
    expect(wrapper.findAll(".overview-stat")).toHaveLength(4);
    expect(wrapper.text()).toContain("连续学习");
    expect(wrapper.get("[data-stat-streak]").text()).toContain("--");
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
