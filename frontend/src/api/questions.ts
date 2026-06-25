import type { Question, QuestionCreate, QuestionUpdate, QuestionMeta } from "@/types";
import request from "./request.ts";

export function getQuestionsMeta(): Promise<QuestionMeta> {
  return request.get("/questions/meta").then(({ data }) => data as QuestionMeta);
}

export function getQuestions(params?: Record<string, string | number>): Promise<Question[] | { total: number; items: Question[] }> {
  return request.get("/questions/", { params }).then(({ data }) => data);
}

export function createQuestion(payload: QuestionCreate): Promise<Question> {
  return request.post("/questions/", payload).then(({ data }) => data as Question);
}

export function updateQuestion(id: number, payload: QuestionUpdate): Promise<Question> {
  return request.patch(`/questions/${id}`, payload).then(({ data }) => data as Question);
}

export function batchCreateQuestions(
  items: QuestionCreate[],
  params?: Record<string, string | number>,
): Promise<{ imported_count: number; course_id: number | null; course_name: string }> {
  return request.post("/questions/batch", items, { params }).then(({ data }) => data);
}

export function deleteQuestion(id: number): Promise<void> {
  return request.delete(`/questions/${id}`);
}

export function publishQuestion(id: number): Promise<Question> {
  return request.post(`/questions/${id}/publish`).then(({ data }) => data as Question);
}

export function unpublishQuestion(id: number): Promise<Question> {
  return request.post(`/questions/${id}/unpublish`).then(({ data }) => data as Question);
}
