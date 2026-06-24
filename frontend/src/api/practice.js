/**
 * Practice-related API calls -> /practice/*
 *
 * Encapsulates all /practice/ endpoints so views don't
 * hard-code request paths or response shapes.
 */
import request from "./request";

function practiceGet(url, params) {
  return request.get(url, { params }).then(({ data }) => data);
}

function practicePost(url, payload) {
  return request.post(url, payload).then(({ data }) => data);
}

/**
 * Fetch practice stats (today_count, total_count, accuracy_rate, etc.).
 * Returns the response data object on success; throws on failure.
 */
export async function getPracticeStats() {
  return practiceGet("/practice/stats");
}

/**
 * Fetch paginated practice history.
 * @param {Object} [params] - { page, page_size, ... }
 * @returns {Promise<Object>} { items, total, page, page_size, ... }
 */
export async function getPracticeHistory(params) {
  return practiceGet("/practice/history", params);
}

/**
 * Fetch one random practice question.
 * @param {Object} [params] - { type, course_id, ... }
 * @returns {Promise<Object>} The question object.
 */
export async function getRandomPracticeQuestion(params) {
  return practiceGet("/practice/random", params);
}

/**
 * Submit an answer for one question.
 * @param {Object} payload - { question_id, user_answer }
 * @returns {Promise<Object>} Result with is_correct, correct_answer, analysis, ...
 */
export async function submitPracticeAnswer(payload) {
  return practicePost("/practice/submit", payload);
}

/**
 * Fetch today's review suggestion (due count, weak types, recommended modes).
 * @returns {Promise<Object>} { due_count, wrong_count, weak_types, recommended_modes }
 */
export async function getTodayReview() {
  return practiceGet("/practice/review/today");
}

/**
 * Fetch weak question types analysis.
 * @returns {Promise<Array>} [{ question_type, total_attempts, wrong_attempts, error_rate }]
 */
export async function getWeakTypes() {
  return practiceGet("/practice/insights/weak-types");
}

/**
 * Fetch a random wrong question for review mode.
 * @param {Object} [params] - { course_id, type }
 * @returns {Promise<Object>} The question object.
 */
export async function getReviewWrongQuestion(params) {
  return practiceGet("/practice/review/wrong", params);
}

/**
 * Fetch a due review question (spaced repetition / overdue practice).
 * @param {Object} [params] - { course_id, type }
 * @returns {Promise<Object>} The question object.
 */
export async function getReviewDueQuestion(params) {
  return practiceGet("/practice/review/due", params);
}

/**
 * Fetch comprehensive learning statistics.
 * @returns {Promise<Object>} Statistical data (may include today_count, total_count,
 *   accuracy_rate, correct_count, wrong_count, recent_count_7d, etc.)
 */
export async function getLearningStats() {
  return practiceGet("/practice/stats");
}
