import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../Home.vue";
import type { Course } from "../../types";

const push = vi.fn();
const courses = ref<Course[]>([]);

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("../../stores/auth", () => ({
  useAuth: () => ({ user: ref({ username: "小明" }) }),
}));

vi.mock("../../composables/useStudyOverview", () => ({
  useStudyOverview: () => ({
    stats: ref({
      todayCount: null,
      totalCount: null,
      correctCount: null,
      wrongCount: null,
      accuracyRate: null,
      recentCount7d: null,
      coursesCount: null,
    }),
    loading: ref(false),
    errorMessage: ref(""),
    fetchAll: vi.fn(),
  }),
}));

vi.mock("../../api/courses", () => ({
  getMyCourses: () => Promise.resolve(courses.value),
}));

function course(id: number, name: string): Course {
  return {
    id,
    owner_id: 1,
    name,
    description: "",
    subject: "公共课",
    visibility: "private",
    created_at: `2026-06-${id.toString().padStart(2, "0")}`,
    question_count: 12,
    last_practiced_at: `2026-06-${id.toString().padStart(2, "0")}`,
  };
}

describe("Home UX polish", () => {
  beforeEach(() => {
    push.mockClear();
    courses.value = [];
  });

  it("renders the four core entry labels with their supporting copy", () => {
    const wrapper = mount(Home);

    expect(wrapper.text()).toContain("AI 导入");
    expect(wrapper.text()).toContain("上传 Word/PPT，自动整理题库");
    expect(wrapper.text()).toContain("开始练习");
    expect(wrapper.text()).toContain("先选题库，再进入专业练习");
    expect(wrapper.text()).toContain("正式考试");
    expect(wrapper.text()).toContain("选择考试并提交成绩");
    expect(wrapper.text()).toContain("学习概览");
    expect(wrapper.text()).toContain("查看今日进度和正确率");
  });

  it("shows at most three recent courses", async () => {
    courses.value = [
      course(1, "题库一"),
      course(2, "题库二"),
      course(3, "题库三"),
      course(4, "题库四"),
    ];

    const wrapper = mount(Home);
    await flushPromises();

    expect(wrapper.text()).toContain("题库四");
    expect(wrapper.text()).toContain("题库三");
    expect(wrapper.text()).toContain("题库二");
    expect(wrapper.text()).not.toContain("题库一");
  });
});
