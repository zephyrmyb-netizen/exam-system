import { beforeEach, describe, expect, it, vi } from "vitest";

import { useStudyOverview } from "../useStudyOverview";

const mocks = vi.hoisted(() => ({
  getPracticeStats: vi.fn(),
  getTodayReview: vi.fn(),
  getWeakTypes: vi.fn(),
  getDailyActivity: vi.fn(),
  getStreak: vi.fn(),
  getTagAccuracy: vi.fn(),
  getTeacherCourseAnalytics: vi.fn(),
  getTodayRecommendation: vi.fn(),
  getTypeDistribution: vi.fn(),
  getToken: vi.fn(),
  requestGet: vi.fn(),
}));

vi.mock("../../api/practice", () => ({
  getPracticeStats: mocks.getPracticeStats,
  getTodayReview: mocks.getTodayReview,
  getWeakTypes: mocks.getWeakTypes,
}));

vi.mock("../../api/analytics", () => ({
  getDailyActivity: mocks.getDailyActivity,
  getStreak: mocks.getStreak,
  getTagAccuracy: mocks.getTagAccuracy,
  getTeacherCourseAnalytics: mocks.getTeacherCourseAnalytics,
  getTodayRecommendation: mocks.getTodayRecommendation,
  getTypeDistribution: mocks.getTypeDistribution,
}));

vi.mock("../../api/request", () => ({
  default: { get: mocks.requestGet },
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
  getToken: mocks.getToken,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((next) => {
    resolve = next;
  });
  return { promise, resolve };
}

const recommendation = {
  weak_tags: [],
  weak_types: [],
  due_count: 0,
  due_question_ids: [],
  recommended_modes: ["random_practice"],
};

describe("useStudyOverview result availability", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getToken.mockReturnValue("account-a");
    mocks.getPracticeStats.mockResolvedValue({
      today_count: 3,
      total_count: 10,
      correct_count: 8,
      wrong_count: 2,
      accuracy_rate: 0.8,
      recent_count_7d: 5,
    });
    mocks.requestGet.mockResolvedValue({ data: [] });
    mocks.getTodayReview.mockResolvedValue({ due_count: 0, wrong_count: 0, recommended_modes: [] });
    mocks.getWeakTypes.mockResolvedValue([]);
    mocks.getDailyActivity.mockResolvedValue([]);
    mocks.getTypeDistribution.mockResolvedValue([]);
    mocks.getTagAccuracy.mockResolvedValue([]);
    mocks.getStreak.mockResolvedValue({ current_streak: 0, longest_streak: 0, last_practiced_date: null });
    mocks.getTodayRecommendation.mockResolvedValue(recommendation);
    mocks.getTeacherCourseAnalytics.mockResolvedValue([]);
  });

  it("tracks successful zero streak and recommendation independently from their values", async () => {
    const overview = useStudyOverview();
    const pending = overview.fetchAll();

    expect(overview.streakAvailable.value).toBeNull();
    expect(overview.recommendationAvailable.value).toBeNull();
    await pending;

    expect(overview.streakAvailable.value).toBe(true);
    expect(overview.streak.value.current_streak).toBe(0);
    expect(overview.recommendationAvailable.value).toBe(true);
    expect(overview.recommendation.value).toEqual(recommendation);
  });

  it("marks only rejected streak and recommendation requests unavailable", async () => {
    mocks.getStreak.mockRejectedValue(new Error("streak failed"));
    mocks.getTodayRecommendation.mockRejectedValue(new Error("recommendation failed"));
    const overview = useStudyOverview();

    await overview.fetchAll();

    expect(overview.streakAvailable.value).toBe(false);
    expect(overview.recommendationAvailable.value).toBe(false);
    expect(overview.stats.value.todayCount).toBe(3);
    expect(overview.errorMessage.value).not.toBe("");
  });

  it("distinguishes a fulfilled empty recommendation from a request failure", async () => {
    mocks.getTodayRecommendation.mockResolvedValue(null);
    mocks.getDailyActivity.mockRejectedValue(new Error("activity failed"));
    const overview = useStudyOverview();

    await overview.fetchAll();

    expect(overview.streakAvailable.value).toBe(true);
    expect(overview.recommendationAvailable.value).toBe(true);
    expect(overview.recommendation.value).toBeNull();
    expect(overview.errorMessage.value).not.toBe("");
  });

  it("starts a fresh request for a new auth context and ignores the prior delayed response", async () => {
    const accountA = deferred<{ today_count: number; total_count: number }>();
    const accountB = deferred<{ today_count: number; total_count: number }>();
    mocks.getPracticeStats
      .mockImplementationOnce(() => accountA.promise)
      .mockImplementationOnce(() => accountB.promise);
    const overview = useStudyOverview();

    const accountARequest = overview.fetchAll();
    expect(mocks.getPracticeStats).toHaveBeenCalledTimes(1);

    mocks.getToken.mockReturnValue("account-b");
    const accountBRequest = overview.fetchAll();
    expect(mocks.getPracticeStats).toHaveBeenCalledTimes(2);
    expect(overview.stats.value.todayCount).toBeNull();

    accountB.resolve({ today_count: 22, total_count: 220 });
    await accountBRequest;
    expect(overview.stats.value.todayCount).toBe(22);
    expect(overview.stats.value.totalCount).toBe(220);
    expect(overview.loading.value).toBe(false);

    accountA.resolve({ today_count: 11, total_count: 110 });
    await accountARequest;
    expect(overview.stats.value.todayCount).toBe(22);
    expect(overview.stats.value.totalCount).toBe(220);
    expect(overview.streakAvailable.value).toBe(true);
    expect(overview.recommendationAvailable.value).toBe(true);
    expect(overview.loading.value).toBe(false);
  });
});
