/**
 * Course-related API calls — /courses/*
 */
import request from "./request";

/**
 * Fetch all courses owned by the current user.
 * @returns {Promise<Array>} Course list [{ id, name, question_count, visibility, ... }]
 */
export async function getMyCourses() {
  const { data } = await request.get("/courses/mine");
  return data;
}

/**
 * Fetch a single course by id.
 * @param {number|string} id
 * @returns {Promise<Object>} Course detail object
 */
export async function getCourse(id) {
  const { data } = await request.get(`/courses/${id}`);
  return data;
}

/**
 * Create a new course.
 * @param {string} name
 * @param {string} [description]
 * @returns {Promise<Object>} Created course object
 */
export async function createCourse(name, description) {
  const { data } = await request.post("/courses/", { name, description });
  return data;
}

/**
 * Update an existing course.
 * @param {number|string} id
 * @param {Object} payload - Fields to update (name, description, etc.)
 * @returns {Promise<Object>} Updated course object
 */
export async function updateCourse(id, payload) {
  const { data } = await request.put(`/courses/${id}`, payload);
  return data;
}

/**
 * Publish a course to the public library.
 * @param {number|string} id
 * @returns {Promise<Object>} Updated course with visibility='public'
 */
export async function publishCourse(id) {
  const { data } = await request.post(`/courses/${id}/publish`);
  return data;
}

/**
 * Retract a course from the public library (make private).
 * @param {number|string} id
 * @returns {Promise<Object>} Updated course with visibility='private'
 */
export async function unpublishCourse(id) {
  const { data } = await request.post(`/courses/${id}/unpublish`);
  return data;
}

/**
 * Delete a course and all its questions.
 * @param {number|string} id
 * @returns {Promise<void>}
 */
export async function deleteCourse(id) {
  await request.delete(`/courses/${id}`);
}
