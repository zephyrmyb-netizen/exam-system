import type {
  FileExtractResponse,
  ImportPreviewResponse,
  ConfirmImportRequest,
  ConfirmImportResponse,
  ImportTaskResponse,
} from "@/types";
import request from "./request.ts";

export const AI_IMPORT_FORMAT_ERROR_MESSAGE = "AI 返回格式异常，已跳过异常片段，请尝试重新解析。";

type UserFacingImportError = Error & { userMessage: string };

function invalidPreviewResponseError(): UserFacingImportError {
  const error = new Error("Invalid import preview response") as UserFacingImportError;
  error.userMessage = AI_IMPORT_FORMAT_ERROR_MESSAGE;
  return error;
}

function parsePreviewResponse(data: unknown): ImportPreviewResponse {
  if (!data || typeof data !== "object" || Array.isArray(data) || !Array.isArray((data as ImportPreviewResponse).questions)) {
    throw invalidPreviewResponseError();
  }
  const preview = data as ImportPreviewResponse;
  const warnings = Array.isArray(preview.warnings) ? preview.warnings : [];
  const hasAiFormatWarning = warnings.some((warning) => (
    /AI 返回了非 JSON 格式内容|AI 返回内容中未找到 questions 数组|AI 返回格式异常/.test(warning)
  ));

  if (!hasAiFormatWarning || warnings.includes(AI_IMPORT_FORMAT_ERROR_MESSAGE)) {
    return { ...preview, warnings };
  }

  return {
    ...preview,
    warnings: [AI_IMPORT_FORMAT_ERROR_MESSAGE, ...warnings],
  };
}

export function extractFileText(
  file: File,
  params?: Record<string, string | number>,
): Promise<FileExtractResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/imports/file", formData, { params }).then(({ data }) => data as FileExtractResponse);
}

export function autoImportFile(
  file: File,
  params?: Record<string, string | number>,
): Promise<{ imported_count: number; course_id: number | null; course_name: string }> {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/imports/file/auto", formData, {
    params,
    timeout: 420000,
  }).then(({ data }) => data);
}

export function previewFile(
  file: File,
  params?: Record<string, string | number>,
): Promise<ImportPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/imports/file/preview", formData, {
    params,
    timeout: 420000,
  }).then(({ data }) => parsePreviewResponse(data));
}

export function confirmImport(
  payload: ConfirmImportRequest,
): Promise<ConfirmImportResponse> {
  return request.post("/imports/confirm", payload).then(({ data }) => data as ConfirmImportResponse);
}

export function createImportTask(
  file: File,
  params?: Record<string, string | number>,
): Promise<ImportTaskResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/imports/tasks", formData, { params, timeout: 30000 }).then(({ data }) => data as ImportTaskResponse);
}

export function getImportTask(taskId: string): Promise<ImportTaskResponse> {
  return request.get(`/imports/tasks/${taskId}`).then(({ data }) => data as ImportTaskResponse);
}

export function confirmImportTask(
  taskId: string,
  payload: ConfirmImportRequest,
): Promise<ConfirmImportResponse> {
  return request.post(`/imports/tasks/${taskId}/confirm`, payload).then(({ data }) => data as ConfirmImportResponse);
}
