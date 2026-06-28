import { defineStore } from "pinia";

export type ThemeMode = "light" | "dark";

const STORAGE_KEY = "xuexibao-theme";

export const useThemeStore = defineStore("theme", {
  state: () => ({
    mode: "light" as ThemeMode,
  }),
  actions: {
    init(): void {
      const saved = window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
      this.setMode(saved === "dark" ? "dark" : "light");
    },
    setMode(mode: ThemeMode): void {
      this.mode = mode;
      document.documentElement.classList.toggle("dark", mode === "dark");
      window.localStorage.setItem(STORAGE_KEY, mode);
    },
    toggle(): void {
      this.setMode(this.mode === "dark" ? "light" : "dark");
    },
  },
});
