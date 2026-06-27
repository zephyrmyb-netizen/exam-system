import { ref, type Ref } from "vue";

import request, { getErrorMessage } from "../api/request";
import type { Course } from "../types";

export interface UseImportCoursesReturn {
  courses: Ref<Course[]>;
  coursesLoading: Ref<boolean>;
  coursesError: Ref<string>;
  fetchCourses: () => Promise<void>;
}

export function useImportCourses(): UseImportCoursesReturn {
  const courses = ref<Course[]>([]);
  const coursesLoading = ref<boolean>(false);
  const coursesError = ref<string>("");

  async function fetchCourses(): Promise<void> {
    coursesLoading.value = true;
    coursesError.value = "";
    try {
      const { data } = await request.get<Course[] | { items: Course[] }>("/courses/mine");
      courses.value = Array.isArray(data) ? data : (data as { items: Course[] }).items || [];
    } catch (error: unknown) {
      courses.value = [];
      coursesError.value = getErrorMessage(error, "获取题库列表失败");
    } finally {
      coursesLoading.value = false;
    }
  }

  return {
    courses,
    coursesLoading,
    coursesError,
    fetchCourses,
  };
}
