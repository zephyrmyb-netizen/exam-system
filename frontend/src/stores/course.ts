import { defineStore } from "pinia";
import request from "@/api/request";

export interface CourseSummary {
  id: number;
  owner_id: number;
  name: string;
  description?: string;
  subject?: string;
  visibility: "private" | "public";
  question_count?: number;
  practice_count?: number;
  last_practiced_at?: string | null;
}

const CACHE_TTL_MS = 30_000;

export const useCourseStore = defineStore("course", {
  state: () => ({
    items: [] as CourseSummary[],
    loading: false,
    error: "",
    lastLoadedAt: 0,
  }),
  getters: {
    isStale: (state) => Date.now() - state.lastLoadedAt > CACHE_TTL_MS,
  },
  actions: {
    async fetchMine(options: { force?: boolean } = {}): Promise<CourseSummary[]> {
      if (!options.force && this.items.length > 0 && !this.isStale) {
        return this.items;
      }
      this.loading = true;
      this.error = "";
      try {
        const { data } = await request.get<CourseSummary[] | { items: CourseSummary[] }>("/courses/mine");
        this.items = Array.isArray(data) ? data : data.items;
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
