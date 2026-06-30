import { beforeEach, describe, expect, it, vi } from "vitest";

const postMock = vi.fn();

vi.mock("../request.ts", () => ({
  default: {
    post: postMock,
  },
}));

describe("practice offline queue", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
    postMock.mockReset();
    vi.stubGlobal("indexedDB", undefined);
  });

  it("queues practice submissions instead of dropping them while offline", async () => {
    vi.stubGlobal("navigator", { onLine: false });
    const { submitPracticeAnswer } = await import("../practice.ts");
    const { useOfflineSync } = await import("../../composables/useOfflineSync.ts");

    await expect(
      submitPracticeAnswer({
        question_id: 7,
        user_answer: "A",
      }),
    ).rejects.toThrow("离线");

    const pending = await useOfflineSync().listPending();
    expect(postMock).not.toHaveBeenCalled();
    expect(pending).toHaveLength(1);
    expect(pending[0]).toMatchObject({
      type: "practice_submit",
      payload: { question_id: 7, user_answer: "A" },
    });
  });

  it("flushes pending practice submissions when the network is available", async () => {
    vi.stubGlobal("navigator", { onLine: true });
    postMock.mockResolvedValue({ data: { is_correct: true, correct_answer: "A", analysis: "", wrongbook_recorded: false } });

    const { flushPendingPracticeSubmissions } = await import("../practice.ts");
    const { useOfflineSync } = await import("../../composables/useOfflineSync.ts");

    await useOfflineSync().enqueue({
      type: "practice_submit",
      payload: { question_id: 9, user_answer: "B" },
    });

    const result = await flushPendingPracticeSubmissions();

    expect(result).toEqual({ synced: 1, failed: 0 });
    expect(postMock).toHaveBeenCalledWith("/practice/submit", { question_id: 9, user_answer: "B" });
    expect(await useOfflineSync().listPending()).toHaveLength(0);
  });
});
