import { type ComputedRef, type Ref } from "vue";
import { defineStore, storeToRefs } from "pinia";

import { AI_IMPORT_FORMAT_ERROR_MESSAGE, createImportTask, getImportTask } from "../api/imports";
import { getErrorMessage } from "../api/request";
import type { ImportPreviewResponse, ImportTaskResponse, ImportTiming } from "../types";
import { getFileExtension } from "../utils/importFiles";

export type TaskStatus = "idle" | "running" | "success" | "error";
export type TaskMode = "preview" | "auto";
export type TaskStage = "idle" | "parsing" | "complete" | "failed";

const TASK_STORAGE_KEY = "xuexibao:active-import-task";
const POLL_INTERVAL_MS = 1500;
const ACTIVE_REMOTE_STATUSES = new Set(["queued", "extracting", "parsing", "importing"]);

export interface AiImportTaskReturn {
  status: Ref<TaskStatus>;
  stage: Ref<TaskStage>;
  mode: Ref<TaskMode>;
  taskId: Ref<string>;
  fileRef: Ref<File | null>;
  fileName: Ref<string>;
  courseId: Ref<number>;
  courseName: Ref<string>;
  startedAt: Ref<number | null>;
  elapsedSeconds: Ref<number>;
  estimatedSeconds: number;
  previewData: Ref<ImportPreviewResponse | null>;
  timing: Ref<ImportTiming | null>;
  importedCount: Ref<number>;
  message: Ref<string>;
  error: Ref<string>;
  resultCourseId: Ref<number | null>;
  resultCourseName: Ref<string>;
  progressTitle: ComputedRef<string>;
  progressDetail: ComputedRef<string>;
  startPreview: (file: File, params?: Record<string, string | number>) => Promise<void>;
  resume: () => Promise<void>;
  markImported: (result: { imported_count?: number; course_id?: number | null; course_name?: string }) => void;
  reset: () => void;
}

let elapsedTimer: ReturnType<typeof setInterval> | null = null;
let pollTimer: ReturnType<typeof setTimeout> | null = null;

function getPreviewErrorMessage(error: unknown): string {
  const requestError = error as { code?: string; response?: { status?: number; data?: { detail?: unknown } } } | undefined;
  if (requestError?.code === "ECONNABORTED" || requestError?.code === "ETIMEDOUT" || requestError?.response?.status === 504) {
    return "文件上传或 AI 解析耗时较长，请在稳定网络下重试；大文件最多可等待 2 分钟。";
  }
  const detail = requestError?.response?.data?.detail;
  if (typeof detail === "string" && /AI 未能解析出题目|非 JSON|未找到 questions 数组|返回格式异常/.test(detail)) {
    return AI_IMPORT_FORMAT_ERROR_MESSAGE;
  }
  return getErrorMessage(error, "AI 解析失败，请检查网络后重试");
}

function formatDuration(ms: number | undefined): string {
  const value = Number(ms || 0);
  return value >= 1000 ? `${Math.round(value / 100) / 10} 秒` : `${value} 毫秒`;
}

