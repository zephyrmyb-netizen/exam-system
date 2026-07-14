import { afterEach, describe, expect, it } from "vitest";

import { MOBILE_VIEWPORT_CONTENT, applyMobileViewportPolicy } from "../viewport";

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
});
