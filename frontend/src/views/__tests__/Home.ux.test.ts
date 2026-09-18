import { mount, flushPromises } from "@vue/test-utils";
import { nextTick, ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course } from "../../types";
import { resetMyCoursesCache } from "../../composables/useMyCourses";

const replace = vi.fn();
const searchMocks = vi.hoisted(() => ({
  openGlobalSearch: vi.fn(),
}));
const courseActionMocks = vi.hoisted(() => ({
  confirm: vi.fn(),
}));
const courseApiMocks = vi.hoisted(() => ({
  getMyCourses: vi.fn(),
  publishCourse: vi.fn(),
  unpublishCourse: vi.fn(),
  createCourseShareLink: vi.fn(),
  deleteCourse: vi.fn(),
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

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats,
    streak,
    streakAvailable,
    loading,
    errorMessage,
    fetchAll: vi.fn(),
  }),
}));

vi.mock("../../api/courses", () => courseApiMocks);

vi.mock("../../api/request", () => ({
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
  getToken: () => "home-test-token",
}));

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: courseActionMocks.confirm }),
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
    courseActionMocks.confirm.mockReset();
    courseActionMocks.confirm.mockResolvedValue(false);
    courseApiMocks.publishCourse.mockReset();
    courseApiMocks.unpublishCourse.mockReset();
    courseApiMocks.createCourseShareLink.mockReset();
    courseApiMocks.deleteCourse.mockReset();
    resetMyCoursesCache();
    courses.value = [];
    courseApiMocks.getMyCourses.mockReset().mockImplementation(() => Promise.resolve(courses.value));
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
    expect(wrapper.text()).toContain("学习小组");
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
      Array.from(children).some((child) => child.textContent?.includes("学习小组") && child.tagName === "DIV"),
    ).toBe(false);
    expect(wrapper.find("[data-home-recommendation]").exists()).toBe(false);
  });

  it("enters study groups with replace and an explicit home source", async () => {
    const wrapper = mount(Home);
    const overviewButton = wrapper.findAll("button").find((button) => button.text().includes("学习小组"));

    await overviewButton?.trigger("click");

    expect(replace).toHaveBeenCalledWith({ name: "study-groups", query: { from: "home" } });
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

  it("does not show a loading sentence while the recent-course request is pending", async () => {
    courseApiMocks.getMyCourses.mockReturnValue(new Promise(() => undefined));

    const wrapper = mount(Home);
    await nextTick();

    expect(wrapper.find(".status-banner--info").exists()).toBe(false);
    expect(wrapper.find(".course-loading-skeleton").exists()).toBe(true);
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

  it("opens the same course detail page from a recent course card", async () => {
    courses.value = [course(1, "很长的移动端复习题库名称")];

    const wrapper = mount(Home);
    await flushPromises();

    const courseCard = wrapper.find('button[aria-label="查看题库：很长的移动端复习题库名称"]');
    expect(courseCard.exists()).toBe(true);
    expect(courseCard.text()).not.toContain("开始练习");

    await courseCard.trigger("click");
    expect(replace).toHaveBeenCalledWith({
      name: "course-detail",
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
    expect(replace).not.toHaveBeenCalled();
    expect(wrapper.findAll(".home-course-menu .home-menu-option")).toHaveLength(5);
    expect(wrapper.find(".home-course-list").classes()).toContain("home-course-list--menu-open");
  });
});
