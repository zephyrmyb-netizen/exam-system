import type {
  Exam,
  ExamAttempt,
  ExamCreate,
  ExamDetail,
  ExamLeaderboard,
  ExamResult,
  ExamSubmissionCreate,
  PaginatedResponse,
} from "@/types";
import request from "./request.ts";

export function listExams(params?: Record<string, string | number>): Promise<PaginatedResponse<Exam>> {
  return request.get("/exams/", { params }).then(({ data }) => data as PaginatedResponse<Exam>);
}

export function listMyExams(params?: Record<string, string | number>): Promise<PaginatedResponse<Exam>> {
  return request.get("/exams/mine", { params }).then(({ data }) => data as PaginatedResponse<Exam>);
}

export function getExamDetail(id: number): Promise<ExamDetail> {
  return request.get(`/exams/${id}`).then(({ data }) => data as ExamDetail);
}

export function createExam(payload: ExamCreate): Promise<Exam> {
  return request.post("/exams/", payload).then(({ data }) => data as Exam);
}

export function publishExam(id: number): Promise<Exam> {
  return request.post(`/exams/${id}/publish`).then(({ data }) => data as Exam);
}

export function startExam(id: number): Promise<ExamAttempt> {
  return request.post(`/exams/${id}/start`).then(({ data }) => data as ExamAttempt);
}

export function submitExam(id: number, payload: ExamSubmissionCreate): Promise<ExamResult> {
  return request.post(`/exams/${id}/submit`, payload).then(({ data }) => data as ExamResult);
}

export function getExamLeaderboard(id: number): Promise<ExamLeaderboard> {
  return request.get(`/exams/${id}/leaderboard`).then(({ data }) => data as ExamLeaderboard);
}
