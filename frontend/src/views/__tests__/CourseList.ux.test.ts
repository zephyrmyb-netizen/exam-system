import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CourseList from "../CourseList.vue";
import type { Course } from "../../types";

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  requestGet: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: mocks.push }),
}));

vi.mock("../../api/request", () => ({
  default: {
    get: mocks.requestGet,
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
}));

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: vi.fn(() => Promise.resolve(false)) }),
}));

function course(overrides: Partial<Course>): Course {
  return {
    id: 1,
    owner_id: 1,
    name: "线性代数复习题库",
    description: "",
    subject: "数学",
    visibility: "private",
    created_at: "2026-06-30",
    question_count: 8,
    ...overrides,
  };
}

describe("CourseList UX polish", () => {
  beforeEach(() => {
    mocks.push.mockClear();
    mocks.requestGet.mockResolvedValue({
      data: [
        course({ id: 1, name: "线性代数复习题库", question_count: 8 }),
        course({ id: 2, name: "空题库", question_count: 0 }),
      ],
    });
  });

  it("keeps practice as the visible primary action and disables it for empty courses", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();

    const buttons = wrapper.findAll("button");
    expect(buttons.some((button) => button.text().includes("开始练习"))).toBe(true);
    const emptyPractice = buttons.find((button) => button.text().includes("暂无题目"));
    expect(emptyPractice?.attributes("disabled")).toBeDefined();
  });

  it("keeps management actions compact but accessible", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();

    const more = wrapper.find('button[aria-label="更多操作：线性代数复习题库"]');
    expect(more.exists()).toBe(true);
    await more.trigger("click");

    expect(wrapper.find('button[aria-label="编辑线性代数复习题库"]').exists()).toBe(true);
    expect(wrapper.find('button[aria-label="公开线性代数复习题库"]').exists()).toBe(true);
    expect(wrapper.find('button[aria-label="删除线性代数复习题库"]').exists()).toBe(true);
  });

  it("filters private and public courses without changing the API shape", async () => {
    mocks.requestGet.mockResolvedValue({
      data: [
        course({ id: 1, name: "私有题库", visibility: "private" }),
        course({ id: 2, name: "公开题库", visibility: "public" }),
      ],
    });

    const wrapper = mount(CourseList);
    await flushPromises();

    await wrapper.get('button[aria-label="公开题库筛选"]').trigger("click");
    expect(wrapper.text()).toContain("公开题库");
    expect(wrapper.text()).not.toContain("私有题库");
  });

  it("truncates long course names inside the card", async () => {
    mocks.requestGet.mockResolvedValue({
      data: [course({ name: "这是一个在手机端必须截断而不能撑破卡片布局的超长题库名称" })],
    });

    const wrapper = mount(CourseList);
    await flushPromises();

    const title = wrapper.find("[data-course-title]");
    expect(title.classes()).toContain("truncate");
    expect(title.attributes("title")).toBe("这是一个在手机端必须截断而不能撑破卡片布局的超长题库名称");
  });
});
