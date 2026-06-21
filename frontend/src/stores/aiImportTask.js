import { ref } from "vue";
import { previewFile } from "../api/imports";
import { getErrorMessage } from "../api/request";

const status = ref("idle"); // idle | running | success | error
const mode = ref("preview");
const fileName = ref("");
const courseId = ref(0);
const courseName = ref("");
const startedAt = ref(null);
const elapsedSeconds = ref(0);
const estimatedSeconds = 90;
const previewData = ref(null);
const importedCount = ref(0);
const message = ref("");
const error = ref("");
const resultCourseId = ref(null);
const resultCourseName = ref("");

let elapsedTimer = null;

function clearElapsedTimer() {
  if (elapsedTimer !== null) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

function startElapsedTimer() {
  clearElapsedTimer();
  elapsedTimer = setInterval(() => {
    if (startedAt.value !== null) {
      elapsedSeconds.value = Math.floor((Date.now() - startedAt.value) / 1000);
    }
  }, 1000);
}

function reset() {
  clearElapsedTimer();
  status.value = "idle";
  mode.value = "preview";
  fileName.value = "";
  courseId.value = 0;
  courseName.value = "";
  startedAt.value = null;
  elapsedSeconds.value = 0;
  previewData.value = null;
  importedCount.value = 0;
  message.value = "";
  error.value = "";
  resultCourseId.value = null;
  resultCourseName.value = "";
}

async function startPreview(file, params = {}) {
  if (status.value === "running") return;

  reset();
  status.value = "running";
  mode.value = "preview";
  fileName.value = file?.name || "";
  courseId.value = Number(params.course_id || 0);
  courseName.value = params.course_name || "";
  startedAt.value = Date.now();
  startElapsedTimer();

  try {
    const data = await previewFile(file, params);
    previewData.value = data;
    message.value = `AI 已解析出 ${data?.questions?.length || 0} 道题，请确认后导入。`;
    status.value = "success";
  } catch (err) {
    error.value = getErrorMessage(err, "AI 解析失败，请检查网络后重试");
    status.value = "error";
  } finally {
    clearElapsedTimer();
  }
}

function markImported(result) {
  importedCount.value = result?.imported_count || 0;
  resultCourseId.value = result?.course_id || null;
  resultCourseName.value = result?.course_name || "";
  courseName.value = result?.course_name || courseName.value;
  message.value = `导入成功，已导入 ${importedCount.value} 道题。`;
}

export function useAiImportTask() {
  return {
    status,
    mode,
    fileName,
    courseId,
    courseName,
    startedAt,
    elapsedSeconds,
    estimatedSeconds,
    previewData,
    importedCount,
    message,
    error,
    resultCourseId,
    resultCourseName,
    startPreview,
    markImported,
    reset,
  };
}
