import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CourseList from "../CourseList.vue";
import type { Course } from "../../types";
import BottomSheet from "../../components/ui/BottomSheet.vue";
import FilterTabs from "../../components/ui/FilterTabs.vue";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  requestGet: vi.fn(),
  requestPost: vi.fn(),
  requestPatch: vi.fn(),
  requestDelete: vi.fn(),
  confirm: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../api/request", () => ({
  default: { get: mocks.requestGet, post: mocks.requestPost, patch: mocks.requestPatch, delete: mocks.requestDelete },
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
}));

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: mocks.confirm }),
}));

function course(overrides: Partial<Course>): Course {
  return {
    id: 1,
    owner_id: 1,
    name: "Course one",
    description: "",
    subject: "Math",
    visibility: "private",
    created_at: "2026-06-30",
    question_count: 8,
    ...overrides,
  };
}

describe("CourseList UX polish", () => {
  beforeEach(() => {
    mocks.replace.mockClear();
    mocks.requestPost.mockReset();
    mocks.requestPatch.mockReset();
    mocks.requestDelete.mockReset();
    mocks.confirm.mockReset();
    mocks.confirm.mockResolvedValue(false);
    mocks.requestGet.mockResolvedValue({
      data: [course({ id: 1, name: "Course one", question_count: 8 }), course({ id: 2, name: "Empty course", question_count: 0 })],
    });
  });

  it("keeps practice in the course menu and disables it for empty courses", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();

    expect(wrapper.find("[data-reference-page='courses']").exists()).toBe(true);
    expect(wrapper.findComponent(FilterTabs).exists()).toBe(true);
    expect(wrapper.findComponent(FilterTabs).findAll('[role="tab"]')).toHaveLength(4);
    const primaryPracticeActions = wrapper.findAll(".practice-action");
    expect(primaryPracticeActions).toHaveLength(2);
    expect(primaryPracticeActions[0].attributes("aria-label")).toBe("开始练习");
    expect(primaryPracticeActions[1].attributes("disabled")).toBeDefined();

    await wrapper.findAll(".more-btn")[0].trigger("click");
    expect(wrapper.findAll(".course-menu .menu-option")[0].text()).toContain("开始练习");

    await wrapper.findAll(".more-btn")[1].trigger("click");
    expect(wrapper.findAll(".course-menu .menu-option")[0].text()).toContain("暂无题目");
    expect(wrapper.findAll(".course-menu .menu-option")[0].attributes("disabled")).toBeDefined();
  });

  it("keeps management actions compact but accessible", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.findAll(".more-btn")[0].trigger("click");

    const options = wrapper.findAll(".course-menu .menu-option");
    expect(options).toHaveLength(5);
    expect(options[0].text()).toContain("开始练习");
    expect(options[1].text()).not.toBe("");
  });

  it("filters private and public courses without changing the API shape", async () => {
    mocks.requestGet.mockResolvedValue({ data: [course({ id: 1, name: "Private course" }), course({ id: 2, name: "Public course", visibility: "public" })] });
    const wrapper = mount(CourseList);
    await flushPromises();

    const tabs = wrapper.findComponent(FilterTabs).findAll('[role="tab"]');
    expect(tabs[1].text()).toContain("我的");
    await tabs[2].trigger("click");
    expect(wrapper.text()).toContain("Public course");
    expect(wrapper.text()).not.toContain("Private course");
  });

  it("searches course content and filters the recently practised subset", async () => {
    mocks.requestGet.mockResolvedValue({ data: [
      course({ id: 1, name: "线性代数", subject: "数学", last_practiced_at: "2026-07-13" }),
      course({ id: 2, name: "英语阅读", subject: "英语", last_practiced_at: undefined }),
    ] });
    const wrapper = mount(CourseList);
    await flushPromises();

    await wrapper.get('input[type="search"]').setValue("英语");
    expect(wrapper.text()).toContain("英语阅读");
    expect(wrapper.text()).not.toContain("线性代数");

    await wrapper.get('input[type="search"]').setValue("");
    await wrapper.findComponent(FilterTabs).findAll('[role="tab"]')[3].trigger("click");
    expect(wrapper.text()).toContain("线性代数");
    expect(wrapper.text()).not.toContain("英语阅读");
  });

  it("truncates long course names inside the card", async () => {
    const longName = "A course name that must truncate on small screens";
    mocks.requestGet.mockResolvedValue({ data: [course({ name: longName })] });
    const wrapper = mount(CourseList);
    await flushPromises();

    const title = wrapper.find("[data-course-title]");
    expect(title.classes()).toContain("truncate");
    expect(title.attributes("title")).toBe(longName);
  });

  it("opens a practice-mode sheet before entering course practice", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.findAll(".more-btn")[0].trigger("click");
    await wrapper.findAll(".course-menu .menu-option")[0].trigger("click");
    expect(wrapper.findComponent(BottomSheet).exists()).toBe(true);
    expect(wrapper.find(".practice-sheet").exists()).toBe(true);
    expect(wrapper.findAll(".practice-sheet__option")).toHaveLength(4);
    await wrapper.findAll(".practice-sheet__option")[0].trigger("click");

    expect(mocks.replace).toHaveBeenCalledWith({
      name: "course-practice",
      params: { courseId: 1 },
      query: { mode: "sequential", autostart: "1", from: "courses" },
    });

    const expectedTargets = [
      { index: 1, target: { name: "course-practice", params: { courseId: 1 }, query: { mode: "random", autostart: "1", from: "courses" } } },
      { index: 2, target: { name: "course-practice", params: { courseId: 1 }, query: { mode: "wrong", autostart: "1", from: "courses" } } },
      { index: 3, target: { name: "bookmarks", query: { course_id: 1, from: "courses" } } },
    ];
    for (const { index, target } of expectedTargets) {
      await wrapper.findAll(".practice-action")[0].trigger("click");
      await wrapper.findAll(".practice-sheet__option")[index].trigger("click");
      expect(mocks.replace).toHaveBeenLastCalledWith(target);
    }
  });

  it("keeps create, edit, publish and delete management requests intact", async () => {
    mocks.requestPost.mockResolvedValue({ data: course({ id: 3, name: "新题库" }) });
    mocks.requestPatch.mockResolvedValue({ data: course({ id: 1, name: "改名题库" }) });
    mocks.requestDelete.mockResolvedValue({ data: null });
    const wrapper = mount(CourseList);
    await flushPromises();

    await wrapper.get("[data-create-course]").trigger("click");
    await wrapper.get('.modal-card input[placeholder="如：Java 期末复习"]').setValue("新题库");
    await wrapper.findAll(".modal-actions button").at(-1)?.trigger("click");
    await flushPromises();
    expect(mocks.requestPost).toHaveBeenCalledWith("/courses/", expect.objectContaining({ name: "新题库", visibility: "private" }));

    const originalRow = wrapper.findAll(".course-row").find((row) => row.get("[data-course-title]").attributes("title") === "Course one");
    await originalRow?.get(".more-btn").trigger("click");
    await originalRow?.findAll(".course-menu .menu-option")[2].trigger("click");
    await wrapper.get('.modal-card input[placeholder="如：Java 期末复习"]').setValue("改名题库");
    await wrapper.findAll(".modal-actions button").at(-1)?.trigger("click");
    await flushPromises();
    expect(mocks.requestPatch).toHaveBeenCalledWith("/courses/1", expect.objectContaining({ name: "改名题库" }));

    const editedRow = wrapper.findAll(".course-row").find((row) => row.get("[data-course-title]").attributes("title") === "改名题库");
    await editedRow?.get(".more-btn").trigger("click");
    await editedRow?.findAll(".course-menu .menu-option")[3].trigger("click");
    await flushPromises();
    expect(mocks.requestPost).toHaveBeenCalledWith("/courses/1/publish");

    mocks.confirm.mockResolvedValue(true);
    await editedRow?.get(".more-btn").trigger("click");
    await editedRow?.findAll(".course-menu .menu-option")[4].trigger("click");
    await flushPromises();
    expect(mocks.confirm).toHaveBeenCalled();
    expect(mocks.requestDelete).toHaveBeenCalledWith("/courses/1");
  });

  it("keeps the reference compact title bar with an icon-only create action", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();

    const createButton = wrapper.get("[data-create-course]");
    expect(createButton.classes()).toContain("library-create-button");
    expect(createButton.attributes("aria-label")).toContain("创建题库");
  });

  it("enters course detail with replace and a courses source", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.get("[data-course-title]").trigger("click");

    expect(mocks.replace).toHaveBeenCalledWith({ path: "/courses/1", query: { from: "courses" } });
  });

  it("keeps an API error separate from the empty-library state", async () => {
    mocks.requestGet.mockRejectedValue(new Error("network"));
    const wrapper = mount(CourseList);
    await flushPromises();

    expect(wrapper.text()).toContain("获取题库失败");
    expect(wrapper.text()).not.toContain("还没有题库");
  });
});
