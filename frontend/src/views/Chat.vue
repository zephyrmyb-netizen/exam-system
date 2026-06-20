<script setup>
import { computed, nextTick, ref } from "vue";
import request from "../api/request.js";
import { getErrorMessage } from "../api/request.js";
import { Sparkles, Send, RefreshCw } from "@lucide/vue";

const messageList = ref(null);
const draft = ref("");
const loading = ref(false);
const messages = ref([
  {
    id: 1,
    role: "assistant",
    text: "晚上好，我可以帮你把题目拆成重点，也可以陪你用问答的方式复习。",
    time: "19:42",
  },
]);

const suggestions = ["出一道选择题", "解释这道错题", "总结本章重点"];

const canSend = computed(() => draft.value.trim().length > 0 && !loading.value);

function currentTime() {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
}

function scrollToBottom() {
  nextTick(() => {
    messageList.value?.scrollTo({
      top: messageList.value.scrollHeight,
      behavior: "smooth",
    });
  });
}

function addMessage(role, text) {
  messages.value.push({
    id: Date.now(),
    role,
    text,
    time: currentTime(),
  });
}

async function sendMessage(text = draft.value) {
  const content = text.trim();
  if (!content || loading.value) return;

  addMessage("user", content);
  draft.value = "";
  scrollToBottom();

  loading.value = true;
  try {
    const resp = await request.post("/chat/", { message: content });
    addMessage("assistant", resp.data.reply);
  } catch (err) {
    const msg = getErrorMessage(err, "AI 回复失败，请稍后重试");
    addMessage("assistant", msg);
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}

function retry(index) {
  const lastUserMsg = [...messages.value]
    .reverse()
    .find((m) => m.role === "user");
  if (!lastUserMsg) return;

  messages.value.splice(index, 1);
  sendMessage(lastUserMsg.text);
}
</script>

<template>
  <section class="chat-page" aria-label="学习对话">
    <!-- Top bar -->
    <div class="chat-topbar">
      <div>
        <p class="chat-kicker">
          <Sparkles :size="12" :stroke-width="3" style="margin-right:4px;vertical-align:-1px" />
          AI 复习助手
        </p>
        <h2>对话练习</h2>
      </div>
      <span class="online-dot">在线</span>
    </div>

    <!-- Messages -->
    <div ref="messageList" class="chat-messages">
      <article
        v-for="(message, idx) in messages"
        :key="message.id"
        class="chat-row"
        :class="message.role"
      >
        <div class="chat-avatar" aria-hidden="true">
          {{ message.role === "assistant" ? "AI" : "我" }}
        </div>
        <div class="chat-bubble">
          <p>{{ message.text }}</p>
          <time>{{ message.time }}</time>
          <button
            v-if="message.role === 'assistant' && message.text.startsWith('AI 回复失败')"
            class="retry-btn"
            @click="retry(idx)"
          >
            <RefreshCw :size="12" :stroke-width="2.5" style="margin-right:3px;vertical-align:-1px" />
            重试
          </button>
        </div>
      </article>

      <!-- Typing indicator -->
      <div v-if="loading" class="chat-row assistant">
        <div class="chat-avatar" aria-hidden="true">AI</div>
        <div class="chat-bubble typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- Suggestions -->
    <div class="suggestion-row" aria-label="快捷提问">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion"
        type="button"
        :disabled="loading"
        @click="sendMessage(suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>

    <!-- Composer -->
    <form class="chat-composer" @submit.prevent="sendMessage()">
      <textarea
        v-model="draft"
        rows="1"
        placeholder="输入题目、知识点或你的答案"
        :disabled="loading"
        @keydown.enter.exact.prevent="sendMessage()"
      />
      <button type="submit" :disabled="!canSend" aria-label="发送消息">
        <Send :size="18" :stroke-width="2.5" />
      </button>
    </form>
  </section>
</template>

<style scoped>
/* Refinements over global chat styles */

.chat-kicker {
  display: inline-flex;
  align-items: center;
}

.suggestion-row button {
  transition: all var(--ease-out);
}

.chat-composer button {
  display: grid;
  place-items: center;
  min-width: 48px;
  padding: 0;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
}
</style>
