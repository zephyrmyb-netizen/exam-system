import type { QuestionType, OptionItem } from "@/types";

export const typeLabels: Record<QuestionType, string> = {
  single_choice: "单选题",
  multiple_choice: "多选题",
  true_false: "判断题",
  fill_blank: "填空题",
  short_answer: "简答题",
};

export const TRUE_FALSE_TRUE = "正确";
export const TRUE_FALSE_FALSE = "错误";

export const TRUE_FALSE_OPTIONS: OptionItem[] = [
  { key: TRUE_FALSE_TRUE, value: TRUE_FALSE_TRUE },
  { key: TRUE_FALSE_FALSE, value: TRUE_FALSE_FALSE },
];

export function typeLabel(type: string): string {
  return typeLabels[type as QuestionType] || type || "未知题型";
}

export function formatOptions(options: unknown): OptionItem[] {
  if (!options) return [];
  if (Array.isArray(options)) {
    return options.map((value, index) => ({
      key: String.fromCharCode(65 + index),
      value: String(value),
    }));
  }
  if (typeof options === "object") {
    return Object.keys(options as Record<string, string>)
      .sort()
      .map((key) => ({ key, value: (options as Record<string, string>)[key] }));
  }
  return [{ key: "选项", value: String(options) }];
}

export function normalizeAnswerDisplay(answer: string): string {
  if (!answer) return "";
  const trimmed = answer.trim();
  if (!trimmed) return "";
  return trimmed;
}

export function isTextQuestionType(type: string): boolean {
  return ["fill_blank", "short_answer"].includes(type);
}

export function getQuestionAnswerHint(type: string): string {
  if (type === "multiple_choice") return "请选择所有正确选项";
  if (type === "single_choice") return "请选择一个选项";
  if (type === "true_false") return "请选择正确或错误";
  if (isTextQuestionType(type)) return "请输入你的答案";
  return "";
}

export function getResultCorrectAnswer(type: string, answer: string): string {
  if (!answer) return "";
  if (type === "true_false") {
    if (answer === "True") return TRUE_FALSE_TRUE;
    if (answer === "False") return TRUE_FALSE_FALSE;
  }
  return normalizeAnswerDisplay(answer);
}

export const typeOptions = (Object.entries(typeLabels) as [string, string][]).map(([value, label]) => ({
  value,
  label,
}));
