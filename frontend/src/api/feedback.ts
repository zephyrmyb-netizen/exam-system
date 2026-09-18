import request from "./request";

export type FeedbackCategory = "bug" | "suggestion" | "question" | "other" | "diagnostic";

export interface FeedbackSubmission {
  id: number;
  category: FeedbackCategory;
  content: string;
  contact: string;
  created_at: string | null;
}

export function submitFeedback(payload: {
  category: FeedbackCategory;
  content: string;
  contact?: string;
}): Promise<FeedbackSubmission> {
  return request.post("/feedback/", payload).then(({ data }) => data as FeedbackSubmission);
}
