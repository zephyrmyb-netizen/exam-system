/**
 * 题目相关的共享工具方法
 * 把 Practice.vue、QuestionList.vue、WrongBook.vue 中的重复逻辑提取到这里
 */

export const typeLabels = {
  single_choice: "单选题",
  multiple_choice: "多选题",
  true_false: "判断题",
  fill_blank: "填空题",
  short_answer: "简答题",
};

export const TRUE_FALSE_TRUE = "正确";
export const TRUE_FALSE_FALSE = "错误";

export const TRUE_FALSE_OPTIONS = [
  { key: TRUE_FALSE_TRUE, value: TRUE_FALSE_TRUE },
  { key: TRUE_FALSE_FALSE, value: TRUE_FALSE_FALSE },
];

/** 根据 type 返回中文题型标签 */
export function typeLabel(type) {
  return typeLabels[type] || type || "未知题型";
}

/**
 * 统一格式化题目选项 -> { key, value }[] 数组
 * 支持数组、对象、undefined
 */
export function formatOptions(options) {
  if (!options) return [];
  if (Array.isArray(options)) {
    return options.map((value, index) => ({
      key: String.fromCharCode(65 + index),
      value,
    }));
  }
  if (typeof options === "object") {
    return Object.keys(options)
      .sort()
      .map((key) => ({ key, value: options[key] }));
  }
  return [{ key: "选项", value: options }];
}

/**
 * 将答案显示为友好格式
 * 多选题已排序，单选题直接返回
 */
export function normalizeAnswerDisplay(answer) {
  if (!answer) return "";
  const trimmed = answer.trim();
  if (!trimmed) return "";
  return trimmed;
}

export function isTextQuestionType(type) {
  return ["fill_blank", "short_answer"].includes(type);
}

export function getQuestionAnswerHint(type) {
  if (type === "multiple_choice") return "请选择所有正确选项";
  if (type === "single_choice") return "请选择一个选项";
  if (type === "true_false") return "请选择正确或错误";
  if (isTextQuestionType(type)) return "请输入你的答案";
  return "";
}

export function getResultCorrectAnswer(type, answer) {
  if (!answer) return "";
  if (type === "true_false") {
    if (answer === "True") return TRUE_FALSE_TRUE;
    if (answer === "False") return TRUE_FALSE_FALSE;
  }
  return normalizeAnswerDisplay(answer);
}

/** 用于筛选下拉的题型选项 */
export const typeOptions = Object.entries(typeLabels).map(([value, label]) => ({
  value,
  label,
}));
