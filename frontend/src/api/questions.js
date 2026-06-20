/**
 * Question-related API calls — /questions/*
 */
import request from "./request";

/**
 * Fetch question metadata (available subjects, chapters for filtering).
 * @returns {Promise<Object>} { subjects: string[], chapters: string[] }
 */
export async function getQuestionsMeta() {
  const { data } = await request.get("/questions/meta");
  return data;
}

/**
 * Fetch paginated question list.
 * @param {Object} [params] - { page, page_size, keyword, type, subject, chapter, course_id }
 * @returns {Promise<Object|Array>} Backend returns either an array or { items, total }
 */
export async function getQuestions(params) {
  const { data } = await request.get("/questions/", { params });
  return data;
}

/**
 * Create a single question.
 * @param {Object} payload - { subject, chapter, type, question, options, answer, analysis, difficulty, course_id }
 * @returns {Promise<Object>} Created question object
 */
export async function createQuestion(payload) {
  const { data } = await request.post("/questions/", payload);
  return data;
}

/**
 * Update an existing question.
 * @param {number|string} id
 * @param {Object} payload - Fields to update
 * @returns {Promise<Object>} Updated question object
 */
export async function updateQuestion(id, payload) {
  const { data } = await request.put(`/questions/${id}`, payload);
  return data;
}

/**
 * Batch import questions (JSON array).
 * @param {Array} items - Array of question objects
 * @param {Object} [params] - { course_id }
 * @returns {Promise<Object>} { imported_count, course_id, course_name }
 */
export async function batchCreateQuestions(items, params) {
  const { data } = await request.post("/questions/batch", items, { params });
  return data;
}

/**
 * Delete a question.
 * @param {number|string} id
 * @returns {Promise<void>}
 */
export async function deleteQuestion(id) {
  await request.delete(`/questions/${id}`);
}

/**
 * Publish a question to the public library.
 * @param {number|string} id
 * @returns {Promise<Object>} Updated question
 */
export async function publishQuestion(id) {
  const { data } = await request.post(`/questions/${id}/publish`);
  return data;
}

/**
 * Retract a question from the public library (make private).
 * @param {number|string} id
 * @returns {Promise<Object>} Updated question
 */
export async function unpublishQuestion(id) {
  const { data } = await request.post(`/questions/${id}/unpublish`);
  return data;
}
