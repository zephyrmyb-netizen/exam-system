import request from "./request.ts";

export interface AdminUser {
  id: number;
  username: string;
  role: string;
}

export interface AdminUserList {
  items: AdminUser[];
  total: number;
}

export interface AdminStats {
  user_count: number;
  course_count: number;
  question_count: number;
  exam_count: number;
  submission_count: number;
}

export type FeedbackStatus = "new" | "in_progress" | "resolved";

export interface AdminFeedback {
  id: number;
  user_id: number;
  username: string;
  display_name: string;
  category: string;
  content: string;
  contact: string;
  status: FeedbackStatus;
  admin_reply: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminFeedbackList {
  items: AdminFeedback[];
  total: number;
}

export function listAdminUsers(): Promise<AdminUserList> {
  return request.get("/admin/users").then(({ data }) => data as AdminUserList);
}

export function updateAdminUserRole(userId: number, role: string): Promise<AdminUser> {
  return request.patch(`/admin/users/${userId}/role`, { role }).then(({ data }) => data as AdminUser);
}

export function getAdminStats(): Promise<AdminStats> {
  return request.get("/admin/stats").then(({ data }) => data as AdminStats);
}

export function listAdminFeedback(status?: FeedbackStatus): Promise<AdminFeedbackList> {
  return request
    .get("/admin/feedback", { params: status ? { status } : undefined })
    .then(({ data }) => data as AdminFeedbackList);
}

export function updateAdminFeedback(
  feedbackId: number,
  payload: Pick<AdminFeedback, "status" | "admin_reply">,
): Promise<AdminFeedback> {
  return request.patch(`/admin/feedback/${feedbackId}`, payload).then(({ data }) => data as AdminFeedback);
}
