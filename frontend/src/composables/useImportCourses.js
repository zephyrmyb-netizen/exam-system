import { ref } from "vue";
import request, { getErrorMessage } from "../api/request";

export function useImportCourses() {
  const courses = ref([]);
  const coursesLoading = ref(false);
  const coursesError = ref("");

  async function fetchCourses() {
    coursesLoading.value = true;
    coursesError.value = "";
    try {
      const { data } = await request.get("/courses/mine");
      courses.value = Array.isArray(data) ? data : data.items || [];
    } catch (error) {
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
