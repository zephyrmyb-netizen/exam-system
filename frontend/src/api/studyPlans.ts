import type { StudyPlan } from "@/types";
import request from "./request.ts";

export interface StudyPlanUpdate {
  title: string;
  daily_target: number;
  deadline: string | null;
}

export function getCurrentStudyPlan(): Promise<StudyPlan | null> {
  return request.get("/study-plans/current").then(({ data }) => (data ?? null) as StudyPlan | null);
}

export function updateCurrentStudyPlan(payload: StudyPlanUpdate): Promise<StudyPlan> {
  return request.put("/study-plans/current", payload).then(({ data }) => data as StudyPlan);
}
