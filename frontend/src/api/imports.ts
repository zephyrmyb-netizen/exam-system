import type { FileExtractResponse, ImportPreviewResponse, ConfirmImportRequest, ConfirmImportResponse } from "@/types";
import request from "./request.ts";

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
  }).then(({ data }) => data as ImportPreviewResponse);
}

export function confirmImport(
  payload: ConfirmImportRequest,
): Promise<ConfirmImportResponse> {
  return request.post("/imports/confirm", payload).then(({ data }) => data as ConfirmImportResponse);
}
