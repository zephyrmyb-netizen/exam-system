import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { replace, get, route } = vi.hoisted(() => ({
  replace: vi.fn(),
  get: vi.fn((url: string) =>
    Promise.resolve(
      url.endsWith("/questions")
        ? {
            data: [
              { id: 1, type: "single_choice", question: "Question 1", options: {}, answer: "A" },
              { id: 2, type: "single_choice", question: "Question 2", options: {}, answer: "A" },
            ],
          }
        : url.startsWith("/wrongbook/")
          ? {
              data: [
                {
                  id: 1,
                  question_id: 1,
                  wrong_count: 1,
                  last_wrong_answer: "B",
                  question: {
                    id: 1,
                    course_id: 7,
                    type: "single_choice",
                    question: "Question",
                    options: {},
                    answer: "A",
                  },
                },
              ],
            }
          : { data: { id: 7, name: "Physics", question_count: 12 } },
    ),
  ),
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
      initialQuestions: { type: Array, default: () => [] },
    },
    template:
      '<div data-test="practice" :data-total="totalQuestions" :data-mode="mode" :data-session-size="initialQuestions.length" />',
  },
}));

import CoursePractice from "../CoursePractice.vue";

describe("CoursePractice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    route.query = {};
    route.fullPath = "/courses/7/practice";
  });

  it("returns direct visits to the single course detail entry", async () => {
    mount(CoursePractice);
    await vi.waitFor(() => expect(replace).toHaveBeenCalled());

    expect(replace).toHaveBeenCalledWith({
      name: "course-detail",
      params: { courseId: "7" },
      query: { from: "courses" },
    });
  });

  it("prepares the complete ordered question set before opening practice", async () => {
    route.query = { autostart: "1" };
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(wrapper.find("[data-test=practice]").exists()).toBe(true));

    const practice = wrapper.get("[data-test=practice]");
    expect(practice.attributes("data-mode")).toBe("normal");
    expect(practice.attributes("data-total")).toBe("2");
    expect(practice.attributes("data-session-size")).toBe("2");
    expect(get).toHaveBeenCalledWith("/courses/7/questions", { params: { order: "asc" } });
  });

  it("uses a complete shuffled session for random practice", async () => {
    route.query = { mode: "random", autostart: "1" };
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(wrapper.find("[data-test=practice]").exists()).toBe(true));

    const practice = wrapper.get("[data-test=practice]");
    expect(practice.attributes("data-mode")).toBe("random");
    expect(practice.attributes("data-session-size")).toBe("2");
  });

  it("loads a course-filtered wrong-answer session", async () => {
    route.query = { mode: "wrong", autostart: "1" };
    const wrapper = mount(CoursePractice);
    await vi.waitFor(() => expect(wrapper.find("[data-test=practice]").exists()).toBe(true));

    const practice = wrapper.get("[data-test=practice]");
    expect(practice.attributes("data-mode")).toBe("wrong_review");
    expect(practice.attributes("data-total")).toBe("1");
  });
});
