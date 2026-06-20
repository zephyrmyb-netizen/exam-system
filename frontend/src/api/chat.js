/**
 * AI Chat API calls — /chat/
 */
import request from "./request";

/**
 * Send a message to the AI chat assistant and get a reply.
 * @param {string} message - The user's message
 * @returns {Promise<Object>} { reply, ... }
 */
export async function sendChatMessage(message) {
  const { data } = await request.post("/chat/", { message });
  return data;
}
