import type { Course, CourseUpdate } from "@/types";
import request from "./request.ts";

export function getMyCourses(): Promise<Course[]> {
  return request.get("/courses/mine").then(({ data }) => data as Course[]);
}

export function getCourse(id: number): Promise<Course> {
  return request.get(`/courses/${id}`).then(({ data }) => data as Course);
}

export function createCourse(name: string, description?: string): Promise<Course> {
  return request.post("/courses/", { name, description }).then(({ data }) => data as Course);
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
