import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

const { replace, get } = vi.hoisted(() => ({
  replace: vi.fn(),
  get: vi.fn().mockResolvedValue({ data: { id: 7, name: "Physics", question_count: 12 } }),
}));

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { courseId: "7" } }),
  useRouter: () => ({ replace }),
}));

vi.mock("../../api/request", () => ({
  default: { get },
  getErrorMessage: () => "request failed",
}));

vi.mock("../Practice.vue", () => ({
  default: { template: "<div data-test=practice />" },
}));

import CoursePractice from "../CoursePractice.vue";

describe("CoursePractice", () => {
  it("keeps mode selection as state and starts practice with the selected mode", async () => {
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(get).toHaveBeenCalled());

    const modeButtons = wrapper.findAll(".mode-card");
    await modeButtons[1].trigger("click");

    expect(modeButtons[1].attributes("aria-pressed")).toBe("true");
    expect(modeButtons[1].attributes("style")).toBeUndefined();

    await wrapper.get(".start-btn").trigger("click");
    expect(wrapper.find("[data-test=practice]").exists()).toBe(true);
  });
});
