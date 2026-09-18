import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SharedCourse from "../SharedCourse.vue";

const api = vi.hoisted(() => ({ getSharedCourse: vi.fn(), copySharedCourse: vi.fn() }));
const router = { replace: vi.fn() };

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { token: "secret-token" } }),
  useRouter: () => router,
}));
vi.mock("../../api/courses", () => api);
vi.mock("../../api/request", () => ({ getErrorMessage: () => "Request failed" }));

describe("SharedCourse", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getSharedCourse.mockResolvedValue({
      name: "Shared private course",
      description: "desc",
      subject: "Math",
      question_count: 3,
    });
    api.copySharedCourse.mockResolvedValue({ id: 42 });
  });

  it("loads the token preview and copies it into the recipient's own course", async () => {
    const wrapper = mount(SharedCourse, { shallow: true });
    await flushPromises();
    await wrapper.get(".shared-course-copy").trigger("click");
    await flushPromises();

    expect(api.getSharedCourse).toHaveBeenCalledWith("secret-token");
    expect(api.copySharedCourse).toHaveBeenCalledWith("secret-token");
    expect(router.replace).toHaveBeenCalledWith({
      name: "course-detail",
      params: { courseId: 42 },
      query: { from: "courses" },
    });
  });
});
