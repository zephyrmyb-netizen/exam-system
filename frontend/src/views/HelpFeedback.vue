<script setup lang="ts">
import { computed, ref } from "vue";
import { CheckCircle2, CircleHelp, MessageSquare, Send } from "@lucide/vue";

import { submitFeedback, type FeedbackCategory } from "@/api/feedback";
import { getErrorMessage } from "@/api/request";

const category = ref<FeedbackCategory>("suggestion");
const content = ref("");
const contact = ref("");
const saving = ref(false);
const errorMessage = ref("");
const submittedId = ref<number | null>(null);
const diagnosing = ref(false);

const canSubmit = computed(() => content.value.trim().length >= 5 && !saving.value);

async function submit() {
  if (!canSubmit.value) return;
  saving.value = true;
  errorMessage.value = "";
  submittedId.value = null;
  try {
    const saved = await submitFeedback({
      category: category.value,
      content: content.value.trim(),
      contact: contact.value.trim(),
    });
    submittedId.value = saved.id;
    content.value = "";
    contact.value = "";
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "反馈提交失败，请稍后重试");
  } finally {
    saving.value = false;
  }
}

async function submitDiagnostic() {
  if (diagnosing.value) return;
  diagnosing.value = true;
  errorMessage.value = "";
  submittedId.value = null;
  try {
    const navigation = window.performance.getEntriesByType("navigation")[0];
    const saved = await submitFeedback({
      category: "diagnostic",
      content: JSON.stringify({
        url: window.location.pathname,
        online: navigator.onLine,
        loadMs: navigation ? Math.round(navigation.duration) : null,
        version: import.meta.env.VITE_APP_VERSION || "web",
      }),
    });
    submittedId.value = saved.id;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "提交运行诊断失败");
  } finally {
    diagnosing.value = false;
  }
}
</script>

<template>
  <section class="help-feedback-page" data-reference-page="help-feedback">
    <header class="help-hero">
      <span class="help-hero__icon"><CircleHelp :size="22" /></span>
      <div>
        <p>帮助中心</p>
        <h1>遇到问题，直接告诉我们</h1>
        <span>反馈会保存并生成编号，方便后续跟进。</span>
      </div>
    </header>

    <section class="faq-card" aria-label="常见问题">
      <h2>常见问题</h2>
      <details open>
        <summary>打开链接却显示未登录怎么办？</summary>
        <p>请先刷新一次页面；系统会自动尝试恢复已保存的登录会话。仍无法恢复时，请提交下面的反馈。</p>
      </details>
      <details>
        <summary>导入资料失败怎么办？</summary>
        <p>请保留文件类型、失败提示和出现问题的时间；这些信息能帮助我们更快定位问题。</p>
      </details>
      <details>
        <summary>如何反馈新的功能建议？</summary>
        <p>选择“功能建议”，说明你想完成的目标和当前不方便的地方即可。</p>
      </details>
    </section>

    <section class="diagnostic-card">
      <div>
        <h2>页面慢或打不开？</h2>
        <p>提交匿名运行诊断：网络状态、页面耗时、版本与访问路径。</p>
      </div>
      <button type="button" data-testid="feedback-diagnostic" :disabled="diagnosing" @click="submitDiagnostic">
        {{ diagnosing ? "正在收集…" : "提交运行诊断" }}
      </button>
    </section>
    <form class="feedback-form" @submit.prevent="submit">
      <div class="form-heading">
        <MessageSquare :size="20" />
        <h2>提交反馈</h2>
      </div>
      <label>
        <span>反馈类型</span>
        <select v-model="category" data-testid="feedback-category">
          <option value="bug">问题报错</option>
          <option value="suggestion">功能建议</option>
          <option value="question">使用疑问</option>
          <option value="other">其他</option>
        </select>
      </label>
      <label>
        <span>具体说明</span>
        <textarea
          v-model="content"
          data-testid="feedback-content"
          rows="6"
          maxlength="2000"
          placeholder="请描述你正在做什么、出现了什么情况，以及你希望得到什么结果。"
        />
      </label>
      <label>
        <span>联系方式（可选）</span>
        <input
          v-model="contact"
          data-testid="feedback-contact"
          maxlength="120"
          placeholder="微信号、邮箱或其他便于联系的方式"
        />
      </label>
      <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
      <p v-if="submittedId" class="success-message" role="status">
        <CheckCircle2 :size="18" /> 已提交，反馈编号：#{{ submittedId }}
      </p>
      <button data-testid="feedback-submit" class="submit-button" type="submit" :disabled="!canSubmit">
        <Send :size="18" /> {{ saving ? "正在提交..." : "提交反馈" }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.help-feedback-page {
  display: grid;
  gap: var(--space-4);
}
.help-hero,
.faq-card,
.feedback-form,
.diagnostic-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-5);
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: var(--surface);
}
.help-hero {
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  background: linear-gradient(135deg, var(--primary-soft), var(--surface));
}
.help-hero__icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: var(--primary);
  color: #fff;
}
.help-hero p,
.help-hero h1,
.help-hero span,
.faq-card h2,
.feedback-form h2 {
  margin: 0;
}
.help-hero p {
  color: var(--primary);
  font-size: var(--text-xs);
  font-weight: 900;
}
.help-hero h1 {
  color: var(--text-main);
  font-size: clamp(25px, 7vw, 38px);
  line-height: 1.15;
}
.help-hero span,
details p {
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}
.faq-card h2,
.feedback-form h2 {
  color: var(--text-main);
  font-size: var(--text-lg);
}
details {
  padding: 12px 0;
  border-top: 1px solid var(--line-soft);
}
summary {
  color: var(--text-main);
  cursor: pointer;
  font-weight: 850;
}
details p {
  margin: 10px 0 0;
}
.feedback-form label {
  display: grid;
  gap: 7px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 850;
}
.feedback-form select,
.feedback-form textarea,
.feedback-form input {
  width: 100%;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  padding: 12px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
}
.feedback-form textarea {
  resize: vertical;
  min-height: 120px;
}
.form-heading,
.success-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--primary);
}
.submit-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  border: 0;
  border-radius: 16px;
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 900;
}
.submit-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.diagnostic-card {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}
.diagnostic-card h2,
.diagnostic-card p {
  margin: 0;
}
.diagnostic-card h2 {
  color: var(--text-main);
  font-size: var(--text-lg);
}
.diagnostic-card p {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: var(--text-sm);
}
.diagnostic-card button {
  min-height: 42px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  padding: 0 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
  font-weight: 800;
}
</style>
