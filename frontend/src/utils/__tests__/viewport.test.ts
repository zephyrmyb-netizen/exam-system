import { afterEach, describe, expect, it } from "vitest";

import { MOBILE_VIEWPORT_CONTENT, applyMobileViewportPolicy, syncMobileViewportScale } from "../viewport";

describe("mobile viewport policy", () => {
  afterEach(() => {
    document.querySelector('meta[name="viewport"]')?.remove();
  });

  it("creates or restores the fixed mobile viewport policy", () => {
    const staleMeta = document.createElement("meta");
    staleMeta.name = "viewport";
    staleMeta.content = "width=980";
    document.head.append(staleMeta);

    applyMobileViewportPolicy();

    expect(document.querySelector<HTMLMetaElement>('meta[name="viewport"]')?.content).toBe(MOBILE_VIEWPORT_CONTENT);
  });

  it("counter-scales the application when a WebView retains a zoomed visual viewport", () => {
    const descriptor = Object.getOwnPropertyDescriptor(window, "visualViewport");
    Object.defineProperty(window, "visualViewport", { value: { scale: 1.5 }, configurable: true });

    syncMobileViewportScale();

    expect(document.documentElement.classList.contains("viewport-scale-recovery")).toBe(true);
    expect(Number(document.documentElement.style.getPropertyValue("--viewport-recovery-scale"))).toBeCloseTo(1 / 1.5);

    if (descriptor) Object.defineProperty(window, "visualViewport", descriptor);
    else delete (window as unknown as { visualViewport?: VisualViewport }).visualViewport;
    document.documentElement.classList.remove("viewport-scale-recovery");
    document.documentElement.style.removeProperty("--viewport-recovery-scale");
  });
});
