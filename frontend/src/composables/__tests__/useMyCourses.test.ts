import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getMyCourses: vi.fn(),
  getToken: vi.fn(),
}));

vi.mock("../../api/courses", () => ({
  getMyCourses: mocks.getMyCourses,
}));

vi.mock("../../api/request", () => ({
  getToken: mocks.getToken,
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
}));

import { resetMyCoursesCache, useMyCourses } from "../useMyCourses";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe("useMyCourses", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getToken.mockReturnValue("account-a");
    mocks.getMyCourses.mockResolvedValue([{ id: 1, name: "机器学习" }]);
    resetMyCoursesCache();
  });

  it("reuses the current account course snapshot when a tab is revisited", async () => {
    const firstPage = useMyCourses();

    await firstPage.fetchCourses();

    const revisitedPage = useMyCourses();
    await revisitedPage.fetchCourses();

    expect(mocks.getMyCourses).toHaveBeenCalledTimes(1);
    expect(revisitedPage.courses.value).toEqual([{ id: 1, name: "机器学习" }]);
    expect(revisitedPage.hasLoaded.value).toBe(true);
    expect(revisitedPage.loading.value).toBe(false);
  });

  it("keeps the previous courses visible while a stale snapshot refreshes", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-16T00:00:00.000Z"));
    const refresh = deferred<Array<{ id: number; name: string }>>();
    mocks.getMyCourses
      .mockResolvedValueOnce([{ id: 1, name: "机器学习" }])
      .mockImplementationOnce(() => refresh.promise);

    const initialPage = useMyCourses();
    await initialPage.fetchCourses();

    vi.setSystemTime(new Date("2026-07-16T00:00:31.000Z"));
    const revisitedPage = useMyCourses();
    const refreshRequest = revisitedPage.fetchCourses();

    expect(revisitedPage.courses.value).toEqual([{ id: 1, name: "机器学习" }]);
    expect(revisitedPage.loading.value).toBe(false);
    expect(revisitedPage.isInitialLoading.value).toBe(false);
    expect(revisitedPage.isRefreshing.value).toBe(true);

    refresh.resolve([{ id: 2, name: "深度学习" }]);
    await refreshRequest;

    expect(revisitedPage.courses.value).toEqual([{ id: 2, name: "深度学习" }]);
    expect(revisitedPage.isRefreshing.value).toBe(false);
    vi.useRealTimers();
  });
});
