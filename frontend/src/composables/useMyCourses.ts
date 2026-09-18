import { ref, type Ref } from "vue";

import { getMyCourses } from "../api/courses";
import { getErrorMessage, getToken } from "../api/request";
import type { Course } from "../types";

const CACHE_TTL_MS = 30_000;

export interface UseMyCoursesReturn {
  courses: Ref<Course[]>;
  /** @deprecated Use isInitialLoading for new callers. */
  loading: Ref<boolean>;
  isInitialLoading: Ref<boolean>;
  isRefreshing: Ref<boolean>;
  hasLoaded: Ref<boolean>;
  errorMessage: Ref<string>;
  fetchCourses: (options?: { force?: boolean }) => Promise<void>;
}

const courses = ref<Course[]>([]);
const isInitialLoading = ref(false);
const loading = isInitialLoading;
const isRefreshing = ref(false);
const hasLoaded = ref(false);
const errorMessage = ref("");

let generation = 0;
let activeAuthContext: string | null = null;
let lastLoadedAt = 0;
let activeRequest: Promise<void> | null = null;
let activeRequestContext: string | null = null;

export function resetMyCoursesCache(): void {
  generation += 1;
  courses.value = [];
  isInitialLoading.value = false;
  isRefreshing.value = false;
  hasLoaded.value = false;
  errorMessage.value = "";
  lastLoadedAt = 0;
  activeRequest = null;
  activeRequestContext = null;
  activeAuthContext = null;
}

function isCurrentRequest(authContext: string): boolean {
  return authContext === activeAuthContext && getToken() === authContext;
}

export function useMyCourses(): UseMyCoursesReturn {
  async function fetchCourses(options: { force?: boolean } = {}): Promise<void> {
    const authContext = getToken();
    if (authContext !== activeAuthContext) {
      resetMyCoursesCache();
      activeAuthContext = authContext;
    }

    if (!options.force && hasLoaded.value && Date.now() - lastLoadedAt < CACHE_TTL_MS) return;
    if (activeRequest && activeRequestContext === authContext) return activeRequest;

    const requestGeneration = ++generation;
    const isCurrent = () => requestGeneration === generation && isCurrentRequest(authContext);
    const initialLoad = !hasLoaded.value;
    if (initialLoad) isInitialLoading.value = true;
    else isRefreshing.value = true;
    if (initialLoad) errorMessage.value = "";

    const request = (async () => {
      try {
        const nextCourses = await getMyCourses();
        if (!isCurrent()) return;
        courses.value = nextCourses;
        hasLoaded.value = true;
        lastLoadedAt = Date.now();
      } catch (error: unknown) {
        if (initialLoad && isCurrent()) {
          errorMessage.value = getErrorMessage(error, "获取题库失败");
        }
      } finally {
        if (isCurrent()) {
          if (initialLoad) isInitialLoading.value = false;
          else isRefreshing.value = false;
          activeRequest = null;
          activeRequestContext = null;
        }
      }
    })();

    activeRequest = request;
    activeRequestContext = authContext;
    return request;
  }

  return {
    courses,
    loading,
    isInitialLoading,
    isRefreshing,
    hasLoaded,
    errorMessage,
    fetchCourses,
  };
}
