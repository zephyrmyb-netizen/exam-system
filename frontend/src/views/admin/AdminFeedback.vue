<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import { listAdminFeedback, updateAdminFeedback, type AdminFeedback, type FeedbackStatus } from "@/api/admin";
import { getErrorMessage } from "@/api/request";

const items = ref<AdminFeedback[]>([]);
const filter = ref<"all" | FeedbackStatus>("all");
const loading = ref(false);
const savingId = ref<number | null>(null);
const errorMessage = ref("");
const successMessage = ref("");

const statusLabels: Record<FeedbackStatus, string> = {
  new: "待处理",
  in_progress: "处理中",
  resolved: "已解决",
};

async function fetchFeedback() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const data = await listAdminFeedback(filter.value === "all" ? undefined : filter.value);
    items.value = data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "反馈列表加载失败");
  } finally {
    loading.value = false;
  }
}

async function saveFeedback(entry: AdminFeedback) {
  savingId.value = entry.id;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const updated = await updateAdminFeedback(entry.id, {
      status: entry.status,
      admin_reply: entry.admin_reply,
    });
    const index = items.value.findIndex((item) => item.id === entry.id);
    if (index >= 0) items.value[index] = updated;
    successMessage.value = `反馈 #${entry.id} 已保存`;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "反馈处理保存失败");
  } finally {
    savingId.value = null;
  }
}

onMounted(fetchFeedback);
</script>

<template>
  <section class="admin-feedback-page">
    <div class="section-heading row-heading">
      <div>
        <h2>反馈处理</h2>
        <p>查看用户反馈，填写回复并同步处理状态。</p>
      </div>
      <button
        data-testid="admin-feedback-refresh"
        class="refresh-button"
        type="button"
        :disabled="loading"
        @click="fetchFeedback"
      >
        <RefreshCw :size="16" />
        刷新
      </button>
    </div>

    <label class="filter-field">
      <span>处理状态</span>
      <select v-model="filter" data-testid="admin-feedback-filter" @change="fetchFeedback">
        <option value="all">全部</option>
        <option value="new">待处理</option>
        <option value="in_progress">处理中</option>
        <option value="resolved">已解决</option>
      </select>
    </label>

    <p v-if="loading" class="info-message">正在加载反馈...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    <p v-if="!loading && !errorMessage && items.length === 0" class="empty-state">暂无符合条件的反馈。</p>

    <article v-for="entry in items" :key="entry.id" class="feedback-card">
      <div class="feedback-card__meta">
        <strong>#{{ entry.id }} · {{ entry.display_name || entry.username }}</strong>
        <span>{{ entry.category }} · {{ entry.contact || "未留联系方式" }}</span>
      </div>
      <p class="feedback-card__content">{{ entry.content }}</p>
      <label class="status-field">
        <span>状态</span>
        <select :data-testid="`admin-feedback-status-${entry.id}`" v-model="entry.status">
          <option value="new">待处理</option>
          <option value="in_progress">处理中</option>
          <option value="resolved">已解决</option>
        </select>
        <small>{{ statusLabels[entry.status] }}</small>
      </label>
      <label class="reply-field">
        <span>处理回复</span>
        <textarea
          :data-testid="`admin-feedback-reply-${entry.id}`"
          v-model="entry.admin_reply"
          rows="3"
          maxlength="2000"
          placeholder="填写给用户的处理说明"
        />
      </label>
      <button
        :data-testid="`admin-feedback-save-${entry.id}`"
        class="save-button"
        type="button"
        :disabled="savingId === entry.id"
        @click="saveFeedback(entry)"
      >
        {{ savingId === entry.id ? "保存中..." : "保存处理结果" }}
      </button>
    </article>
  </section>
</template>

<style scoped>
.admin-feedback-page {
  display: grid;
  gap: var(--space-3);
}
.refresh-button,
.save-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  border-radius: 14px;
  font: inherit;
  font-weight: 850;
}
.refresh-button {
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-main);
}
.filter-field,
.status-field,
.reply-field {
  display: grid;
  gap: 6px;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 800;
}
.filter-field select,
.status-field select,
.reply-field textarea {
  width: 100%;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
}
.filter-field select,
.status-field select {
  min-height: 40px;
  padding: 0 10px;
}
.reply-field textarea {
  padding: 10px;
  resize: vertical;
  line-height: 1.5;
}
.feedback-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.feedback-card__meta {
  display: grid;
  gap: 3px;
}
.feedback-card__meta strong {
  color: var(--text-main);
}
.feedback-card__meta span,
.status-field small {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 750;
}
.feedback-card__content {
  margin: 0;
  white-space: pre-wrap;
  color: var(--text-main);
  line-height: 1.6;
}
.save-button {
  border: 0;
  background: var(--primary);
  color: #fff;
}
.save-button:disabled,
.refresh-button:disabled {
  opacity: 0.6;
  cursor: wait;
}
</style>
