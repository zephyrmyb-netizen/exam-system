import { type ComputedRef, type Ref } from "vue";
import { defineStore, storeToRefs } from "pinia";

import { previewFile } from "../api/imports";
import { getErrorMessage } from "../api/request";
import type { ImportPreviewResponse, ImportTiming } from "../types";
import { getFileExtension } from "../utils/importFiles";

export type TaskStatus = "idle" | "running" | "success" | "error";
export type TaskMode = "preview" | "auto";

export interface AiImportTaskReturn {
  status: Ref<TaskStatus>;
  mode: Ref<TaskMode>;
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
  markImported: (result: { imported_count?: number; course_id?: number | null; course_name?: string }) => void;
  reset: () => void;
}

let elapsedTimer: ReturnType<typeof setInterval> | null = null;

function formatDuration(ms: number | undefined): string {
  const value = Number(ms || 0);
  if (value >= 1000) return `${Math.round(value / 100) / 10} 秒`;
  return `${value} 毫秒`;
}

function clearElapsedTimer(): void {
  if (elapsedTimer !== null) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

export const useAiImportTaskStore = defineStore("aiImportTask", {
  state: () => ({
    status: "idle" as TaskStatus,
    mode: "preview" as TaskMode,
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
        if (ext === ".pptx") {
          return state.elapsedSeconds < 3 ? "正在读取 PPT 页内容" : "正在识别 PPT 中的图片题目";
        }
        if (ext === ".pdf") {
          return state.elapsedSeconds < 3 ? "正在读取 PDF 页面文字" : "AI 正在解析 PDF 题目";
        }
        if ([".png", ".jpg", ".jpeg", ".webp"].includes(ext)) return "正在识别图片中的题目";
        if (state.elapsedSeconds < 3) return "正在提取文档文字";
        return "AI 正在解析题目，请稍等";
      }
      if (state.status === "success") return "AI 解析完成";
      if (state.status === "error") return "AI 解析失败";
      return "AI 导入";
    },

    progressDetail(state): string {
      if (state.status === "running") {
        const ext = getFileExtension(state.fileName);
        if (ext === ".pptx") {
          return state.elapsedSeconds < 3
            ? "正在读取 PPT 页内容，请稍候。"
            : "正在识别 PPT 中的图片题目，PPT 页数较多时可能需要 1-3 分钟。";
        }
        if (ext === ".pdf") {
          return "文本型 PDF 会直接提取页面文字；扫描版 PDF 建议导出为图片后上传。";
        }
        if ([".png", ".jpg", ".jpeg", ".webp"].includes(ext)) {
          return "图片识别依赖多模态 AI，可能需要 10-60 秒。";
        }
        if (state.elapsedSeconds < 3) {
          return "正在提取文档文字，请稍候。";
        }
        return "正在让 AI 整理题目，文档较长时可能需要 30-120 秒；切到其他页面也会继续。";
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
        if (this.startedAt !== null) {
          this.elapsedSeconds = Math.floor((Date.now() - this.startedAt) / 1000);
        }
      }, 1000);
    },

    reset(): void {
      clearElapsedTimer();
      this.status = "idle";
      this.mode = "preview";
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
      this.mode = "preview";
      this.fileRef = file || null;
      this.fileName = file?.name || "";
      this.courseId = Number(params.course_id || 0);
      this.courseName = (params.course_name as string) || "";
      this.startedAt = Date.now();
      this.startElapsedTimer();

      try {
        const data = await previewFile(file, params);
        this.previewData = data;
        this.timing = data?.timing || null;
        this.message = `AI 已解析出 ${data?.questions?.length || 0} 道题，请确认后导入。`;
        this.status = "success";
      } catch (err: unknown) {
        this.error = getErrorMessage(err, "AI 解析失败，请检查网络后重试");
        this.status = "error";
      } finally {
        clearElapsedTimer();
      }
    },

    markImported(result: { imported_count?: number; course_id?: number | null; course_name?: string }): void {
      this.importedCount = result?.imported_count || 0;
      this.resultCourseId = result?.course_id ?? null;
      this.resultCourseName = result?.course_name || "";
      this.courseName = result?.course_name || this.courseName;
      this.message = `导入成功，已导入 ${this.importedCount} 道题。`;
    },
  },
});

export function useAiImportTask(): AiImportTaskReturn {
  const store = useAiImportTaskStore();
  const refs = storeToRefs(store);
  return {
    status: refs.status,
    mode: refs.mode,
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
    markImported: store.markImported,
    reset: store.reset,
  };
}
