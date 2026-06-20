/**
 * Wrong book API calls — /wrongbook/*
 */
import request from "./request";

/**
 * Fetch wrong-book metadata (available subjects, chapters for filtering).
 * @returns {Promise<Object>} { subjects: string[], chapters: string[] }
 */
export async function getWrongBookMeta() {
  const { data } = await request.get("/wrongbook/meta");
  return data;
}

/**
 * Fetch paginated wrong-book items.
 * @param {Object} [params] - { page, page_size, keyword, type, subject, chapter }
 * @returns {Promise<Object|Array>} Backend returns either an array or { items, total }
 */
export async function getWrongBook(params) {
  const { data } = await request.get("/wrongbook/", { params });
  return data;
}

/**
 * Remove an item from the wrong book.
 * @param {number|string} questionId
 * @returns {Promise<void>}
 */
export async function removeWrongItem(questionId) {
  await request.delete(`/wrongbook/${questionId}`);
}
