import { describe, expect, it, vi } from "vitest";

const getMock = vi.fn(async (url: string) => ({ data: { url } }));

vi.mock("@/api/request", () => ({
  default: {
    get: getMock,
  },
}));

describe("phase4 analytics api", () => {
  it("calls the analytics endpoints used by the study dashboard", async () => {
    const {
      getDailyActivity,
      getTypeDistribution,
      getStreak,
      getTagAccuracy,
      getTodayRecommendation,
    } = await import("../analytics");

    await getDailyActivity(14);
    await getTypeDistribution();
    await getStreak();
    await getTagAccuracy();
    await getTodayRecommendation();

    expect(getMock).toHaveBeenNthCalledWith(1, "/analytics/daily-activity", { params: { days: 14 } });
    expect(getMock).toHaveBeenNthCalledWith(2, "/analytics/type-distribution");
    expect(getMock).toHaveBeenNthCalledWith(3, "/analytics/streak");
    expect(getMock).toHaveBeenNthCalledWith(4, "/tags/accuracy");
    expect(getMock).toHaveBeenNthCalledWith(5, "/recommendations/today");
  });
});
