<script setup>
import { computed, onMounted, ref } from "vue";
import request, { getErrorMessage } from "../api/request";
import {
  typeLabel,
  typeOptions,
  formatOptions,
} from "../utils/question";
import {
  Search, RefreshCw, Eye, EyeOff, Trash2, ChevronLeft, ChevronRight,
  Plus, Pencil, Globe, Lock,
} from "@lucide/vue";
import QuestionEditor from "../components/question/QuestionEditor.vue";
import { useConfirmDialog } from "../stores/confirmDialog";

const props = defineProps({
  courseId: { type: String, default: "" },
});

const confirmDialog = useConfirmDialog();

const questions = ref([]);
const expandedIds = ref(new Set());
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

// Editor state
const showEditor = ref(false);
const editingQuestion = ref(null);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));
const hasMore = computed(() => page.value < totalPages.value);

function onFilterChange() { page.value = 1; fetchQuestions(); }

function isExpanded(id) { return expandedIds.value.has(id); }

function toggleAnswer(id) {
  const next = new Set(expandedIds.value);
  next.has(id) ? next.delete(id) : next.add(id);
  expandedIds.value = next;
}

async function fetchMeta() {
  metaLoading.value = true;
  try {
    const { data } = await request.get("/questions/meta");
    subjects.value = data.subjects || [];
    chapters.value = data.chapters || [];
  } catch { subjects.value = []; chapters.value = []; }
  finally { metaLoading.value = false; }
}

async function fetchQuestions() {
  loading.value = true;
  errorMessage.value = "";
  actionMessage.value = "";
  const params = { page: page.value, page_size: pageSize };
  if (keyword.value.trim()) params.keyword = keyword.value.trim();
  if (typeFilter.value) params.type = typeFilter.value;
  if (subjectFilter.value) params.subject = subjectFilter.value;
  if (chapterFilter.value) params.chapter = chapterFilter.value;
  if (props.courseId) params.course_id = props.courseId;
  try {
    const { data } = await request.get("/questions/", { params });
    if (Array.isArray(data)) { questions.value = data; total.value = data.length; }
    else { questions.value = data.items || []; total.value = data.total || 0; }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取题目列表失败");
    questions.value = []; total.value = 0;
  } finally { loading.value = false; }
}

function goPrevPage() { if (page.value > 1) { page.value--; fetchQuestions(); } }
function goNextPage() { if (hasMore.value) { page.value++; fetchQuestions(); } }

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
  if (props.courseId) params.course_id = props.courseId;
  try {
    const { data } = await request.get("/questions/", { params });
    const newItems = Array.isArray(data) ? data : data.items || [];
    questions.value = [...questions.value, ...newItems];
    total.value = Array.isArray(data) ? questions.value.length : data.total || 0;
  } catch (error) { errorMessage.value = getErrorMessage(error, "加载更多失败"); page.value--; }
  finally { loading.value = false; }
}

async function deleteQuestion(q) {
  const confirmed = await confirmDialog.confirm({
    title: "删除题目",
    message: `确定删除这道题吗？\n${q.question}`,
    confirmText: "删除",
    tone: "danger",
  });
  if (!confirmed) return;
  actionMessage.value = "";
  errorMessage.value = "";
  try {
    await request.delete(`/questions/${q.id}`);
    actionMessage.value = "题目已删除。";
    await fetchQuestions();
  } catch (error) { errorMessage.value = getErrorMessage(error, "删除题目失败"); }
}

async function toggleQuestionVisibility(q) {
  actionMessage.value = "";
  errorMessage.value = "";
  try {
    if (q.visibility === "public") {
      await request.post(`/questions/${q.id}/unpublish`);
      q.visibility = "private";
      actionMessage.value = "题目已设为私有。";
    } else {
      await request.post(`/questions/${q.id}/publish`);
      q.visibility = "public";
      actionMessage.value = "题目已发布。";
    }
  } catch (error) { errorMessage.value = getErrorMessage(error, "操作失败"); }
}

function openCreateEditor() { editingQuestion.value = null; showEditor.value = true; }
function openEditEditor(q) { editingQuestion.value = q; showEditor.value = true; }
function closeEditor() { showEditor.value = false; }

function onQuestionSaved() { fetchQuestions(); }

onMounted(() => { fetchMeta(); fetchQuestions(); });
</script>

