import type { PublicCourse } from "@/types";
import request from "./request.ts";

export function getPublicCourses(
  params?: Record<string, string | number>,
): Promise<PublicCourse[] | { total: number; items: PublicCourse[] }> {
  return request.get("/library/public", { params }).then(({ data }) => data);
}

export function copyPublicCourse(id: number): Promise<{ copied_course_id: number }> {
  return request.post(`/library/public/${id}/copy`).then(({ data }) => data);
}

export function favoritePublicCourse(id: number): Promise<{ favorited: boolean }> {
  return request.post(`/library/public/${id}/favorite`).then(({ data }) => data);
}

export function reportPublicCourse(id: number, reason: string, detail: string): Promise<void> {
  return request.post(`/library/public/${id}/report`, { reason, detail });
}
