import { beforeEach, describe, expect, it, vi } from "vitest";
import { useOfflineSync } from "../useOfflineSync";

describe("useOfflineSync", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("indexedDB", undefined);
    vi.stubGlobal("navigator", { onLine: true });
  });

  it("queues pending actions when IndexedDB is unavailable", async () => {
    const sync = useOfflineSync();

    await sync.enqueue({
      type: "practice_submit",
      payload: { question_id: 1, answer: "A" },
    });

    const pending = await sync.listPending();
    expect(pending).toHaveLength(1);
    expect(pending[0].type).toBe("practice_submit");
    expect(sync.pendingCount.value).toBe(1);
  });

  it("flushes queued actions after a handler succeeds", async () => {
    const sync = useOfflineSync();

    await sync.enqueue({ type: "bookmark", payload: { question_id: 2 } });
    const handled = vi.fn().mockResolvedValue(true);

    const result = await sync.flush(handled);

    expect(result.synced).toBe(1);
    expect(handled).toHaveBeenCalledWith(expect.objectContaining({ type: "bookmark" }));
    expect(await sync.listPending()).toHaveLength(0);
  });
});
