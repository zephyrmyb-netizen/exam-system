import type { WrongRecord, QuestionMeta } from "@/types";
import request from "./request.ts";

export function getWrongBookMeta(): Promise<QuestionMeta> {
  return request.get("/wrongbook/meta").then(({ data }) => data as QuestionMeta);
}

export function getWrongBook(
  params?: Record<string, string | number>,
): Promise<WrongRecord[] | { total: number; items: WrongRecord[] }> {
  return request.get("/wrongbook/", { params }).then(({ data }) => data);
}

export function removeWrongItem(questionId: number): Promise<void> {
  return request.delete(`/wrongbook/${questionId}`);
}
