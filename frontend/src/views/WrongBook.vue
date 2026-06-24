<script setup>
import { computed, onMounted, ref } from "vue";
import request, { getErrorMessage } from "../api/request";
import { typeLabel, typeOptions, formatOptions } from "../utils/question";
import { Search, RefreshCw, Trash2, ChevronLeft, ChevronRight } from "@lucide/vue";
import { useConfirmDialog } from "../stores/confirmDialog";

const confirmDialog = useConfirmDialog();

const wrongItems = ref([]);
const loading = ref(false);
const metaLoading = ref(false);
const errorMessage = ref("");
const actionMessage = ref("");

const keyword = ref("");
const typeFilter = ref("");
const subjectFilter = ref("");
const chapterFilter = ref("");
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const subjects = ref([]);
const chapters = ref([]);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));
const hasMore = computed(() => page.value < totalPages.value);

function onFilterChange() { page.value = 1; fetchWrongBook(); }

async function fetchMeta() {
  metaLoading.value = true;
  try {
    const { data } = await request.get("/wrongbook/meta");
    subjects.value = data.subjects || [];
    chapters.value = data.chapters || [];
  } catch {
    subjects.value = [];
    chapters.value = [];
  } finally {
    metaLoading.value = false;
  }
}

async function fetchWrongBook() {
  loading.value = true;
  errorMessage.value = "";
  actionMessage.value = "";

  const params = { page: page.value, page_size: pageSize };
  if (keyword.value.trim()) params.keyword = keyword.value.trim();
  if (typeFilter.value) params.type = typeFilter.value;
  if (subjectFilter.value) params.subject = subjectFilter.value;
  if (chapterFilter.value) params.chapter = chapterFilter.value;

  try {
    const { data } = await request.get("/wrongbook/", { params });
    if (Array.isArray(data)) {
      wrongItems.value = data;
      total.value = data.length;
    } else {
      wrongItems.value = data.items || [];
      total.value = data.total || 0;
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取错题本失败");
    wrongItems.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function goPrevPage() {
  if (page.value > 1) { page.value--; fetchWrongBook(); }
}

function goNextPage() {
  if (hasMore.value) { page.value++; fetchWrongBook(); }
}

async function loadMore() {
  if (!hasMore.value || loading.value) return;
  page.value++;
  loading.value = true;
  errorMessage.value = "";

  const params = { page: page.value, page_size: pageSize };
  if (keyword.value.trim()) params.keyword = keyword.value.trim();
  if (typeFilter.value) params.type = typeFilter.value;
  if (subjectFilter.value) params.subject = subjectFilter.value;
  if (chapterFilter.value) params.chapter = chapterFilter.value;

  try {
    const { data } = await request.get("/wrongbook/", { params });
    const newItems = Array.isArray(data) ? data : data.items || [];
    wrongItems.value = [...wrongItems.value, ...newItems];
    total.value = Array.isArray(data) ? wrongItems.value.length : data.total || 0;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "加载更多失败");
    page.value--;
  } finally {
    loading.value = false;
  }
}

async function removeWrongItem(item) {
  const confirmed = await confirmDialog.confirm({
    title: "移除错题",
    message: "确定从错题本移除这道题吗？移除后不会删除原题。",
    confirmText: "移除",
    tone: "danger",
  });
  if (!confirmed) return;

  errorMessage.value = "";
  actionMessage.value = "";
  try {
    await request.delete(`/wrongbook/${item.question_id}`);
    actionMessage.value = "已从错题本移除。";
    await fetchWrongBook();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "移除错题失败");
  }
}

onMounted(() => {
  fetchMeta();
  fetchWrongBook();
});
</script>

<template>
  <section class="stack">
    <div class="section-heading row-heading">
      <div>
        <h2>错题本</h2>
        <p>共 {{ total }} 道错题</p>
      </div>
      <button class="ghost-button" type="button" :disabled="loading" @click="fetchWrongBook">
        <RefreshCw :size="16" :stroke-width="2.5" style="margin-right:4px" />
        刷新
      </button>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="input-with-icon filter-input-wrapper">
        <Search class="input-icon" :size="17" />
        <input
          v-model="keyword"
          class="text-input has-left-icon"
          type="search"
          placeholder="搜索题目关键词..."
          @input="onFilterChange"
        />
      </div>
      <select v-model="typeFilter" class="filter-select" @change="onFilterChange">
        <option value="">全部题型</option>
        <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <select v-model="subjectFilter" class="filter-select" @change="onFilterChange">
        <option value="">全部科目</option>
        <option v-if="metaLoading" disabled>加载中...</option>
        <option v-for="s in subjects" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="chapterFilter" class="filter-select" @change="onFilterChange">
        <option value="">全部章节</option>
        <option v-if="metaLoading" disabled>加载中...</option>
        <option v-for="c in chapters" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <p v-if="loading && wrongItems.length === 0" class="info-message">正在加载错题...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="actionMessage" class="success-message">{{ actionMessage }}</p>

    <div v-if="!loading && wrongItems.length === 0 && !errorMessage" class="empty-state">
      暂时没有错题。练习答错后会自动记录在这里。
    </div>

    <article v-for="item in wrongItems" :key="item.id" class="card question-card">
      <template v-if="item.question">
        <div class="meta-row">
          <span>{{ item.question.subject }}</span>
          <span>{{ item.question.chapter }}</span>
          <span class="meta-type">{{ typeLabel(item.question.type) }}</span>
        </div>
        <h3>{{ item.question.question }}</h3>

        <ul v-if="formatOptions(item.question.options).length" class="option-list">
          <li v-for="option in formatOptions(item.question.options)" :key="option.key">
            <strong>{{ option.key }}</strong>
            <span>{{ option.value }}</span>
          </li>
        </ul>

        <div class="answer-panel">
          <div class="answer-line">
            <span class="answer-label">正确答案</span>
            <span class="answer-value correct-answer">{{ item.question.answer }}</span>
          </div>
          <div class="answer-line">
            <span class="answer-label">解析</span>
            <span class="answer-value">{{ item.question.analysis || "暂无解析" }}</span>
          </div>
        </div>

        <div class="wrongbook-stats">
          <span class="stat-badge">
            错题 <strong>{{ item.wrong_count }}</strong> 次
          </span>
          <span class="stat-badge wrong-answer">
            上次错误答案：<strong>{{ item.last_wrong_answer || "无记录" }}</strong>
          </span>
        </div>
      </template>
      <div v-else class="deleted-question-notice">
        <p>题目已删除或不可用。</p>
        <div class="wrongbook-stats" style="justify-content:center;margin-top:8px">
          <span class="stat-badge">错题次数：<strong>{{ item.wrong_count }}</strong></span>
          <span class="stat-badge wrong-answer">
            上次错误答案：<strong>{{ item.last_wrong_answer || "无记录" }}</strong>
          </span>
        </div>
      </div>

      <button class="danger-button full-button" type="button" @click="removeWrongItem(item)">
        <Trash2 :size="16" :stroke-width="2.5" style="margin-right:4px" />
        移除错题
      </button>
    </article>

    <p v-if="loading && wrongItems.length > 0" class="info-message">加载中...</p>

    <div v-if="total > pageSize" class="pagination-bar">
      <button class="ghost-button" :disabled="page <= 1 || loading" @click="goPrevPage">
        <ChevronLeft :size="16" :stroke-width="2.5" style="margin-right:2px" />
        上一页
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="ghost-button" :disabled="!hasMore || loading" @click="goNextPage">
        下一页
        <ChevronRight :size="16" :stroke-width="2.5" style="margin-left:2px" />
      </button>
    </div>

    <button
      v-if="hasMore && wrongItems.length > 0"
      class="ghost-button full-button"
      :disabled="loading"
      @click="loadMore"
    >
      {{ loading ? "加载中..." : "加载更多" }}
    </button>
  </section>
</template>

<style scoped>
.filter-input-wrapper {
  grid-column: 1 / -1;
  position: relative;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-placeholder);
  z-index: 1;
  pointer-events: none;
}

.text-input.has-left-icon {
  padding-left: 40px;
}

.meta-type {
  background: var(--rose-soft) !important;
  color: var(--rose) !important;
}

.answer-line {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-2);
  align-items: baseline;
}

.answer-label {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.answer-value {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.55;
}

.correct-answer {
  color: var(--primary-strong);
  font-weight: 700;
}

.ghost-button,
.danger-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 640px) {
  .filter-input-wrapper {
    grid-column: auto;
  }
}
</style>
