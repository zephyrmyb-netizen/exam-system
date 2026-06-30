import type { ChatRequest, ChatResponse, ChatMessage } from "@/types";
import request, { getToken, getErrorMessage } from "./request.ts";

export function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
): Promise<ChatResponse> {
  return request.post(
    "/chat/",
    { message, history } satisfies ChatRequest,
    { timeout: 90000 },
  ).then(({ data }) => data as ChatResponse);
}

/**
 * 流式发送聊天消息（SSE）。
 *
 * 调用 `onDelta` 接收增量文本片段；`onDone` 在流结束时回调（已拼接的完整文本）；
 * `onError` 在出错时回调（错误消息）。流式失败时调用方可改用 `sendChatMessage` 回退。
 *
 * 返回一个 `abort()` 函数，调用即可中断流（用户离开页面/取消发送时使用）。
 */
export function streamChatMessage(
  message: string,
  history: ChatMessage[] = [],
  handlers: {
    onDelta: (delta: string) => void;
    onDone: (fullText: string) => void;
    onError: (msg: string) => void;
  },
): { abort: () => void } {
  const controller = new AbortController();
  const token = getToken();
  let full = "";

  (async () => {
    try {
      const resp = await fetch("/chat/stream", {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, history } satisfies ChatRequest),
      });

      if (!resp.ok) {
        // 4xx/5xx —— 提取 detail 或状态码文案，给调用方回退机会
        let detail = "";
        try {
          const data = await resp.json();
          detail = typeof data?.detail === "string" ? data.detail : "";
        } catch {
          // 非 JSON 响应
        }
        handlers.onError(detail || `请求失败（${resp.status}）`);
        return;
      }

      if (!resp.body) {
        handlers.onError("当前浏览器不支持流式响应，已自动切换为普通模式。");
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE 帧以双换行分隔，按 \n\n 拆分；最后一个可能不完整，留在 buffer
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || "";
        for (const frame of frames) {
          const line = frame.trim();
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (payload === "[DONE]") {
            handlers.onDone(full);
            return;
          }
          try {
            const obj = JSON.parse(payload);
            if (typeof obj.delta === "string") {
              full += obj.delta;
              handlers.onDelta(obj.delta);
            } else if (typeof obj.error === "string") {
              handlers.onError(obj.error);
              return;
            }
          } catch {
            // 忽略无法解析的帧
          }
        }
      }
      // 流自然结束但未收到 [DONE] —— 仍视为完成
      handlers.onDone(full);
    } catch (err: any) {
      if (controller.signal.aborted) return;
      handlers.onError(getErrorMessage(err, "AI 回复失败，请稍后重试"));
    }
  })();

  return { abort: () => controller.abort() };
}
