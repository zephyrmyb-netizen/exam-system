import { describe, expect, it } from "vitest";

import { normalizeChatReply, renderAssistantMarkdown } from "../chatText";

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

  it("renders safe assistant markdown without leaking raw markers", () => {
    expect(
      renderAssistantMarkdown("**拆解某道题目**\n- 先看 `条件`\n- 再排除<script>alert(1)</script>"),
    ).toBe(
      "<p><strong>拆解某道题目</strong></p><ul><li>先看 <code>条件</code></li><li>再排除&lt;script&gt;alert(1)&lt;/script&gt;</li></ul>",
    );
  });
});
