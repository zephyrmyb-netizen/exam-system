import { ref, type Ref } from "vue";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import {
  getDailyActivity,
  getStreak,
  getTagAccuracy,
  getOwnerCourseAnalytics,
  getTodayRecommendation,
  getTypeDistribution,
} from "../api/analytics";
import { getErrorMessage, getToken } from "../api/request";
import { useMyCourses } from "./useMyCourses";
import type {
  CourseAnalytics,
  DailyActivity,
  Streak,
  TagAccuracy,
  TodayRecommendation,
  TypeDistribution,
  WeakType,
} from "../types";

const OVERVIEW_CACHE_TTL_MS = 30_000;

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
  /** @deprecated Use isInitialLoading for new callers. */
  loading: Ref<boolean>;
  isInitialLoading: Ref<boolean>;
  isRefreshing: Ref<boolean>;
  hasLoaded: Ref<boolean>;
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

const isInitialLoading = ref(false);
const loading = isInitialLoading;
const isRefreshing = ref(false);
const errorMessage = ref("");
const hasLoaded = ref(false);

let activeAuthContext: string | null = null;
let activeGeneration = 0;
let activeRequest: Promise<void> | null = null;
let activeRequestContext: string | null = null;
let lastLoadedAt = 0;

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
  isInitialLoading.value = false;
  isRefreshing.value = false;
  errorMessage.value = "";
  hasLoaded.value = false;
  lastLoadedAt = 0;
}

export function resetStudyOverviewCache(): void {
  activeGeneration += 1;
  activeAuthContext = null;
  activeRequest = null;
  activeRequestContext = null;
  resetOverviewSnapshot();
}

function isCurrentRequest(generation: number, authContext: string): boolean {
  return generation === activeGeneration && authContext === activeAuthContext && getToken() === authContext;
}

export function useStudyOverview(): UseStudyOverviewReturn {
  const courseStore = useMyCourses();

  function fetchAll(): Promise<void> {
    const authContext = getToken();
    if (authContext !== activeAuthContext) {
      activeAuthContext = authContext;
      activeRequest = null;
      activeRequestContext = null;
      resetOverviewSnapshot();
    }

    if (activeRequest && activeRequestContext === authContext) return activeRequest;

    if (hasLoaded.value && Date.now() - lastLoadedAt < OVERVIEW_CACHE_TTL_MS) {
      return Promise.resolve();
    }

    const generation = ++activeGeneration;
    const initialLoad = !hasLoaded.value;
    if (initialLoad) {
      isInitialLoading.value = true;
      errorMessage.value = "";
      streakAvailable.value = null;
      recommendationAvailable.value = null;
    } else isRefreshing.value = true;

    const requestPromise = (async () => {
      try {
        // Render each section as soon as it resolves; slow charts must not hold
        // back today's counts. A generation check prevents stale account data.
        function observe<T>(promise: Promise<T>, apply: (value: T) => void, reject?: () => void): Promise<T> {
          return promise.then(
            (value) => {
              if (isCurrentRequest(generation, authContext)) apply(value);
              return value;
            },
            (error: unknown) => {
              if (isCurrentRequest(generation, authContext)) reject?.();
              throw error;
            },
          );
        }
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
          observe(getPracticeStats(), (value) => {
            const data = value || ({} as Record<string, number>);
            stats.value.todayCount = data.today_count ?? null;
            stats.value.totalCount = data.total_count ?? null;
            stats.value.correctCount = data.correct_count ?? null;
            stats.value.wrongCount = data.wrong_count ?? null;
            stats.value.accuracyRate = data.accuracy_rate ?? null;
            stats.value.recentCount7d = data.recent_count_7d ?? null;
          }),
          observe(courseStore.fetchCourses(), () => {
            stats.value.coursesCount = courseStore.courses.value.length;
          }),
          observe(getTodayReview(), (value) => {
            const data = value || ({} as Record<string, unknown>);
            review.value.dueCount = (data.due_count as number) ?? null;
            review.value.wrongCount = (data.wrong_count as number) ?? null;
            review.value.recommendedModes = Array.isArray(data.recommended_modes)
              ? (data.recommended_modes as string[])
              : [];
          }),
          observe(getWeakTypes(), (value) => {
            review.value.weakTypes = Array.isArray(value) ? (value.slice(0, 8) as WeakType[]) : [];
          }),
          observe(getDailyActivity(14), (value) => {
            activity.value = Array.isArray(value) ? value : [];
          }),
          observe(getTypeDistribution(), (value) => {
            typeDistribution.value = Array.isArray(value) ? value : [];
          }),
          observe(getTagAccuracy(), (value) => {
            tagAccuracy.value = Array.isArray(value) ? value.slice(0, 8) : [];
          }),
          observe(
            getStreak(),
            (value) => {
              streak.value = value;
              streakAvailable.value = true;
            },
            () => {
              streakAvailable.value = false;
            },
          ),
          observe(
            getTodayRecommendation(),
            (value) => {
              recommendation.value = value;
              recommendationAvailable.value = true;
            },
            () => {
              recommendationAvailable.value = false;
            },
          ),
          observe(getOwnerCourseAnalytics(), (value) => {
            courseAnalytics.value = Array.isArray(value) ? value.slice(0, 6) : [];
          }),
        ]);
        if (!isCurrentRequest(generation, authContext)) return;

        const hasSuccessfulResult = [
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
        ].some((result) => result.status === "fulfilled");
        if (hasSuccessfulResult) {
          hasLoaded.value = true;
          lastLoadedAt = Date.now();
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
        if (firstRejected && initialLoad) {
          errorMessage.value = getErrorMessage(
            (firstRejected as PromiseRejectedResult).reason,
            "学习数据更新失败，请稍后重试。",
          );
        } else if (hasSuccessfulResult) {
          errorMessage.value = "";
        }
      } catch (error: unknown) {
        if (initialLoad && isCurrentRequest(generation, authContext)) {
          errorMessage.value = getErrorMessage(error, "学习数据更新失败，请稍后重试。");
        }
      } finally {
        if (isCurrentRequest(generation, authContext)) {
          if (initialLoad) isInitialLoading.value = false;
          else isRefreshing.value = false;
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
    isInitialLoading,
    isRefreshing,
    hasLoaded,
    errorMessage,
    fetchAll,
  };
}
