import { defineStore } from "pinia";

export type ThemeMode = "light" | "dark" | "system";

const STORAGE_KEY = "xuexibao-theme";

export const useThemeStore = defineStore("theme", {
  state: () => ({
    mode: "system" as ThemeMode,
    systemDark: false,
    systemListenerBound: false,
  }),
  getters: {
    isDark: (state): boolean => state.mode === "dark" || (state.mode === "system" && state.systemDark),
  },
  actions: {
    init(): void {
      let saved: string | null = null;
      try {
        saved = window.localStorage.getItem(STORAGE_KEY);
      } catch {
        /* Use system theme when storage is unavailable. */
      }
      const mode: ThemeMode = saved === "dark" || saved === "light" ? saved : "system";
      if (typeof window.matchMedia === "function") {
        const media = window.matchMedia("(prefers-color-scheme: dark)");
        this.systemDark = media.matches;
        if (!this.systemListenerBound) {
          const handleSystemChange = (event: MediaQueryListEvent) => {
            this.systemDark = event.matches;
            this.applyTheme();
          };
          if (media.addEventListener) {
            media.addEventListener("change", handleSystemChange);
          } else {
            media.addListener(handleSystemChange);
          }
          this.systemListenerBound = true;
        }
      }
      this.setMode(mode);
    },
    setMode(mode: ThemeMode): void {
      this.mode = mode;
      this.applyTheme();
      try {
        window.localStorage.setItem(STORAGE_KEY, mode);
      } catch {
        /* Theme remains usable in memory. */
      }
    },
    toggle(): void {
      this.setMode(this.isDark ? "light" : "dark");
    },
    applyTheme(): void {
      document.documentElement.classList.toggle("dark", this.isDark);
      document.querySelector('meta[name="theme-color"]')?.setAttribute("content", this.isDark ? "#000000" : "#f2f2f7");
    },
  },
});
