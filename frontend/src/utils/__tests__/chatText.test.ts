import { describe, expect, it } from "vitest";

import { normalizeChatReply } from "../chatText";

describe("normalizeChatReply", () => {
  it("removes markdown markers from assistant replies", () => {
    expect(
      normalizeChatReply("你好！比如： - **拆解某道题目** - **总结重点**"),
    ).toBe("你好！比如：\n• 拆解某道题目\n• 总结重点");
  });

  it("keeps plain text readable without rendering html", () => {
    expect(normalizeChatReply("## 重点\n请记住 `TCP` 和 __UDP__。")).toBe(
      "重点\n请记住 TCP 和 UDP。",
    );
  });
});
