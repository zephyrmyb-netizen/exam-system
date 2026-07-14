import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { replace, get, route } = vi.hoisted(() => ({
  replace: vi.fn(),
  get: vi.fn().mockResolvedValue({ data: { id: 7, name: "Physics", question_count: 12 } }),
  route: {
    params: { courseId: "7" },
    query: {} as Record<string, string>,
    fullPath: "/courses/7/practice",
  },
}));

vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => ({ replace }),
}));

vi.mock("../../api/request", () => ({
  default: { get },
  getErrorMessage: () => "request failed",
}));

vi.mock("../Practice.vue", () => ({
  default: {
    props: {
      totalQuestions: { type: Number, default: 0 },
      mode: { type: String, default: "normal" },
    },
    template: '<div data-test="practice" :data-total="totalQuestions" :data-mode="mode" />',
  },
}));

import CoursePractice from "../CoursePractice.vue";

describe("CoursePractice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    route.query = {};
    route.fullPath = "/courses/7/practice";
  });

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

  it("passes the real course total to normal random practice", async () => {
    route.query = { autostart: "1" };
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(wrapper.find("[data-test=practice]").exists()).toBe(true));

    const practice = wrapper.get("[data-test=practice]");
    expect(practice.attributes("data-mode")).toBe("normal");
    expect(practice.attributes("data-total")).toBe("12");
  });

  it("does not pass the course total to wrong-review autostart", async () => {
    route.query = { mode: "wrong", autostart: "1" };
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(wrapper.find("[data-test=practice]").exists()).toBe(true));

    const practice = wrapper.get("[data-test=practice]");
    expect(practice.attributes("data-mode")).toBe("wrong_review");
    expect(practice.attributes("data-total")).toBe("0");
  });
});
