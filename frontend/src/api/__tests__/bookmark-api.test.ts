import { describe, expect, it, vi } from "vitest";

const getMock = vi.fn(async () => ({ data: { items: [], total: 0, folders: [] } }));
const postMock = vi.fn(async () => ({ data: { id: 1, question_id: 2 } }));
const deleteMock = vi.fn(async () => ({ data: {} }));

vi.mock("@/api/request", () => ({
  default: {
    get: getMock,
    post: postMock,
    delete: deleteMock,
  },
}));

describe("bookmark api", () => {
  it("calls backend bookmark endpoints", async () => {
    const { listBookmarks, addBookmark, removeBookmark } = await import("../bookmark");

    await listBookmarks("重点");
    await addBookmark(2, "重点", "复习");
    await removeBookmark(2);

    expect(getMock).toHaveBeenCalledWith("/bookmarks/", { params: { folder: "重点" } });
    expect(postMock).toHaveBeenCalledWith("/bookmarks/", { question_id: 2, folder_name: "重点", note: "复习" });
    expect(deleteMock).toHaveBeenCalledWith("/bookmarks/2");
  });
});