function clearElapsedTimer(): void {
  if (elapsedTimer !== null) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

function clearPollTimer(): void {
  if (pollTimer !== null) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function getStoredTaskId(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(TASK_STORAGE_KEY) || "";
}

function storeTaskId(taskId: string): void {
  if (typeof window === "undefined") return;
  if (taskId) window.localStorage.setItem(TASK_STORAGE_KEY, taskId);
  else window.localStorage.removeItem(TASK_STORAGE_KEY);
}

export const useAiImportTaskStore = defineStore("aiImportTask", {
  state: () => ({
    status: "idle" as TaskStatus,
    stage: "idle" as TaskStage,
    mode: "preview" as TaskMode,
    taskId: "",
    fileRef: null as File | null,
    fileName: "",
    courseId: 0,
    courseName: "",
    startedAt: null as number | null,
    elapsedSeconds: 0,
    estimatedSeconds: 90,
    previewData: null as ImportPreviewResponse | null,
    timing: null as ImportTiming | null,
    importedCount: 0,
    message: "",
    error: "",
    resultCourseId: null as number | null,
    resultCourseName: "",
  }),
  getters: {
    progressTitle(state): string {
      if (state.status === "running") {
        const ext = getFileExtension(state.fileName);
        if (ext === ".pptx") return state.elapsedSeconds < 3 ? "正在读取 PPT 页内容" : "AI 正在识别 PPT 中的题目";
        if (ext === ".pdf") return state.elapsedSeconds < 3 ? "正在读取 PDF 页面文字" : "AI 正在解析 PDF 题目";
        if ([".png", ".jpg", ".jpeg", ".webp"].includes(ext)) return "正在识别图片中的题目";
        return state.elapsedSeconds < 3 ? "正在提取文档文字" : "AI 正在解析题目，请稍等";
      }
      if (state.status === "success") return "AI 解析完成";
      if (state.status === "error") return "AI 解析失败";
      return "AI 导入";
    },
    progressDetail(state): string {
      if (state.status === "running") {
        if (state.taskId) return "解析任务已保存，切换页面或刷新后可以继续查看进度。";
        return "正在让 AI 整理题目，文档较长时可能需要 30-120 秒。";
      }
      if (state.status === "success" && state.timing) {
        return `本次用时 ${formatDuration(state.timing.total_ms)}，其中 AI 生成 ${formatDuration(state.timing.ai_ms)}。`;
      }
      return "";
    },
  },
  actions: {
    startElapsedTimer(): void {
      clearElapsedTimer();
      elapsedTimer = setInterval(() => {
        if (this.startedAt !== null) this.elapsedSeconds = Math.floor((Date.now() - this.startedAt) / 1000);
      }, 1000);
    },

    applyRemoteTask(task: ImportTaskResponse): void {
      this.taskId = task.id;
      this.fileName = task.source_filename;
      this.courseId = task.course_id || 0;
      this.courseName = task.course_name || task.suggested_course_name || "";
      this.timing = task.timing;

      if (task.status === "ready" || task.status === "imported") {
        this.previewData = {
          questions: task.questions,
          suggested_course_name: task.suggested_course_name,
          warnings: task.warnings,
          total_parsed: task.total_valid + task.total_invalid,
          total_valid: task.total_valid,
          total_invalid: task.total_invalid,
          timing: task.timing,
        };
        this.status = "success";
        this.stage = "complete";
        this.message = task.status === "imported"
          ? `导入成功，已导入 ${task.total_valid} 道题。`
          : `AI 已解析出 ${task.total_valid} 道题，请确认后导入。`;
        clearElapsedTimer();
        return;
      }

      if (task.status === "failed") {
        this.status = "error";
        this.stage = "failed";
        this.error = task.error_message || "AI 解析失败，请稍后重试。";
        clearElapsedTimer();
        return;
      }

      this.status = "running";
      this.stage = "parsing";
      if (this.startedAt === null && task.started_at) this.startedAt = Date.parse(task.started_at);
      this.startElapsedTimer();
    },

    schedulePoll(): void {
      clearPollTimer();
      if (!this.taskId || this.status !== "running") return;
      pollTimer = setTimeout(() => void this.refreshTask(), POLL_INTERVAL_MS);
    },

    async refreshTask(): Promise<void> {
      if (!this.taskId) return;
      try {
        const task = await getImportTask(this.taskId);
        this.applyRemoteTask(task);
        if (ACTIVE_REMOTE_STATUSES.has(task.status)) this.schedulePoll();
      } catch (error: unknown) {
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 404) {
          this.reset();
          return;
        }
        this.error = getPreviewErrorMessage(error);
        this.status = "error";
        this.stage = "failed";
        clearElapsedTimer();
      }
    },

    reset(): void {
      clearElapsedTimer();
      clearPollTimer();
      storeTaskId("");
      this.status = "idle";
      this.stage = "idle";
      this.mode = "preview";
      this.taskId = "";
      this.fileRef = null;
      this.fileName = "";
      this.courseId = 0;
      this.courseName = "";
      this.startedAt = null;
      this.elapsedSeconds = 0;
      this.previewData = null;
      this.timing = null;
      this.importedCount = 0;
      this.message = "";
      this.error = "";
      this.resultCourseId = null;
      this.resultCourseName = "";
    },

    async startPreview(file: File, params: Record<string, string | number> = {}): Promise<void> {
      if (this.status === "running") return;
      this.reset();
      this.status = "running";
      this.stage = "parsing";
      this.mode = "preview";
      this.fileRef = file;
      this.fileName = file.name;
      this.courseId = Number(params.course_id || 0);
      this.courseName = (params.course_name as string) || "";
      this.startedAt = Date.now();
      this.startElapsedTimer();

      try {
        const task = await createImportTask(file, params);
        storeTaskId(task.id);
        this.applyRemoteTask(task);
        if (ACTIVE_REMOTE_STATUSES.has(task.status)) this.schedulePoll();
      } catch (error: unknown) {
        this.error = getPreviewErrorMessage(error);
        this.status = "error";
        this.stage = "failed";
        clearElapsedTimer();
      }
    },

    async resume(): Promise<void> {
      if (this.taskId || this.status === "success") return;
      const storedTaskId = getStoredTaskId();
      if (!storedTaskId) return;
      this.taskId = storedTaskId;
      await this.refreshTask();
    },

    markImported(result: { imported_count?: number; course_id?: number | null; course_name?: string }): void {
      clearPollTimer();
      this.importedCount = result.imported_count || 0;
      this.resultCourseId = result.course_id ?? null;
      this.resultCourseName = result.course_name || "";
      this.courseName = result.course_name || this.courseName;
      this.message = `导入成功，已导入 ${this.importedCount} 道题。`;
      storeTaskId("");
    },
  },
});

export function useAiImportTask(): AiImportTaskReturn {
  const store = useAiImportTaskStore();
  const refs = storeToRefs(store);
  return {
    status: refs.status,
    stage: refs.stage,
    mode: refs.mode,
    taskId: refs.taskId,
    fileRef: refs.fileRef,
    fileName: refs.fileName,
    courseId: refs.courseId,
    courseName: refs.courseName,
    startedAt: refs.startedAt,
    elapsedSeconds: refs.elapsedSeconds,
    estimatedSeconds: store.estimatedSeconds,
    previewData: refs.previewData,
    timing: refs.timing,
    importedCount: refs.importedCount,
    message: refs.message,
    error: refs.error,
    resultCourseId: refs.resultCourseId,
    resultCourseName: refs.resultCourseName,
    progressTitle: refs.progressTitle as ComputedRef<string>,
    progressDetail: refs.progressDetail as ComputedRef<string>,
    startPreview: store.startPreview,
    resume: store.resume,
    markImported: store.markImported,
    reset: store.reset,
  };
}
