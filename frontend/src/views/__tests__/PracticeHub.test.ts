import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { replaceTo, replaceWithSource, getPracticeStats, getTodayReview, getWeakTypes, get } = vi.hoisted(() => ({
  replaceTo: vi.fn(),
  replaceWithSource: vi.fn(),
  getPracticeStats: vi.fn(),
  getTodayReview: vi.fn(),
  getWeakTypes: vi.fn(),
  get: vi.fn(),
}));

vi.mock("../../composables/useAppNavigation", () => ({ useAppNavigation: () => ({ replaceTo, replaceWithSource }) }));
vi.mock("../../api/practice", () => ({ getPracticeStats, getTodayReview, getWeakTypes }));
vi.mock("../../api/request", () => ({ default: { get }, getErrorMessage: () => "request failed" }));

import PracticeHub from "../PracticeHub.vue";

function mountHub() {
  return mount(PracticeHub, {
    global: {
      stubs: {
        PracticeOverviewCard: {
          props: ["title", "description", "hasPrimaryCourse", "todayCount", "totalCount", "wrongCount", "dueCount", "weakTypes", "loading"],
          template: "<div class='overview-stub'><span>{{ title }}</span><span>{{ wrongCount ?? '--' }}</span><button class='primary' @click='$emit(\"primary\")'>primary</button></div>",
        },
        PracticeModeCard: {
          props: ["title", "disabled"],
          template: "<button class='mode-stub' :disabled='disabled' @click='$emit(\"select\")'>{{ title }}</button>",
        },
      },
    },
  });
}

describe("PracticeHub", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPracticeStats.mockResolvedValue({ today_count: 4, total_count: 18, wrong_count: 2 });
    getTodayReview.mockResolvedValue({ due_count: 1, wrong_count: 2 });
    getWeakTypes.mockResolvedValue([]);
    get.mockResolvedValue({ data: [{ id: 7, name: "高等数学", question_count: 12, visibility: "private" }] });
  });

  it("uses real practice stats and keeps direct entry points actionable", async () => {
    const wrapper = mountHub();
    await vi.waitFor(() => expect(get).toHaveBeenCalledWith("/courses/mine"));
    await vi.waitFor(() => expect(wrapper.find(".overview-stub").text()).toContain("2"));

    expect(wrapper.find(".overview-stub").text()).toContain("2");
    await wrapper.get(".primary").trigger("click");
    expect(replaceWithSource).toHaveBeenCalledWith("/courses/7/practice", "practice");
  });

  it("does not turn unavailable wrong-question stats into a fabricated zero", async () => {
    getPracticeStats.mockResolvedValue({ today_count: null, total_count: null, wrong_count: null });
    getTodayReview.mockResolvedValue({ due_count: null, wrong_count: null });

    const wrapper = mountHub();
    await vi.waitFor(() => expect(get).toHaveBeenCalled());

    expect(wrapper.find(".overview-stub").text()).toContain("--");
  });
});
