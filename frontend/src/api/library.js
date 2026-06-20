/**
 * Public library API calls — /library/*
 */
import request from "./request";

/**
 * Fetch public courses (searchable).
 * @param {Object} [params] - { keyword, page, page_size }
 * @returns {Promise<Array|Object>} Course list (array or { items, total })
 */
export async function getPublicCourses(params) {
  const { data } = await request.get("/library/public", { params });
  return data;
}
