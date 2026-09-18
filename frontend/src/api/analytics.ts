import type {
  CourseAnalytics,
  ExamAnalytics,
  DailyActivity,
  ScoreBucket,
  Streak,
  TagAccuracy,
  TodayRecommendation,
  TypeDistribution,
} from "@/types";
import request from "./request";

export function getDailyActivity(days = 30): Promise<DailyActivity[]> {
  return request.get("/analytics/daily-activity", { params: { days } }).then(({ data }) => data);
}

export function getTypeDistribution(): Promise<TypeDistribution[]> {
  return request.get("/analytics/type-distribution").then(({ data }) => data);
}

export function getStreak(): Promise<Streak> {
  return request.get("/analytics/streak").then(({ data }) => data);
}

export function getTagAccuracy(): Promise<TagAccuracy[]> {
  return request.get("/tags/accuracy").then(({ data }) => data);
}

export function getTodayRecommendation(): Promise<TodayRecommendation> {
  return request.get("/recommendations/today").then(({ data }) => data);
}

export function getOwnerCourseAnalytics(): Promise<CourseAnalytics[]> {
  return request.get("/analytics/owner/courses").then(({ data }) => data);
}

export function getOwnerExamScoreDistribution(examId: number): Promise<ScoreBucket[]> {
  return request.get(`/analytics/owner/exam-scores/${examId}`).then(({ data }) => data);
}

export function getOwnerExamAnalytics(examId: number): Promise<ExamAnalytics> {
  return request.get(`/analytics/owner/exams/${examId}`).then(({ data }) => data as ExamAnalytics);
}
