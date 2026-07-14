import type { Bookmark, BookmarkList } from "@/types";
import request from "./request";

export function listBookmarks(folder?: string): Promise<BookmarkList> {
  const params = folder ? { folder } : {};
  return request.get("/bookmarks/", { params }).then(({ data }) => data);
}

export function addBookmark(questionId: number, folderName = "Default", note = ""): Promise<Bookmark> {
  return request
    .post("/bookmarks/", { question_id: questionId, folder_name: folderName, note })
    .then(({ data }) => data);
}

export function removeBookmark(questionId: number): Promise<void> {
  return request.delete(`/bookmarks/${questionId}`).then(() => undefined);
}
