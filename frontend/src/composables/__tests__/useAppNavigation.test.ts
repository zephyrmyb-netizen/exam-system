import { reactive } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAppNavigation } from "../useAppNavigation";

const mocks = {
  replace: vi.fn(),
};

const route = reactive({ query: {} as Record<string, string> });

vi.mock("vue-router", () => ({
  useRouter: () => mocks,
  useRoute: () => route,
}));

describe("useAppNavigation", () => {
  beforeEach(() => {
    mocks.replace.mockReset();
    route.query = {};
  });

  it("always replaces and preserves an allowed source", () => {
    const navigation = useAppNavigation();

    navigation.replaceTo({ name: "courses" });
    navigation.replaceWithSource({ name: "study-overview" }, "home");

    expect(mocks.replace).toHaveBeenNthCalledWith(1, { name: "courses" });
    expect(mocks.replace).toHaveBeenNthCalledWith(2, { name: "study-overview", query: { from: "home" } });
  });

  it("falls back instead of trusting an invalid source", () => {
    route.query = { from: "unknown" };
    const navigation = useAppNavigation();

    navigation.returnToSource({ name: "mine" });
    navigation.replaceWithSource("/courses", "unknown");

    expect(mocks.replace).toHaveBeenNthCalledWith(1, { name: "mine" });
    expect(mocks.replace).toHaveBeenNthCalledWith(2, "/courses");
  });
});
