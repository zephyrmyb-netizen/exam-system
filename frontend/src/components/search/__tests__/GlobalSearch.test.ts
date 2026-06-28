import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import GlobalSearch from "../GlobalSearch.vue";

const push = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/api/courses", () => ({
  getMyCourses: vi.fn(async () => [
    { id: 1, name: "Java 复习题", question_count: 12 },
    { id: 2, name: "Python", question_count: 6 },
  ]),
}));

vi.mock("@/api/questions", () => ({
  getQuestions: vi.fn(async () => ({
    items: [
      { id: 9, course_id: 1, question: "JVM 是什么？" },
    ],
  })),
}));

describe("GlobalSearch", () => {
  it("opens and renders matched courses and questions", async () => {
    const wrapper = mount(GlobalSearch, { attachTo: document.body });

    (wrapper.vm as unknown as { open: () => void }).open();
    await wrapper.vm.$nextTick();

    const input = document.body.querySelector("input") as HTMLInputElement;
    input.value = "Java";
    input.dispatchEvent(new Event("input"));
    await new Promise((resolve) => setTimeout(resolve, 280));
    await wrapper.vm.$nextTick();

    expect(document.body.textContent).toContain("Java 复习题");
    expect(document.body.textContent).toContain("JVM 是什么？");
    wrapper.unmount();
  });
});
