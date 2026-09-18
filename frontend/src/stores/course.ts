import { defineStore } from "pinia";

import { getMyCourses } from "@/api/courses";
import type { Course } from "@/types";

const CACHE_TTL_MS = 30_000;

export const useCourseStore = defineStore("course", {
  state: () => ({
    items: [] as Course[],
    loading: false,
    error: "",
    lastLoadedAt: 0,
  }),
  getters: {
    isStale: (state) => Date.now() - state.lastLoadedAt > CACHE_TTL_MS,
  },
  actions: {
    async fetchMine(options: { force?: boolean } = {}): Promise<Course[]> {
      if (!options.force && this.items.length > 0 && !this.isStale) {
        return this.items;
      }
      this.loading = true;
      this.error = "";
      try {
        this.items = await getMyCourses();
        this.lastLoadedAt = Date.now();
        return this.items;
      } catch (error: any) {
        this.error = error?.userMessage || "课程加载失败";
        throw error;
      } finally {
        this.loading = false;
      }
    },
    invalidate(): void {
      this.lastLoadedAt = 0;
    },
  },
});
