import type { GroupResources, StudyGroup } from "@/types";
import request from "./request.ts";

export function getMyStudyGroups(): Promise<StudyGroup[]> {
  return request.get("/study-groups/mine").then(({ data }) => data as StudyGroup[]);
}

export function createStudyGroup(name: string): Promise<StudyGroup> {
  return request.post("/study-groups/", { name }).then(({ data }) => data as StudyGroup);
}

export function joinStudyGroup(code: string): Promise<StudyGroup> {
  return request.post(`/study-groups/join/${encodeURIComponent(code)}`).then(({ data }) => data as StudyGroup);
}

export function getStudyGroupResources(groupId: number): Promise<GroupResources> {
  return request.get(`/study-groups/${groupId}/resources`).then(({ data }) => data as GroupResources);
}

export function shareCourseToGroup(groupId: number, courseId: number): Promise<void> {
  return request.post(`/study-groups/${groupId}/courses/${courseId}`);
}

export function shareExamToGroup(groupId: number, examId: number): Promise<void> {
  return request.post(`/study-groups/${groupId}/exams/${examId}`);
}
