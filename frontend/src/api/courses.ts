import type { Course, CourseCreate, CourseUpdate, Question, SharedCourse } from "@/types";
import request from "./request.ts";

export function getMyCourses(): Promise<Course[]> {
  return request.get("/courses/mine").then(({ data }) => data as Course[]);
}

export function getCourse(id: number): Promise<Course> {
  return request.get(`/courses/${id}`).then(({ data }) => data as Course);
}

/**
 * Fetch the complete course list before a normal practice session starts.
 * The returned order becomes that session's stable 1..N order; the UI never
 * exposes database IDs or source-document labels as question numbers.
 */
export function getCoursePracticeQuestions(id: number): Promise<Question[]> {
  return request.get(`/courses/${id}/questions`, { params: { order: "asc" } }).then(({ data }) => {
    if (Array.isArray(data)) return data as Question[];
    return Array.isArray(data?.items) ? (data.items as Question[]) : [];
  });
}

export function createCourse(payload: CourseCreate): Promise<Course> {
  return request.post("/courses/", payload).then(({ data }) => data as Course);
}

export function updateCourse(id: number, payload: CourseUpdate): Promise<Course> {
  return request.patch(`/courses/${id}`, payload).then(({ data }) => data as Course);
}

export function publishCourse(id: number): Promise<Course> {
  return request.post(`/courses/${id}/publish`).then(({ data }) => data as Course);
}

export function unpublishCourse(id: number): Promise<Course> {
  return request.post(`/courses/${id}/unpublish`).then(({ data }) => data as Course);
}

export function deleteCourse(id: number): Promise<void> {
  return request.delete(`/courses/${id}`);
}

export function createCourseShareLink(id: number): Promise<{ token: string }> {
  return request.post(`/courses/${id}/share-link`).then(({ data }) => data as { token: string });
}

export function getSharedCourse(token: string): Promise<SharedCourse> {
  return request.get(`/courses/share/${token}`).then(({ data }) => data as SharedCourse);
}

export function copySharedCourse(token: string): Promise<{ id: number }> {
  return request.post(`/courses/share/${token}/copy`).then(({ data }) => data as { id: number });
}
