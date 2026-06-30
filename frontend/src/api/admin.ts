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

export function listAdminUsers(): Promise<AdminUserList> {
  return request.get("/admin/users").then(({ data }) => data as AdminUserList);
}

export function updateAdminUserRole(userId: number, role: string): Promise<AdminUser> {
  return request.patch(`/admin/users/${userId}/role`, { role }).then(({ data }) => data as AdminUser);
}

export function getAdminStats(): Promise<AdminStats> {
  return request.get("/admin/stats").then(({ data }) => data as AdminStats);
}
