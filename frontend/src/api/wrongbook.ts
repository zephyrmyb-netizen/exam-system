import type { Question, WrongRecord, QuestionMeta } from "@/types";
import request from "./request.ts";

export function getWrongBookMeta(): Promise<QuestionMeta> {
  return request.get("/wrongbook/meta").then(({ data }) => data as QuestionMeta);
}

export function getWrongBook(
  params?: Record<string, string | number>,
): Promise<WrongRecord[] | { total: number; items: WrongRecord[] }> {
  return request.get("/wrongbook/", { params }).then(({ data }) => data);
}

/** Build a complete, stable question list for a course's wrong-answer practice. */
export async function getCourseWrongPracticeQuestions(courseId: number): Promise<Question[]> {
  const data = await getWrongBook();
  const records = Array.isArray(data) ? data : data.items;
  return records
    .map((record) => record.question)
    .filter((question): question is Question => Boolean(question) && question.course_id === courseId);
}

export function removeWrongItem(questionId: number): Promise<void> {
  return request.delete(`/wrongbook/${questionId}`);
}
