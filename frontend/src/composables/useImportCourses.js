import { ref } from "vue";
import request from "../api/request";

export function useImportCourses() {
  const courses = ref([]);
  const coursesLoading = ref(false);

  async function fetchCourses() {
    coursesLoading.value = true;
    try {
      const { data } = await request.get("/courses/mine");
      courses.value = Array.isArray(data) ? data : data.items || [];
    } catch {
      courses.value = [];
    } finally {
      coursesLoading.value = false;
    }
  }

  return {
    courses,
    coursesLoading,
    fetchCourses,
  };
}
