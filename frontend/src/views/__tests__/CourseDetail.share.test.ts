import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CourseDetail from "../CourseDetail.vue";

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
const clipboard = vi.hoisted(() => ({ writeText: vi.fn() }));
const route = { params: { courseId: "12" }, query: {} };

vi.mock("vue-router", () => ({ useRoute: () => route }));
vi.mock("../../api/request", () => ({ default: api, getErrorMessage: () => "Request failed" }));
vi.mock("../../composables/useAppNavigation", () => ({
  useAppNavigation: () => ({ replaceWithSource: vi.fn(), returnToSource: vi.fn() }),
}));
vi.mock("../../stores/auth", () => ({ useAuthStore: () => ({ user: { id: 1 } }) }));

describe("CourseDetail sharing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clipboard.writeText.mockResolvedValue(undefined);
    api.post.mockResolvedValue({ data: { token: "private-course-token" } });
    api.get.mockResolvedValue({
      data: {
        id: 12,
        name: "Public course",
        visibility: "public",
        question_count: 2,
        practice_count: 0,
      },
    });
  });

  it("copies the real detail URL for a public course", async () => {
    vi.stubGlobal("navigator", { clipboard });
    const wrapper = mount(CourseDetail, { shallow: true });
    await flushPromises();

    await wrapper.get('[data-testid="course-detail-share"]').trigger("click");
    await flushPromises();

    expect(clipboard.writeText).toHaveBeenCalledWith(expect.stringMatching(/\/courses\/12$/));
    expect(wrapper.find('[role="status"]').exists()).toBe(true);
    vi.unstubAllGlobals();
  });

  it("creates a tokenized link for the owner's private course", async () => {
    api.get.mockResolvedValue({
      data: {
        id: 12,
        owner_id: 1,
        name: "Private course",
        visibility: "private",
        question_count: 2,
        practice_count: 0,
      },
    });
    const wrapper = mount(CourseDetail, { shallow: true });
    await flushPromises();

    vi.stubGlobal("navigator", { clipboard });
    await wrapper.get('[data-testid="course-detail-share"]').trigger("click");
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith("/courses/12/share-link");
    expect(clipboard.writeText).toHaveBeenCalledWith(expect.stringMatching(/\/shared-courses\/private-course-token$/));
    vi.unstubAllGlobals();
  });
});
