import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SharedCourse from "../SharedCourse.vue";

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
const router = { replace: vi.fn() };

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { token: "secret-token" } }),
  useRouter: () => router,
}));
vi.mock("../../api/request", () => ({ default: api, getErrorMessage: () => "Request failed" }));

describe("SharedCourse", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({
      data: { name: "Shared private course", description: "desc", subject: "Math", question_count: 3 },
    });
    api.post.mockResolvedValue({ data: { id: 42 } });
  });

  it("loads the token preview and copies it into the recipient's own course", async () => {
    const wrapper = mount(SharedCourse, { shallow: true });
    await flushPromises();
    await wrapper.get(".shared-course-copy").trigger("click");
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith("/courses/share/secret-token");
    expect(api.post).toHaveBeenCalledWith("/courses/share/secret-token/copy");
    expect(router.replace).toHaveBeenCalledWith({
      name: "course-detail",
      params: { courseId: 42 },
      query: { from: "courses" },
    });
  });
});
