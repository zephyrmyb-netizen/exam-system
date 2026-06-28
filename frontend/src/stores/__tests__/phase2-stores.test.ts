import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useCourseStore } from "../course";
import { useThemeStore } from "../theme";
import { useUiStore } from "../ui";

vi.mock("@/api/request", () => ({
  default: {
    get: vi.fn(async () => ({
      data: [
        { id: 1, owner_id: 1, name: "Java", visibility: "private" },
      ],
    })),
  },
}));

describe("phase2 stores", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("course store loads and caches my courses", async () => {
    const store = useCourseStore();
    const items = await store.fetchMine();
    expect(items).toHaveLength(1);
    expect(store.items[0].name).toBe("Java");
    expect(store.lastLoadedAt).toBeGreaterThan(0);
  });

  it("theme store toggles the dark class and persists the mode", () => {
    const theme = useThemeStore();
    theme.init();
    theme.toggle();
    expect(theme.mode).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(window.localStorage.getItem("xuexibao-theme")).toBe("dark");
  });

  it("ui store tracks sidebar and global loading", () => {
    const ui = useUiStore();
    ui.toggleSidebar();
    ui.setGlobalLoading(true);
    expect(ui.sidebarOpen).toBe(true);
    expect(ui.globalLoading).toBe(true);
  });
});
