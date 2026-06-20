/**
 * Shared study overview data — single source of truth for
 * Home.vue, Mine.vue, and StudyOverview.vue.
 *
 * Module-level refs survive component mount/unmount so every
 * consumer sees the same data without redundant requests.
 */
import { ref } from "vue";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import request from "../api/request";

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
  weakTypes: [],          // [{ question_type, total_attempts, wrong_attempts, error_rate }]
  recommendedModes: [],
});

const loading = ref(false);

export function useStudyOverview() {
  async function fetchAll() {
    if (loading.value) return;
    loading.value = true;

    const [statsR, coursesR, reviewR, weakR] = await Promise.allSettled([
      getPracticeStats(),
      request.get("/courses/mine"),
      getTodayReview(),
      getWeakTypes(),
    ]);

    if (statsR.status === "fulfilled") {
      const d = statsR.value;
      stats.value.todayCount = d.today_count ?? null;
      stats.value.totalCount = d.total_count ?? null;
      stats.value.correctCount = d.correct_count ?? null;
      stats.value.wrongCount = d.wrong_count ?? null;
      stats.value.accuracyRate = d.accuracy_rate ?? null;
      stats.value.recentCount7d = d.recent_count_7d ?? null;
    }

    if (coursesR.status === "fulfilled") {
      const d = coursesR.value.data;
      const items = Array.isArray(d) ? d : d.items || [];
      stats.value.coursesCount = items.length;
    }

    if (reviewR.status === "fulfilled") {
      const d = reviewR.value;
      review.value.dueCount = d.due_count ?? null;
      review.value.wrongCount = d.wrong_count ?? null;
      review.value.recommendedModes = d.recommended_modes || [];
    }

    if (weakR.status === "fulfilled") {
      review.value.weakTypes = weakR.value.slice(0, 8);
    }

    loading.value = false;
  }

  return { stats, review, loading, fetchAll };
}
