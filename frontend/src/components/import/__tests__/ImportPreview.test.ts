import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportPreview from "../ImportPreview.vue";

const previewData = {
  suggested_course_name: "图片题库",
  questions: [],
  warnings: ["PPT 中第 3 页图片识别失败", "图片数量超过 12 张，仅处理前 12 张"],
  total_parsed: 0,
  total_valid: 0,
  total_invalid: 0,
  timing: null,
};

function mountPreview(data = previewData) {
  return mount(ImportPreview, {
    props: {
      previewData: data,
    },
    global: {
      stubs: {
        QuestionEditor: true,
      },
    },
  });
}

vi.mock("../../stores/confirmDialog", () => ({
  useConfirmDialog: () => ({ confirm: vi.fn(() => Promise.resolve(true)) }),
}));

describe("ImportPreview warnings and empty state", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders multiple warnings as separate list items", () => {
    const wrapper = mountPreview();

    expect(wrapper.findAll(".warn-line")).toHaveLength(2);
    expect(wrapper.text()).toContain("PPT 中第 3 页图片识别失败");
    expect(wrapper.text()).toContain("图片数量超过 12 张，仅处理前 12 张");
  });

  it("shows actions when no questions are recognized", () => {
    const wrapper = mountPreview();

    expect(wrapper.text()).toContain("未识别到可预览的题目");
    expect(wrapper.text()).toContain("重新解析");
    expect(wrapper.text()).toContain("返回重新选择文件");
    expect(wrapper.text()).toContain("手动新增题目");
  });

  it("disables confirmation when there are no questions to import", () => {
    const wrapper = mountPreview();

    expect(wrapper.get(".primary-button").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("确认导入已禁用");
  });

  it("shows the source file, target course, and skipped fragment count", () => {
    const wrapper = mount(ImportPreview, {
      props: {
        previewData: {
          ...previewData,
          questions: [{ type: "fill_blank", question: "Java 是什么？", answer: "语言" }],
          total_valid: 1,
          total_invalid: 2,
        },
        fileName: "Java复习题.docx",
        initialCourseName: "Java复习题",
      },
      global: {
        stubs: { QuestionEditor: true },
      },
    });

    expect(wrapper.text()).toContain("文件：Java复习题.docx");
    expect(wrapper.text()).toContain("目标题库：Java复习题");
    expect(wrapper.text()).toContain("解析出 1 道题");
    expect(wrapper.text()).toContain("已跳过 2 条无效题目");
    expect(wrapper.text()).toContain("异常提示 2 条");
  });
});
