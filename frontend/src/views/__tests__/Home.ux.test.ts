import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course, TodayRecommendation } from "../../types";
import StatGrid from "../../components/ui/StatGrid.vue";

const replace = vi.fn();
const courses = ref<Course[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const user = ref({ id: 7, username: "林海同学", role: "student" });
const stats = ref({
  todayCount: 4,
  totalCount: 36,
  correctCount: 30,
  wrongCount: 6,
  accuracyRate: 30 / 36,
  recentCount7d: 18,
  coursesCount: 2,
});
const streak = ref({ current_streak: 7, longest_streak: 12, last_practiced_date: "2026-07-14" });
const streakAvailable = ref<boolean | null>(true);
const recommendationAvailable = ref<boolean | null>(true);
const recommendation = ref<TodayRecommendation | null>({
  weak_tags: [{ tag_id: 1, tag_name: "函数", total_count: 10, correct_count: 4, accuracy_rate: 0.4 }],
  weak_types: [{ question_type: "single_choice", total_attempts: 8, wrong_attempts: 5, error_rate: 0.625 }],
  due_count: 8,
  due_question_ids: [1, 2],
  recommended_modes: ["weak_tag_practice", "weak_type_practice", "spaced_repeat"],
});

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats,
    streak,
    recommendation,
    streakAvailable,
    recommendationAvailable,
    loading,
    errorMessage,
    fetchAll: vi.fn(),
  }),
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({ user }),
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
    user.value = { id: 7, username: "林海同学", role: "student" };
    stats.value = {
      todayCount: 4,
      totalCount: 36,
      correctCount: 30,
      wrongCount: 6,
      accuracyRate: 30 / 36,
      recentCount7d: 18,
      coursesCount: 2,
    };
    streak.value = { current_streak: 7, longest_streak: 12, last_practiced_date: "2026-07-14" };
    streakAvailable.value = true;
    recommendationAvailable.value = true;
    recommendation.value = {
      weak_tags: [{ tag_id: 1, tag_name: "函数", total_count: 10, correct_count: 4, accuracy_rate: 0.4 }],
      weak_types: [{ question_type: "single_choice", total_attempts: 8, wrong_attempts: 5, error_rate: 0.625 }],
      due_count: 8,
      due_question_ids: [1, 2],
      recommended_modes: ["weak_tag_practice", "weak_type_practice", "spaced_repeat"],
    };
  });

  it("starts with a compact greeting header and the search entry", () => {
    const wrapper = mount(Home);
    const searchEntry = wrapper.get("[data-home-search]");

    expect(wrapper.find(".home-hero").exists()).toBe(true);
    expect(wrapper.find("[data-reference-page='home']").exists()).toBe(true);
    expect(wrapper.text()).toContain("林海同学");
    expect(wrapper.get(".home-hero__avatar").text()).toBe("林");
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

  it("uses real streak and recommendation fields in the reference page order", async () => {
    const wrapper = mount(Home);

    expect(wrapper.find("[data-home-ai-chat]").exists()).toBe(false);
    expect(wrapper.find("[data-home-recommendation]").exists()).toBe(true);
    expect(wrapper.find(".home-recommendation__tag").text()).toContain("每日一练");
    expect(wrapper.findComponent(StatGrid).exists()).toBe(true);
    expect(wrapper.findAll(".stat-grid__item")).toHaveLength(4);
    expect(wrapper.text()).toContain("连续学习");
    expect(wrapper.get("[data-stat-streak]").text()).toContain("7");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("函数");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("8 题待复习");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("薄弱标签");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("去题库选择相关内容");

    await wrapper.get("[data-home-recommendation]").trigger("click");
    expect(replace).toHaveBeenCalledWith("/courses");
  });

  it("routes a real spaced-repeat recommendation directly to due practice", async () => {
    recommendation.value = {
      weak_tags: [],
      weak_types: [],
      due_count: 8,
      due_question_ids: [1, 2],
      recommended_modes: ["spaced_repeat"],
    };
    const wrapper = mount(Home);

    expect(wrapper.get("[data-home-recommendation]").text()).toContain("到期复习");
    await wrapper.get("[data-home-recommendation]").trigger("click");
    expect(replace).toHaveBeenCalledWith({ name: "practice-due" });
  });

  it("routes a weak-type recommendation to course selection without inventing a filtered practice", async () => {
    recommendation.value = {
      weak_tags: [],
      weak_types: [{ question_type: "single_choice", total_attempts: 8, wrong_attempts: 5, error_rate: 0.625 }],
      due_count: 0,
      due_question_ids: [],
      recommended_modes: ["weak_type_practice"],
    };
    const wrapper = mount(Home);

    expect(wrapper.get("[data-home-recommendation]").text()).toContain("单选题");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("薄弱题型");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("去题库选择相关内容");
    await wrapper.get("[data-home-recommendation]").trigger("click");
    expect(replace).toHaveBeenCalledWith("/courses");
  });

  it("shows a truthful empty recommendation without copying a sample value", () => {
    recommendation.value = null;
    const wrapper = mount(Home);

    expect(wrapper.get("[data-home-recommendation]").text()).toContain("暂无个性化推荐");
    expect(wrapper.get("[data-home-recommendation]").text()).not.toContain("函数");
  });

  it("does not present stale streak or recommendation values when their requests fail", () => {
    streak.value.current_streak = 99;
    streakAvailable.value = false;
    recommendationAvailable.value = false;
    const wrapper = mount(Home);

    expect(wrapper.get("[data-stat-streak]").text()).toContain("--");
    expect(wrapper.get("[data-stat-streak]").text()).not.toContain("99");
    expect(wrapper.get("[data-home-recommendation]").text()).toContain("推荐暂不可用");
    expect(wrapper.get("[data-home-recommendation]").text()).not.toContain("函数");
  });

  it("keeps a fulfilled zero-day streak as real data", () => {
    streak.value.current_streak = 0;
    streakAvailable.value = true;
    const wrapper = mount(Home);

    expect(wrapper.get("[data-stat-streak]").text()).toContain("0天");
    expect(wrapper.get("[data-stat-streak]").text()).not.toContain("--");
  });

  it("enters study overview with replace and an explicit home source", async () => {
    const wrapper = mount(Home);
    const overviewButton = wrapper.findAll("button").find((button) => button.text().includes("学习概览"));

    await overviewButton?.trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "study-overview", query: { from: "home" } });
  });

  it("shows at most three recent courses", async () => {
    courses.value = [course(1, "题库一"), course(2, "题库二"), course(3, "题库三"), course(4, "题库四")];

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
    stats.value.totalCount = 36;
    const errorWrapper = mount(Home);
    expect(errorWrapper.text()).toContain("学习数据暂时不可用");
    expect(errorWrapper.find(".overview-surface").exists()).toBe(true);
    expect(errorWrapper.find(".overview-surface").text()).toContain("36");
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