<template>
  <section class="stack">
    <div class="section-heading row-heading">
      <div>
        <h2>题目</h2>
        <p v-if="total">共 {{ total }} 道题</p>
      </div>
      <div class="heading-actions">
        <button class="ghost-button" type="button" :disabled="loading" @click="fetchQuestions">
          <RefreshCw :size="15" :stroke-width="2.5" style="margin-right:3px" />刷新
        </button>
        <button v-if="props.courseId" class="primary-button" type="button" @click="openCreateEditor">
          <Plus :size="16" :stroke-width="2.5" style="margin-right:4px" />新增题目
        </button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="input-with-icon filter-input-wrapper">
        <Search class="input-icon" :size="17" />
        <input v-model="keyword" class="text-input has-left-icon" type="search" placeholder="搜索关键词..." @input="onFilterChange" />
      </div>
      <select v-model="typeFilter" class="filter-select" @change="onFilterChange">
        <option value="">全部题型</option>
        <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
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

    <p v-if="loading && questions.length === 0" class="info-message">正在加载题目...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="actionMessage" class="success-message">{{ actionMessage }}</p>

    <div v-if="!loading && questions.length === 0 && !errorMessage" class="empty-state">
      还没有匹配的题目。
    </div>

    <article v-for="q in questions" :key="q.id" class="card question-card">
      <div class="meta-row">
        <span>{{ q.subject }}</span>
        <span>{{ q.chapter }}</span>
        <span class="meta-type">{{ typeLabel(q.type) }}</span>
        <span v-if="q.visibility === 'public'" class="meta-public" title="已公开">公开</span>
      </div>
      <h3>{{ q.question }}</h3>

      <ul v-if="formatOptions(q.options).length" class="option-list">
        <li v-for="opt in formatOptions(q.options)" :key="opt.key">
          <strong>{{ opt.key }}</strong><span>{{ opt.value }}</span>
        </li>
      </ul>

      <div v-if="isExpanded(q.id)" class="answer-panel">
        <div class="answer-line"><span class="answer-label">正确答案</span><span class="answer-value correct-answer">{{ q.answer }}</span></div>
        <div class="answer-line"><span class="answer-label">解析</span><span class="answer-value">{{ q.analysis || "暂无解析" }}</span></div>
      </div>

      <div class="button-row">
        <button class="ghost-button" type="button" @click="toggleAnswer(q.id)">
          <EyeOff v-if="isExpanded(q.id)" :size="15" style="margin-right:3px" />
          <Eye v-else :size="15" style="margin-right:3px" />
          {{ isExpanded(q.id) ? "收起" : "查看" }}
        </button>
        <button class="ghost-button" type="button" @click="openEditEditor(q)">
          <Pencil :size="15" style="margin-right:3px" />编辑
        </button>
        <button class="ghost-button" type="button" @click="toggleQuestionVisibility(q)">
          <Globe v-if="q.visibility === 'public'" :size="15" style="margin-right:3px" />
          <Lock v-else :size="15" style="margin-right:3px" />
          {{ q.visibility === "public" ? "撤回" : "发布" }}
        </button>
        <button class="danger-button" type="button" @click="deleteQuestion(q)">
          <Trash2 :size="15" style="margin-right:3px" />删除
        </button>
      </div>
    </article>

    <p v-if="loading && questions.length > 0" class="info-message">加载中...</p>

    <div v-if="total > pageSize" class="pagination-bar">
      <button class="ghost-button" :disabled="page <= 1 || loading" @click="goPrevPage">
        <ChevronLeft :size="16" :stroke-width="2.5" style="margin-right:2px" />上一页
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="ghost-button" :disabled="!hasMore || loading" @click="goNextPage">
        下一页<ChevronRight :size="16" :stroke-width="2.5" style="margin-left:2px" />
      </button>
    </div>

    <button v-if="hasMore && questions.length > 0" class="ghost-button full-button" :disabled="loading" @click="loadMore">
      {{ loading ? "加载中..." : "加载更多" }}
    </button>

    <!-- Editor modal -->
    <QuestionEditor
      v-if="showEditor"
      :courseId="props.courseId"
      :question="editingQuestion"
      @close="closeEditor"
      @saved="onQuestionSaved"
    />
  </section>
</template>

<style scoped>
.heading-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.filter-input-wrapper { grid-column: 1 / -1; position: relative; }
.input-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-placeholder); z-index: 1; pointer-events: none; }
.text-input.has-left-icon { padding-left: 40px; }
.meta-type { background: var(--primary-soft) !important; color: var(--primary-strong) !important; }
.meta-public { background: var(--emerald-soft) !important; color: var(--emerald) !important; }

.button-row { display: flex; flex-wrap: wrap; gap: 6px; }

.answer-line { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2); align-items: baseline; }
.answer-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.answer-value { font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.55; }
.correct-answer { color: var(--primary-strong); font-weight: 700; }

.ghost-button, .danger-button, .primary-button { display: inline-flex; align-items: center; justify-content: center; }

@media (min-width: 640px) { .filter-input-wrapper { grid-column: auto; } }
</style>
