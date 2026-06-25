import { ref, type Ref } from "vue";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import request, { getErrorMessage } from "../api/request";
import type { WeakType } from "../types";

interface OverviewStats {
  todayCount: number | null;
  totalCount: number | null;
  correctCount: number | null;
  wrongCount: number | null;
  accuracyRate: number | null;
  recentCount7d: number | null;
  coursesCount: number | null;
}

interface OverviewReview {
  dueCount: number | null;
  wrongCount: number | null;
  weakTypes: WeakType[];
  recommendedModes: string[];
}

export interface UseStudyOverviewReturn {
  stats: Ref<OverviewStats>;
  review: Ref<OverviewReview>;
  loading: Ref<boolean>;
  errorMessage: Ref<string>;
  fetchAll: () => Promise<void>;
}

const stats = ref<OverviewStats>({
  todayCount: null,
  totalCount: null,
  correctCount: null,
  wrongCount: null,
  accuracyRate: null,
  recentCount7d: null,
  coursesCount: null,
});

const review = ref<OverviewReview>({
  dueCount: null,
  wrongCount: null,
  weakTypes: [],
  recommendedModes: [],
});

const loading = ref(false);
const errorMessage = ref("");

export function useStudyOverview(): UseStudyOverviewReturn {
  async function fetchAll(): Promise<void> {
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
        const data = statsResult.value || {} as Record<string, number>;
        stats.value.todayCount = data.today_count ?? null;
        stats.value.totalCount = data.total_count ?? null;
        stats.value.correctCount = data.correct_count ?? null;
        stats.value.wrongCount = data.wrong_count ?? null;
        stats.value.accuracyRate = data.accuracy_rate ?? null;
        stats.value.recentCount7d = data.recent_count_7d ?? null;
      }

      if (coursesResult.status === "fulfilled") {
        const data = coursesResult.value?.data || {};
        const items = Array.isArray(data) ? data : Array.isArray((data as Record<string, unknown>).items) ? (data as Record<string, unknown>).items : [];
        stats.value.coursesCount = (items as unknown[]).length;
      }

      if (reviewResult.status === "fulfilled") {
        const data = reviewResult.value || {} as Record<string, unknown>;
        review.value.dueCount = (data.due_count as number) ?? null;
        review.value.wrongCount = (data.wrong_count as number) ?? null;
        review.value.recommendedModes = Array.isArray(data.recommended_modes) ? data.recommended_modes as string[] : [];
      }

      if (weakResult.status === "fulfilled") {
        review.value.weakTypes = Array.isArray(weakResult.value) ? weakResult.value.slice(0, 8) as WeakType[] : [];
      }

      const firstRejected = [statsResult, coursesResult, reviewResult, weakResult].find(
        (result) => result.status === "rejected",
      );
      if (firstRejected) {
        errorMessage.value = getErrorMessage((firstRejected as PromiseRejectedResult).reason, "学习数据更新失败，请稍后重试。");
      }
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "学习数据更新失败，请稍后重试。");
    } finally {
      loading.value = false;
    }
  }

  return { stats, review, loading, errorMessage, fetchAll };
}
