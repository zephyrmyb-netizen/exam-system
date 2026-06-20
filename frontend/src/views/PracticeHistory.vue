<script setup>
import { computed, onMounted, ref } from "vue";
import request from "../api/request";
import { getPracticeHistory } from "../api/practice";
import { getErrorMessage } from "../api/request";
import {
  Clock,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  History,
} from "@lucide/vue";

const records = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const page = ref(1);
const pageSize = 20;
const total = ref(0);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));
const hasMore = computed(() => page.value < totalPages.value);
const isEmpty = computed(() => !loading.value && records.value.length === 0 && !errorMessage.value);

function formatTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return iso;
  }
}

async function fetchPage(p) {
  page.value = p;
  loading.value = true;
  errorMessage.value = "";
  try {
    const data = await getPracticeHistory({ page: p, page_size: pageSize });
    records.value = data.items || [];
    total.value = data.total || 0;
  } catch (error) {
    records.value = [];
    total.value = 0;
    errorMessage.value = getErrorMessage(error, "获取练习记录失败");
  } finally {
    loading.value = false;
  }
}

function goPrev() {
  if (page.value > 1) fetchPage(page.value - 1);
}

function goNext() {
  if (hasMore.value) fetchPage(page.value + 1);
}

onMounted(() => fetchPage(1));
</script>

<template>
  <section class="stack">
    <p v-if="loading" class="info-message">正在加载记录...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <!-- Empty -->
    <div v-if="isEmpty" class="empty-state">
      <History :size="40" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p>还没有练习记录。</p>
      <p class="empty-hint">去练习页面开始，记录会自动保存。</p>
    </div>

    <!-- Record list -->
    <article
      v-for="record in records"
      :key="record.id"
      class="history-card"
    >
      <div class="history-top">
        <span class="history-status" :class="record.is_correct ? 'status-ok' : 'status-fail'">
          <CheckCircle v-if="record.is_correct" :size="15" :stroke-width="2.5" />
          <XCircle v-else :size="15" :stroke-width="2.5" />
          {{ record.is_correct ? "正确" : "错误" }}
        </span>
        <time v-if="record.answered_at" class="history-time">
          <Clock :size="12" :stroke-width="2.5" style="margin-right:3px" />
          {{ formatTime(record.answered_at) }}
        </time>
      </div>

      <p class="history-question">
        {{ record.question_text || "（题目已删除或不可用）" }}
      </p>

      <div class="history-answers">
        <div class="answer-line">
          <span class="answer-role">你的答案</span>
          <span :class="record.is_correct ? 'answer-correct' : 'answer-wrong'">
            {{ record.user_answer || "—" }}
          </span>
        </div>
        <div v-if="!record.is_correct" class="answer-line">
          <span class="answer-role">正确答案</span>
          <span class="answer-correct">{{ record.correct_answer || "—" }}</span>
        </div>
      </div>
    </article>

    <p v-if="loading && records.length > 0" class="info-message">加载中...</p>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="pagination-bar">
      <button class="ghost-button" :disabled="page <= 1 || loading" @click="goPrev">
        <ChevronLeft :size="16" :stroke-width="2.5" style="margin-right:2px" />
        上一页
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="ghost-button" :disabled="!hasMore || loading" @click="goNext">
        下一页
        <ChevronRight :size="16" :stroke-width="2.5" style="margin-left:2px" />
      </button>
    </div>
  </section>
</template>

<style scoped>
/* ── Card ── */
.history-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

/* ── Top row ── */
.history-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.history-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  line-height: 1.4;
}

.status-ok {
  color: var(--emerald);
  background: var(--emerald-soft);
}

.status-fail {
  color: var(--rose);
  background: var(--rose-soft);
}

.history-time {
  display: inline-flex;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--text-placeholder);
  font-weight: 600;
}

/* ── Question ── */
.history-question {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.55;
  word-break: break-word;
}

/* ── Answers ── */
.history-answers {
  display: grid;
  gap: 6px;
  padding-top: var(--space-1);
}

.answer-line {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-2);
  align-items: baseline;
  font-size: var(--text-xs);
  line-height: 1.5;
}

.answer-role {
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.answer-correct {
  color: var(--emerald);
  font-weight: 700;
}

.answer-wrong {
  color: var(--rose);
  font-weight: 700;
}

/* ── Empty ── */
.empty-state {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  padding: var(--space-10) var(--space-4);
  text-align: center;
  color: var(--text-muted);
}

.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
}

.empty-hint {
  font-size: var(--text-xs) !important;
  color: var(--text-placeholder);
}

/* ── Buttons ── */
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>