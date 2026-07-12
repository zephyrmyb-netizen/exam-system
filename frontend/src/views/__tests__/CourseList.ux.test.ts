import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CourseList from "../CourseList.vue";
import type { Course } from "../../types";

const mocks = vi.hoisted(() => ({ replace: vi.fn(), requestGet: vi.fn() }));

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useRoute: () => ({ query: {} }),
}));

vi.mock("../../api/request", () => ({
  default: { get: mocks.requestGet, post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
}));

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: vi.fn(() => Promise.resolve(false)) }),
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
    mocks.requestGet.mockResolvedValue({
      data: [course({ id: 1, name: "Course one", question_count: 8 }), course({ id: 2, name: "Empty course", question_count: 0 })],
    });
  });

  it("keeps practice in the course menu and disables it for empty courses", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();

    await wrapper.findAll(".more-btn")[0].trigger("click");
    expect(wrapper.findAll(".course-menu .menu-option")[0].text()).not.toBe("");

    await wrapper.findAll(".more-btn")[1].trigger("click");
    expect(wrapper.findAll(".course-menu .menu-option")[0].attributes("disabled")).toBeDefined();
  });

  it("keeps management actions compact but accessible", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.findAll(".more-btn")[0].trigger("click");

    const options = wrapper.findAll(".course-menu .menu-option");
    expect(options).toHaveLength(5);
    expect(options[0].text()).not.toBe("");
    expect(options[1].text()).not.toBe("");
  });

  it("filters private and public courses without changing the API shape", async () => {
    mocks.requestGet.mockResolvedValue({ data: [course({ id: 1, name: "Private course" }), course({ id: 2, name: "Public course", visibility: "public" })] });
    const wrapper = mount(CourseList);
    await flushPromises();

    await wrapper.findAll(".seg-item")[2].trigger("click");
    expect(wrapper.text()).toContain("Public course");
    expect(wrapper.text()).not.toContain("Private course");
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

  it("enters course practice with replace and a courses source", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.findAll(".more-btn")[0].trigger("click");
    await wrapper.findAll(".course-menu .menu-option")[0].trigger("click");

    expect(mocks.replace).toHaveBeenCalledWith({ path: "/courses/1/practice", query: { from: "courses" } });
  });

  it("enters course detail with replace and a courses source", async () => {
    const wrapper = mount(CourseList);
    await flushPromises();
    await wrapper.get("[data-course-title]").trigger("click");

    expect(mocks.replace).toHaveBeenCalledWith({ path: "/courses/1", query: { from: "courses" } });
  });
});
