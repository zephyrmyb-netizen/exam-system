import { describe, expect, it, vi } from "vitest";

vi.mock("../api/request", () => ({
  default: { get: vi.fn() },
  getToken: () => "",
  clearToken: vi.fn(),
  setToken: vi.fn(),
  getErrorMessage: vi.fn(),
}));

import { interactionManifest } from "../interactionManifest";
import router from "../router";

describe("interaction manifest", () => {
  it("assigns every named route a user-visible interaction checklist", () => {
    const manifestRoutes = new Set(interactionManifest.map((entry) => entry.routeName));
    const namedRoutes = router.getRoutes().flatMap((route) => (typeof route.name === "string" ? [route.name] : []));

    expect(manifestRoutes).toEqual(new Set(namedRoutes));
  });

  it("keeps every interaction entry actionable and role-scoped", () => {
    for (const entry of interactionManifest) {
      expect(entry.roles.length, entry.routeName).toBeGreaterThan(0);
      expect(entry.actions.length, entry.routeName).toBeGreaterThan(0);
      expect(new Set(entry.actions).size, entry.routeName).toBe(entry.actions.length);
    }
  });
});
