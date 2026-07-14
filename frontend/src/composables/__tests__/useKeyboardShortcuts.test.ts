import { describe, expect, it, vi } from "vitest";
import { useKeyboardShortcuts } from "../useKeyboardShortcuts";

describe("useKeyboardShortcuts", () => {
  it("calls handlers on matching navigation keys", () => {
    const next = vi.fn();
    const prev = vi.fn();
    const shortcuts = useKeyboardShortcuts({ next, prev });

    shortcuts.bind();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
    shortcuts.unbind();

    expect(next).toHaveBeenCalledTimes(1);
    expect(prev).toHaveBeenCalledTimes(1);
  });

  it("ignores navigation keys while typing", () => {
    const next = vi.fn();
    const shortcuts = useKeyboardShortcuts({ next });
    const input = document.createElement("input");
    document.body.appendChild(input);

    shortcuts.bind();
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    shortcuts.unbind();
    document.body.removeChild(input);

    expect(next).not.toHaveBeenCalled();
  });
});
