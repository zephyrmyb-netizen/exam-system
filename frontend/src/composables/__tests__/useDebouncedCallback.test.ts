import { describe, expect, it, vi } from "vitest";

import { useDebouncedCallback } from "../useDebouncedCallback";

describe("useDebouncedCallback", () => {
  it("only runs the latest scheduled callback after the delay", async () => {
    vi.useFakeTimers();
    const callback = vi.fn();
    const { schedule } = useDebouncedCallback(callback, 240);

    schedule("first");
    schedule("latest");
    await vi.advanceTimersByTimeAsync(239);

    expect(callback).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith("latest");
    vi.useRealTimers();
  });
});
