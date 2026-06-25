/**
 * Practice-related API calls → /practice/*
 */
import type { SubmitRequest, SubmitResponse, PracticeStats, PracticeRecord, PaginatedResponse, Question, TodayReview, WeakType } from "@/types";
import request from "./request.ts";

function practiceGet<T>(url: string, params?: Record<string, string | number>): Promise<T> {
  return request.get(url, { params }).then(({ data }) => data as T);
}

function practicePost<T>(url: string, payload: unknown): Promise<T> {
  return request.post(url, payload).then(({ data }) => data as T);
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
  return practicePost<SubmitResponse>("/practice/submit", payload);
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
