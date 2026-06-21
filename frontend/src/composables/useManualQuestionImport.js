import { ref } from "vue";
import request, { getErrorMessage } from "../api/request";

const DEFAULT_JSON_TEXT = `[
  {
    "subject": "语文",
    "chapter": "古诗词",
    "type": "single_choice",
    "question": "下列诗句中，出自《静夜思》的是哪一句？",
    "options": { "A": "床前明月光", "B": "春眠不觉晓", "C": "白日依山尽", "D": "两个黄鹂鸣翠柳" },
    "answer": "A",
    "analysis": "《静夜思》是李白的诗，首句是床前明月光。",
    "difficulty": "easy"
  }
]`;

function validateQuestionItem(item, index) {
  const errors = [];
  const n = index + 1;
  const validTypes = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"];

  if (!item.question?.trim()) errors.push(`第 ${n} 题：缺少题干`);
  if (!item.type || !validTypes.includes(item.type)) errors.push(`第 ${n} 题：题型无效`);
  if (!item.answer?.trim()) errors.push(`第 ${n} 题：缺少答案`);

  return errors;
}

export function useManualQuestionImport(selectedCourseId) {
  const jsonText = ref(DEFAULT_JSON_TEXT);
  const importLoading = ref(false);
  const importMessage = ref("");
  const importError = ref("");
  const jsonResultCourseId = ref(null);

  async function importQuestions() {
    importLoading.value = true;
    importMessage.value = "";
    importError.value = "";

    try {
      const parsed = JSON.parse(jsonText.value);
      if (!Array.isArray(parsed)) throw new Error("请粘贴 JSON 数组");
      if (parsed.length === 0) throw new Error("JSON 数组为空");

      const allErrors = [];
      parsed.forEach((item, i) => allErrors.push(...validateQuestionItem(item, i)));
      if (allErrors.length > 0) {
        importError.value = `校验未通过：\n${allErrors.join("\n")}`;
        return;
      }

      const { data } = await request.post("/questions/batch", parsed, {
        params: { course_id: selectedCourseId.value > 0 ? selectedCourseId.value : 0 },
      });

      importMessage.value = `导入成功，共 ${data.imported_count || parsed.length} 道题。`;
      jsonResultCourseId.value = data.course_id || null;
    } catch (error) {
      importError.value =
        error instanceof SyntaxError || error.message?.includes("JSON")
          ? `JSON 格式不正确：${error.message}`
          : getErrorMessage(error, "导入失败");
    } finally {
      importLoading.value = false;
    }
  }

  return {
    jsonText,
    importLoading,
    importMessage,
    importError,
    jsonResultCourseId,
    importQuestions,
  };
}
