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

const multipleChoicePrefix = /^\s*(?:选\s*项|选|答案|答|选择|option\s*|choice\s*)[：:.\s]*/i;

function extractMultipleChoiceKeys(value: unknown): string[] {
  if (typeof value !== "string") return [];
  const cleaned = value.replace(multipleChoicePrefix, "").trim().toUpperCase();
  if (!cleaned) return [];

  const singleKey = cleaned.match(/^([A-Z])[.)\s]*$/);
  if (singleKey) return [singleKey[1]];
  if (/^[A-Z]+$/.test(cleaned)) return Array.from(cleaned);
  return [];
}

/**
 * Normalize the answer formats accepted by the backend into stable option keys.
 * The result is uppercase, de-duplicated and sorted for direct Set conversion.
 */
export function normalizeMultipleChoiceKeys(answer: unknown): string[] {
  if (Array.isArray(answer)) {
    return Array.from(new Set(answer.flatMap(extractMultipleChoiceKeys))).sort();
  }
  if (typeof answer !== "string") return [];

  const cleaned = answer.replace(multipleChoicePrefix, "").trim();
  if (!cleaned) return [];

  const jsonCandidate = cleaned
    .normalize("NFKC")
    .replace(/[“”]/g, '"')
    .replace(/、/g, ",");
  if (jsonCandidate.startsWith("[")) {
    try {
      const parsed: unknown = JSON.parse(jsonCandidate);
      if (Array.isArray(parsed)) {
        return Array.from(new Set(parsed.flatMap(extractMultipleChoiceKeys))).sort();
      }
    } catch {
      // Fall through to the same separator/compact-letter tolerance as the backend.
    }
  }

  const parts = cleaned.split(/[,，、/;；\s]+/).filter(Boolean);
  const separatedKeys = parts.flatMap(extractMultipleChoiceKeys);
  if (separatedKeys.length > 0) {
    return Array.from(new Set(separatedKeys)).sort();
  }

  const compactKeys = cleaned.toUpperCase().match(/[A-Z]/g) || [];
  return Array.from(new Set(compactKeys)).sort();
}

export function toggleMultipleChoiceKey(answer: unknown, key: string): string {
  const normalizedKey = key.trim().toUpperCase();
  const keys = new Set(normalizeMultipleChoiceKeys(answer));
  if (!/^[A-Z]$/.test(normalizedKey)) return [...keys].sort().join(",");
  if (keys.has(normalizedKey)) keys.delete(normalizedKey);
  else keys.add(normalizedKey);
  return [...keys].sort().join(",");
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
