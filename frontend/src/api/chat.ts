import type { ChatRequest, ChatResponse, ChatMessage } from "@/types";
import request from "./request.ts";

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
