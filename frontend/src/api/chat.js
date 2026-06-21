import request from "./request";

export async function sendChatMessage(message, history = []) {
  const { data } = await request.post(
    "/chat/",
    { message, history },
    { timeout: 90000 }
  );
  return data;
}
