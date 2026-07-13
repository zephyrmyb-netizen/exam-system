import { ref, type Ref } from "vue";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import {
  getDailyActivity,
  getStreak,
  getTagAccuracy,
  getTeacherCourseAnalytics,
  getTodayRecommendation,
  getTypeDistribution,
} from "../api/analytics";
import request, { getErrorMessage, getToken } from "../api/request";
import type {
  CourseAnalytics,
  DailyActivity,
  Streak,
  TagAccuracy,
  TodayRecommendation,
  TypeDistribution,
  WeakType,
} from "../types";

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
  activity: Ref<DailyActivity[]>;
  typeDistribution: Ref<TypeDistribution[]>;
  tagAccuracy: Ref<TagAccuracy[]>;
  courseAnalytics: Ref<CourseAnalytics[]>;
  streak: Ref<Streak>;
  recommendation: Ref<TodayRecommendation | null>;
  streakAvailable: Ref<boolean | null>;
  recommendationAvailable: Ref<boolean | null>;
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

const activity = ref<DailyActivity[]>([]);
const typeDistribution = ref<TypeDistribution[]>([]);
const tagAccuracy = ref<TagAccuracy[]>([]);
const courseAnalytics = ref<CourseAnalytics[]>([]);
const streak = ref<Streak>({
  current_streak: 0,
  longest_streak: 0,
  last_practiced_date: null,
});
const recommendation = ref<TodayRecommendation | null>(null);
const streakAvailable = ref<boolean | null>(null);
const recommendationAvailable = ref<boolean | null>(null);

const loading = ref(false);
const errorMessage = ref("");

let activeAuthContext: string | null = null;
let activeGeneration = 0;
let activeRequest: Promise<void> | null = null;
let activeRequestContext: string | null = null;

function resetOverviewSnapshot(): void {
  stats.value = {
    todayCount: null,
    totalCount: null,
    correctCount: null,
    wrongCount: null,
    accuracyRate: null,
    recentCount7d: null,
    coursesCount: null,
  };
  review.value = {
    dueCount: null,
    wrongCount: null,
    weakTypes: [],
    recommendedModes: [],
  };
  activity.value = [];
  typeDistribution.value = [];
  tagAccuracy.value = [];
  courseAnalytics.value = [];
  streak.value = {
    current_streak: 0,
    longest_streak: 0,
    last_practiced_date: null,
  };
  recommendation.value = null;
  streakAvailable.value = null;
  recommendationAvailable.value = null;
  loading.value = false;
  errorMessage.value = "";
}

function isCurrentRequest(generation: number, authContext: string): boolean {
  return generation === activeGeneration && authContext === activeAuthContext && getToken() === authContext;
}

export function useStudyOverview(): UseStudyOverviewReturn {
  function fetchAll(): Promise<void> {
    const authContext = getToken();
    if (authContext !== activeAuthContext) {
      activeAuthContext = authContext;
      activeRequest = null;
      activeRequestContext = null;
      resetOverviewSnapshot();
    }

    if (activeRequest && activeRequestContext === authContext) return activeRequest;

    const generation = ++activeGeneration;
    loading.value = true;
    errorMessage.value = "";
    streakAvailable.value = null;
    recommendationAvailable.value = null;

    const requestPromise = (async () => {
      try {
        const [
          statsResult,
          coursesResult,
          reviewResult,
          weakResult,
          activityResult,
          typeDistributionResult,
          tagAccuracyResult,
          streakResult,
          recommendationResult,
          courseAnalyticsResult,
        ] = await Promise.allSettled([
          getPracticeStats(),
          request.get("/courses/mine"),
          getTodayReview(),
          getWeakTypes(),
          getDailyActivity(14),
          getTypeDistribution(),
          getTagAccuracy(),
          getStreak(),
          getTodayRecommendation(),
          getTeacherCourseAnalytics(),
        ]);

        if (!isCurrentRequest(generation, authContext)) return;

        if (statsResult.status === "fulfilled") {
          const data = statsResult.value || ({} as Record<string, number>);
          stats.value.todayCount = data.today_count ?? null;
          stats.value.totalCount = data.total_count ?? null;
          stats.value.correctCount = data.correct_count ?? null;
          stats.value.wrongCount = data.wrong_count ?? null;
          stats.value.accuracyRate = data.accuracy_rate ?? null;
          stats.value.recentCount7d = data.recent_count_7d ?? null;
        }

        if (coursesResult.status === "fulfilled") {
          const data = coursesResult.value?.data || {};
          const items = Array.isArray(data)
            ? data
            : Array.isArray((data as Record<string, unknown>).items)
              ? (data as Record<string, unknown>).items
              : [];
          stats.value.coursesCount = (items as unknown[]).length;
        }

        if (reviewResult.status === "fulfilled") {
          const data = reviewResult.value || ({} as Record<string, unknown>);
          review.value.dueCount = (data.due_count as number) ?? null;
          review.value.wrongCount = (data.wrong_count as number) ?? null;
          review.value.recommendedModes = Array.isArray(data.recommended_modes)
            ? (data.recommended_modes as string[])
            : [];
        }

        if (weakResult.status === "fulfilled") {
          review.value.weakTypes = Array.isArray(weakResult.value) ? (weakResult.value.slice(0, 8) as WeakType[]) : [];
        }

        if (activityResult.status === "fulfilled") {
          activity.value = Array.isArray(activityResult.value) ? activityResult.value : [];
        }

        if (typeDistributionResult.status === "fulfilled") {
          typeDistribution.value = Array.isArray(typeDistributionResult.value) ? typeDistributionResult.value : [];
        }

        if (tagAccuracyResult.status === "fulfilled") {
          tagAccuracy.value = Array.isArray(tagAccuracyResult.value) ? tagAccuracyResult.value.slice(0, 8) : [];
        }

        if (streakResult.status === "fulfilled") {
          streak.value = streakResult.value;
          streakAvailable.value = true;
        } else {
          streakAvailable.value = false;
        }

        if (recommendationResult.status === "fulfilled") {
          recommendation.value = recommendationResult.value;
          recommendationAvailable.value = true;
        } else {
          recommendationAvailable.value = false;
        }

        if (courseAnalyticsResult.status === "fulfilled") {
          courseAnalytics.value = Array.isArray(courseAnalyticsResult.value)
            ? courseAnalyticsResult.value.slice(0, 6)
            : [];
        }

        const firstRejected = [
          statsResult,
          coursesResult,
          reviewResult,
          weakResult,
          activityResult,
          typeDistributionResult,
          tagAccuracyResult,
          streakResult,
          recommendationResult,
        ].find((result) => result.status === "rejected");
        if (firstRejected) {
          errorMessage.value = getErrorMessage(
            (firstRejected as PromiseRejectedResult).reason,
            "学习数据更新失败，请稍后重试。",
          );
        }
      } catch (error: unknown) {
        if (isCurrentRequest(generation, authContext)) {
          errorMessage.value = getErrorMessage(error, "学习数据更新失败，请稍后重试。");
        }
      } finally {
        if (isCurrentRequest(generation, authContext)) {
          loading.value = false;
          activeRequest = null;
          activeRequestContext = null;
        }
      }
    })();

    activeRequest = requestPromise;
    activeRequestContext = authContext;
    return requestPromise;
  }

  return {
    stats,
    review,
    activity,
    typeDistribution,
    tagAccuracy,
    courseAnalytics,
    streak,
    recommendation,
    streakAvailable,
    recommendationAvailable,
    loading,
    errorMessage,
    fetchAll,
  };
}
