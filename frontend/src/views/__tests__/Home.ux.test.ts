import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course, TodayRecommendation } from "../../types";

const replace = vi.fn();
const searchMocks = vi.hoisted(() => ({
  openGlobalSearch: vi.fn(),
}));
const courses = ref<Course[]>([]);
const loading = ref(false);
const errorMessage = ref("");
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

vi.mock("../../api/courses", () => ({
  getMyCourses: () => Promise.resolve(courses.value),
}));

vi.mock("../../utils/globalSearch", () => ({
  openGlobalSearch: searchMocks.openGlobalSearch,
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
    searchMocks.openGlobalSearch.mockClear();
    courses.value = [];
    loading.value = false;
    errorMessage.value = "";
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

  it("keeps the header focused on search without greeting or avatar chrome", () => {
    const wrapper = mount(Home);
    const searchEntry = wrapper.get("[data-home-search]");

    expect(wrapper.find(".home-hero").exists()).toBe(true);
    expect(wrapper.find("[data-reference-page='home']").exists()).toBe(true);
    expect(wrapper.find(".home-hero__top").exists()).toBe(false);
    expect(wrapper.find(".home-hero__avatar").exists()).toBe(false);
    expect(searchEntry.classes()).toContain("home-search-entry");
    expect(searchEntry.text()).toContain("搜索题库、文档、作者");
  });

  it("opens global search from the home search entry instead of routing to courses", async () => {
    const wrapper = mount(Home);

    await wrapper.get("[data-home-search]").trigger("click");

    expect(searchMocks.openGlobalSearch).toHaveBeenCalledTimes(1);
    expect(replace).not.toHaveBeenCalled();
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

  it("keeps the reference content order from shortcuts to recent courses", () => {
    const wrapper = mount(Home);
    const page = wrapper.get("[data-reference-page='home']");
    const children = page.element.children;

    expect(
      wrapper
        .get("[data-testid='home-shortcuts']")
        .element.compareDocumentPosition(wrapper.get("[data-testid='home-recent']").element),
    ).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(
      Array.from(children).some((child) => child.textContent?.includes("学习概览") && child.tagName === "DIV"),
    ).toBe(false);
  });

  it("uses the real recommendation fields in the reference page order", async () => {
    const wrapper = mount(Home);

    expect(wrapper.find("[data-home-ai-chat]").exists()).toBe(false);
    expect(wrapper.find("[data-home-recommendation]").exists()).toBe(true);
    expect(wrapper.find(".home-recommendation__tag").text()).toContain("每日一练");
    expect(wrapper.find("[data-testid='home-stats']").exists()).toBe(false);
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

  it("does not present stale recommendation values when its request fails", () => {
    recommendationAvailable.value = false;
    const wrapper = mount(Home);

    expect(wrapper.get("[data-home-recommendation]").text()).toContain("推荐暂不可用");
    expect(wrapper.get("[data-home-recommendation]").text()).not.toContain("函数");
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

  it("uses the same document icon as the course list for recent courses", async () => {
    courses.value = [course(1, "机器学习")];

    const wrapper = mount(Home);
    await flushPromises();

    const icons = wrapper.findAll("[data-home-course-icon]");
    expect(icons).toHaveLength(1);
    expect(icons[0].find("svg").exists()).toBe(true);
    expect(icons[0].text()).toBe("");
  });

  it("starts practice when a recent course card is clicked", async () => {
    courses.value = [course(1, "很长的移动端复习题库名称")];

    const wrapper = mount(Home);
    await flushPromises();

    const courseCard = wrapper.find('button[aria-label="开始练习：很长的移动端复习题库名称"]');
    expect(courseCard.exists()).toBe(true);
    expect(courseCard.text()).not.toContain("开始练习");

    await courseCard.trigger("click");
    expect(replace).toHaveBeenCalledWith({
      name: "course-practice",
      params: { courseId: 1 },
      query: { from: "home" },
    });
  });

  it("keeps a trailing management button for each recent course", async () => {
    courses.value = [course(1, "机器学习")];

    const wrapper = mount(Home);
    await flushPromises();

    const moreButton = wrapper.get("[data-home-course-more]");
    expect(moreButton.find("svg").exists()).toBe(true);
    expect(moreButton.attributes("aria-label")).toContain("机器学习");

    await moreButton.trigger("click");
    expect(replace).toHaveBeenCalledWith("/courses");
  });
});
