/**
 * File import API calls — /imports/*
 *
 * Upload methods use FormData (proper multipart boundary).
 */
import request from "./request";

/**
 * Upload a .docx / .pptx file and extract its text content.
 * @param {File} file - The file to extract
 * @param {Object} [params] - { course_id }
 * @returns {Promise<Object>} { filename, text, ... }
 */
export async function extractFileText(file, params) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post("/imports/file", formData, { params });
  return data;
}

/**
 * Upload a .docx / .pptx file for AI auto-recognition and import.
 * Long timeout (120s) for large files.
 * @param {File} file - The file to process
 * @param {Object} [params] - { course_id, course_name }
 * @returns {Promise<Object>} { imported_count, course_id, course_name, ... }
 */
export async function autoImportFile(file, params) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post("/imports/file/auto", formData, {
    params,
    timeout: 120000,
  });
  return data;
}

/**
 * Upload a .docx / .pptx file for AI preview (parse only, no import).
 * Returns parsed questions for user confirmation.
 * @param {File} file - The file to preview
 * @param {Object} [params] - { course_name }
 * @returns {Promise<Object>} { suggested_course_name, questions, warnings, total_count, ... }
 */
export async function previewFile(file, params) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post("/imports/file/preview", formData, {
    params,
    timeout: 120000,
  });
  return data;
}

/**
 * Confirm and commit an import after user review.
 * @param {Object} payload - { course_id?, course_name?, questions: [...] }
 * @returns {Promise<Object>} { imported_count, course_id, course_name }
 */
export async function confirmImport(payload) {
  const { data } = await request.post("/imports/confirm", payload);
  return data;
}
