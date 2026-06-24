import { ref } from "vue";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import request, { getErrorMessage } from "../api/request";

const stats = ref({
  todayCount: null,
  totalCount: null,
  correctCount: null,
  wrongCount: null,
  accuracyRate: null,
  recentCount7d: null,
  coursesCount: null,
});

const review = ref({
  dueCount: null,
  wrongCount: null,
  weakTypes: [],
  recommendedModes: [],
});

const loading = ref(false);
const errorMessage = ref("");

export function useStudyOverview() {
  async function fetchAll() {
    if (loading.value) return;
    loading.value = true;
    errorMessage.value = "";

    try {
      const [statsResult, coursesResult, reviewResult, weakResult] = await Promise.allSettled([
        getPracticeStats(),
        request.get("/courses/mine"),
        getTodayReview(),
        getWeakTypes(),
      ]);

      if (statsResult.status === "fulfilled") {
        const data = statsResult.value || {};
        stats.value.todayCount = data.today_count ?? null;
        stats.value.totalCount = data.total_count ?? null;
        stats.value.correctCount = data.correct_count ?? null;
        stats.value.wrongCount = data.wrong_count ?? null;
        stats.value.accuracyRate = data.accuracy_rate ?? null;
        stats.value.recentCount7d = data.recent_count_7d ?? null;
      }

      if (coursesResult.status === "fulfilled") {
        const data = coursesResult.value?.data || {};
        const items = Array.isArray(data) ? data : Array.isArray(data.items) ? data.items : [];
        stats.value.coursesCount = items.length;
      }

      if (reviewResult.status === "fulfilled") {
        const data = reviewResult.value || {};
        review.value.dueCount = data.due_count ?? null;
        review.value.wrongCount = data.wrong_count ?? null;
        review.value.recommendedModes = Array.isArray(data.recommended_modes) ? data.recommended_modes : [];
      }

      if (weakResult.status === "fulfilled") {
        review.value.weakTypes = Array.isArray(weakResult.value) ? weakResult.value.slice(0, 8) : [];
      }

      const firstRejected = [statsResult, coursesResult, reviewResult, weakResult].find(
        (result) => result.status === "rejected",
      );
      if (firstRejected) {
        errorMessage.value = getErrorMessage(firstRejected.reason, "学习数据更新失败，请稍后重试。");
      }
    } catch (error) {
      errorMessage.value = getErrorMessage(error, "学习数据更新失败，请稍后重试。");
    } finally {
      loading.value = false;
    }
  }

  return { stats, review, loading, errorMessage, fetchAll };
}
