import type { Course } from "@/types";
import request from "./request.ts";

export function getPublicCourses(
  params?: Record<string, string | number>,
): Promise<Course[] | { total: number; items: Course[] }> {
  return request.get("/library/public", { params }).then(({ data }) => data);
}
