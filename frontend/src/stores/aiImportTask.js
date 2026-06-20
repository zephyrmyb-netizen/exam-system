/**
 * Global AI import task state.
 *
 * Module-level refs survive component mount/unmount so the import
 * status is preserved across route changes.  Page refresh naturally
 * clears the state (no persistence).
 */
import { ref } from "vue";
import request, { getErrorMessage } from "../api/request";

// ── Module-level (shared) state ──────────────────────────────────

/** @type {"idle"|"running"|"success"|"error"} */
const status = ref("idle");
const fileName = ref("");
const courseId = ref(0);
const courseName = ref("");
const startedAt = ref(null); // Date.now() timestamp
const elapsedSeconds = ref(0);
const estimatedSeconds = 30;
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

// ── Composable ──────────────────────────────────────────────────

export function useAiImportTask() {
  /**
   * Reset to idle.
   * @param {boolean} [keepFile=false] - Preserve fileName when re-importing after error.
   */
  function reset(keepFile = false) {
    clearElapsedTimer();
    status.value = "idle";
    if (!keepFile) fileName.value = "";
    courseId.value = 0;
    courseName.value = "";
    startedAt.value = null;
    elapsedSeconds.value = 0;
    importedCount.value = 0;
    message.value = "";
    error.value = "";
    resultCourseId.value = null;
    resultCourseName.value = "";
  }

  /**
   * Start an AI import task.
   *
   * Rejects silently when already running (guard against duplicate clicks).
   *
   * @param {File}  file       - The .docx / .pptx file to upload.
   * @param {number} targetCourseId  - 0 = auto-create "未分类题库".
   * @param {string} [targetCourseName] - Display name of the target course.
   */
  async function startImport(file, targetCourseId, targetCourseName) {
    if (status.value === "running") return;

    // Keep fileName across retries only if the same file is re-used
    reset(false);
    status.value = "running";
    fileName.value = file?.name || "";
    courseId.value = targetCourseId;
    courseName.value = targetCourseName || "";
    startedAt.value = Date.now();
    elapsedSeconds.value = 0;
    startElapsedTimer();

    try {
      const formData = new FormData();
      formData.append("file", file);
      const params = {};
      if (targetCourseId > 0) {
        params.course_id = targetCourseId;
      } else if (targetCourseName) {
        // New course — send the name so the backend creates it
        params.course_name = targetCourseName;
      }

      const { data } = await request.post("/imports/file/auto", formData, {
        params,
        timeout: 120000,
      });

      const count = data.imported_count ?? data.count ?? 0;
      importedCount.value = count;
      resultCourseId.value = data.course_id || null;
      resultCourseName.value = data.course_name || "";
      message.value = `AI 识别成功，已导入 ${count} 道题。`;
      if (data.course_name) {
        message.value += ` 已导入到课程「${data.course_name}」。`;
      }
      status.value = "success";
    } catch (err) {
      // 401 is already handled by the axios interceptor (clearToken + userMessage)
      if (err?.response?.status === 401) {
        error.value = "请先登录后使用 AI 导入。";
      } else {
        error.value = getErrorMessage(err, "AI 自动识别并导入失败");
      }
      status.value = "error";
    } finally {
      clearElapsedTimer();
    }
  }

  return {
    // Read-only state
    status,
    fileName,
    courseId,
    courseName,
    startedAt,
    elapsedSeconds,
    estimatedSeconds,
    importedCount,
    message,
    error,
    resultCourseId,
    resultCourseName,
    // Actions
    startImport,
    reset,
  };
}
