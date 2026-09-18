import { flushPromises, mount } from "@vue/test-utils";
import { reactive } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExamList from "../ExamList.vue";

const router = { replace: vi.fn() };
const store = reactive({
  exams: [
    {
      id: 7,
      title: "普通用户考试",
      description: "",
      question_count: 1,
      total_score: 10,
      time_limit: 30,
      status: "published",
    },
  ],
  myExams: [],
  loading: false,
  error: "",
  fetchExams: vi.fn(),
  fetchMyExams: vi.fn(),
});

vi.mock("vue-router", () => ({ useRoute: () => ({ query: {} }), useRouter: () => router }));
vi.mock("@/stores/exam", () => ({ useExamStore: () => store }));

describe("ExamList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    store.exams = [
      {
        id: 7,
        title: "普通用户考试",
        description: "",
        question_count: 1,
        total_score: 10,
        time_limit: 30,
        status: "published",
      },
    ];
    store.myExams = [];
  });

  it("shows creation to every authenticated visitor and opens an exam through its own button", async () => {
    const wrapper = mount(ExamList);
    await flushPromises();

    expect(store.fetchExams).toHaveBeenCalled();
    expect(store.fetchMyExams).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="exam-list-create"]').exists()).toBe(true);

    await wrapper.get('[data-testid="exam-list-open-7"]').trigger("click");
    expect(router.replace).toHaveBeenCalledWith({ name: "exam-detail", params: { examId: 7 } });
  });
});
