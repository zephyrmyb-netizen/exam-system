import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CourseHeader from "../CourseHeader.vue";

describe("CourseHeader", () => {
  it("emits export for an owned course", async () => {
    const wrapper = mount(CourseHeader, {
      props: {
        course: {
          id: 1,
          owner_id: 1,
          name: "Java",
          description: "",
          subject: "Java",
          visibility: "private",
          question_count: 8,
        },
        isOwner: true,
        canStartPractice: true,
      },
    });

    const button = wrapper.findAll("button").find((item) => item.text().includes("导出"));
    expect(button).toBeTruthy();
    await button!.trigger("click");

    expect(wrapper.emitted("export")).toHaveLength(1);
  });
});
