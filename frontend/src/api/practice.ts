/**
 * Practice-related API calls → /practice/*
 */
import type { SubmitRequest, SubmitResponse, PracticeStats, PracticeRecord, PaginatedResponse, Question, TodayReview, WeakType } from "@/types";
import { useOfflineSync, type PendingOfflineAction } from "@/composables/useOfflineSync";
import request from "./request.ts";

const PRACTICE_SUBMIT_ACTION = "practice_submit";

class OfflinePracticeSubmitError extends Error {
  userMessage = "离线提交已保存，联网后会自动同步。";

  constructor() {
    super("离线提交已保存，联网后会自动同步。");
    this.name = "OfflinePracticeSubmitError";
  }
}

function practiceGet<T>(url: string, params?: Record<string, string | number>): Promise<T> {
  return request.get(url, { params }).then(({ data }) => data as T);
}

function practicePost<T>(url: string, payload: unknown): Promise<T> {
  return request.post(url, payload).then(({ data }) => data as T);
}

function isOfflineLikeError(error: unknown): boolean {
  const maybeError = error as { response?: unknown; code?: string } | undefined;
  return !maybeError?.response && (maybeError?.code === "ERR_NETWORK" || maybeError?.code === "ECONNABORTED");
}

function isBrowserOffline(): boolean {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

async function queuePracticeSubmit(payload: SubmitRequest): Promise<void> {
  await useOfflineSync().enqueue({
    type: PRACTICE_SUBMIT_ACTION,
    payload,
  });
}

async function replayPracticeSubmit(action: Required<PendingOfflineAction>): Promise<boolean> {
  if (action.type !== PRACTICE_SUBMIT_ACTION) return false;
  await practicePost<SubmitResponse>("/practice/submit", action.payload);
  return true;
}

export async function flushPendingPracticeSubmissions() {
  return useOfflineSync().flush(replayPracticeSubmit);
}

function triggerPracticeQueueFlush(): void {
  if (!isBrowserOffline()) {
    void flushPendingPracticeSubmissions();
  }
}

export function getPracticeStats(): Promise<PracticeStats> {
  return practiceGet<PracticeStats>("/practice/stats");
}

export function getPracticeHistory(params?: Record<string, string | number>): Promise<PaginatedResponse<PracticeRecord>> {
  return practiceGet<PaginatedResponse<PracticeRecord>>("/practice/history", params);
}

export function getRandomPracticeQuestion(params?: Record<string, string | number>): Promise<Question> {
  return practiceGet<Question>("/practice/random", params);
}

export function submitPracticeAnswer(payload: SubmitRequest): Promise<SubmitResponse> {
  if (isBrowserOffline()) {
    return queuePracticeSubmit(payload).then(() => Promise.reject(new OfflinePracticeSubmitError()));
  }

  return practicePost<SubmitResponse>("/practice/submit", payload)
    .then((data) => {
      triggerPracticeQueueFlush();
      return data;
    })
    .catch(async (error) => {
      if (isOfflineLikeError(error)) {
        await queuePracticeSubmit(payload);
        throw new OfflinePracticeSubmitError();
      }
      throw error;
    });
}

export function getTodayReview(): Promise<TodayReview> {
  return practiceGet<TodayReview>("/practice/review/today");
}

export function getWeakTypes(): Promise<WeakType[]> {
  return practiceGet<WeakType[]>("/practice/insights/weak-types");
}

export function getReviewWrongQuestion(params?: Record<string, string | number>): Promise<Question> {
  return practiceGet<Question>("/practice/review/wrong", params);
}

export function getReviewDueQuestion(params?: Record<string, string | number>): Promise<Question> {
  return practiceGet<Question>("/practice/review/due", params);
}

export function getLearningStats(): Promise<PracticeStats> {
  return getPracticeStats();
}

if (typeof window !== "undefined") {
  window.addEventListener("online", triggerPracticeQueueFlush);
  window.addEventListener("focus", triggerPracticeQueueFlush);
  setTimeout(triggerPracticeQueueFlush, 0);
}
