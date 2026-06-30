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
});
