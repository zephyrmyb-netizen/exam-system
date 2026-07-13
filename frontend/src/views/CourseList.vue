<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  Eye,
  Globe,
  GraduationCap,
  Lock,
  MoreHorizontal,
  Pencil,
  Play,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from "@lucide/vue";

import request, { getErrorMessage } from "../api/request";
import { useAppNavigation } from "../composables/useAppNavigation";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { useConfirmDialog } from "../stores/confirmDialog";
import type { Course } from "../types";
import Button from "../components/ui/button/Button.vue";

const { replaceWithSource } = useAppNavigation();
const confirmDialog = useConfirmDialog();

const courses = ref<Course[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const deleteLoading = ref<number | null>(null);
const publishLoading = ref<number | null>(null);
const searchText = ref("");
const visibilityFilter = ref<"all" | "private" | "public">("all");
const openCourseMenuId = ref<number | null>(null);

const visibilityFilters = [
  { key: "all", label: "全部" },
  { key: "private", label: "私有" },
  { key: "public", label: "公开" },
] as const;

function flashSuccess(msg: string) {
  successMessage.value = msg;
  setTimeout(() => {
    successMessage.value = "";
  }, 2500);
}

const showForm = ref(false);
const editingCourse = ref<Course | null>(null);
const formLoading = ref(false);
const formError = ref("");
const form = reactive({ name: "", description: "", subject: "" });

const filteredCourses = computed(() => {
  const keyword = searchText.value.trim().toLowerCase();
  return courses.value.filter((course) => {
    if (visibilityFilter.value !== "all" && course.visibility !== visibilityFilter.value) return false;
    if (!keyword) return true;
    const fields = [course.name, course.subject, course.description, course.visibility];
    return fields.some((field) => String(field || "").toLowerCase().includes(keyword));
  });
});

const courseSummary = computed(() => {
  const total = courses.value.length;
  const visible = filteredCourses.value.length;
  if (!total) return "创建题库或导入资料后，就可以开始练习。";
  if (searchText.value.trim() || visibilityFilter.value !== "all") return `已筛选 ${visible} / ${total} 个题库`;
  return `共 ${total} 个题库，选择一个开始练习。`;
});

const isEdit = computed(() => !!editingCourse.value);

function openCreate() {
  form.name = "";
  form.description = "";
  form.subject = "";
  editingCourse.value = null;
  formError.value = "";
  showForm.value = true;
}

function openEdit(course: Course) {
  form.name = course.name;
  form.description = course.description || "";
  form.subject = course.subject || "";
  editingCourse.value = course;
  formError.value = "";
  openCourseMenuId.value = null;
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
}

function clearSearch() {
  searchText.value = "";
}

function toggleCourseMenu(courseId: number) {
  openCourseMenuId.value = openCourseMenuId.value === courseId ? null : courseId;
}

async function handleSave() {
  if (!form.name.trim()) {
    formError.value = "题库名称不能为空";
    return;
  }

  formLoading.value = true;
  formError.value = "";

  try {
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      subject: form.subject.trim(),
    };

    if (editingCourse.value) {
      const { data } = await request.patch<Course>(`/courses/${editingCourse.value.id}`, payload);
      Object.assign(editingCourse.value, data);
      flashSuccess("题库已更新");
    } else {
      const { data } = await request.post<Course>("/courses/", { ...payload, visibility: "private" });
      courses.value.unshift(data);
      flashSuccess("题库已创建");
    }

    closeForm();
  } catch (error) {
    formError.value = getErrorMessage(error, "保存失败");
  } finally {
    formLoading.value = false;
  }
}

async function fetchCourses() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const { data } = await request.get<Course[] | { items: Course[] }>("/courses/mine");
    courses.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取题库失败");
  } finally {
    loading.value = false;
  }
}

async function deleteCourse(course: Course) {
  openCourseMenuId.value = null;
  const confirmed = await confirmDialog.confirm({
    title: "删除题库",
    message: `确定删除「${getCourseDisplayName(course)}」吗？\n其中 ${course.question_count ?? 0} 道题会一起移除。`,
    confirmText: "删除",
    cancelText: "取消",
    tone: "danger",
  });

  if (!confirmed) return;

  deleteLoading.value = course.id;
  errorMessage.value = "";

  try {
    await request.delete(`/courses/${course.id}`);
    courses.value = courses.value.filter((item) => item.id !== course.id);
    flashSuccess("题库已删除");
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "删除失败");
  } finally {
    deleteLoading.value = null;
  }
}

async function togglePublish(course: Course) {
  openCourseMenuId.value = null;
  publishLoading.value = course.id;
  errorMessage.value = "";

  try {
    if (course.visibility === "public") {
      const { data } = await request.post<Course>(`/courses/${course.id}/unpublish`);
      course.visibility = data.visibility || "private";
      flashSuccess("已取消发布");
    } else {
      const { data } = await request.post<Course>(`/courses/${course.id}/publish`);
      course.visibility = data.visibility || "public";
      flashSuccess("已发布到公共题库");
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "操作失败");
  } finally {
    publishLoading.value = null;
  }
}

function goToPractice(course: Course) {
  if (!isPracticeReadyCourse(course)) return;
  replaceWithSource(`/courses/${course.id}/practice`, "courses");
}

function formatLastPracticed(course: Course) {
  if (!course.last_practiced_at) return "尚未练习";
  return `最近练习 ${new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
  }).format(new Date(course.last_practiced_at))}`;
}

onMounted(fetchCourses);
</script>

<template>
  <section class="library-page">
    <header class="library-head fade-up">
      <div>
        <p class="eyebrow">学习工具 · 题库管理</p>
        <h2 class="library-title">题库</h2>
        <p class="library-count">{{ courses.length }} 个题库</p>
      </div>
      <button class="primary-action" type="button" @click="openCreate">
        <Plus :size="17" :stroke-width="2.4" />
        创建题库
      </button>
    </header>

    <p v-if="loading" class="status-banner status-banner--info">题库加载中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="status-banner status-banner--success">{{ successMessage }}</p>

    <div v-if="courses.length > 0" class="library-tools fade-up d1">
      <div class="search-bar">
        <Search :size="18" :stroke-width="2.4" class="search-icon" />
        <input
          v-model="searchText"
          type="search"
          class="search-input"
          placeholder="搜索题库、科目或描述"
        />
        <button
          v-if="searchText"
          class="search-clear"
          type="button"
          aria-label="清空搜索"
          @click="clearSearch"
        >
          <X :size="14" :stroke-width="2.6" />
        </button>
      </div>
      <div class="seg">
        <button
          v-for="filter in visibilityFilters"
          :key="filter.key"
          class="seg-item"
          :class="{ active: visibilityFilter === filter.key }"
          type="button"
          :aria-label="`${filter.label}题库筛选`"
          :aria-pressed="visibilityFilter === filter.key"
          @click="visibilityFilter = filter.key"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>

    <p v-if="courses.length > 0" class="lib-summary fade-up d1">{{ courseSummary }}</p>

    <div
      v-if="!loading && courses.length === 0 && !errorMessage"
      class="empty-state ink-card fade-up d2"
    >
      <GraduationCap :size="48" :stroke-width="1.5" class="empty-icon" />
      <strong class="empty-title">还没有题库</strong>
      <p class="empty-desc">创建一门课程，或先去导入题目。</p>
      <div class="empty-actions">
        <button class="btn-solid" type="button" @click="openCreate">
          <Plus :size="16" :stroke-width="2.5" />
          创建题库
        </button>
        <button class="btn-outline" type="button" @click="replaceWithSource('/import', 'courses')">
          <Sparkles :size="16" :stroke-width="2.5" />
          去导入
        </button>
      </div>
    </div>

    <div
      v-if="!loading && courses.length > 0 && filteredCourses.length === 0 && !errorMessage"
      class="empty-state ink-card fade-up d2"
    >
      <Search :size="44" :stroke-width="1.5" class="empty-icon" />
      <strong class="empty-title">没有找到匹配题库</strong>
      <p class="empty-desc">换个关键词，或者清空搜索查看全部。</p>
      <button class="btn-outline" type="button" @click="clearSearch">清空搜索</button>
    </div>

    <div v-if="filteredCourses.length > 0" class="section-head fade-up d2">
      <h3 class="section-title">我的题库</h3>
      <button
        class="section-more"
        type="button"
        :disabled="loading"
        aria-label="刷新题库列表"
        @click="fetchCourses"
      >
        刷新
      </button>
    </div>

    <div v-if="filteredCourses.length > 0" class="course-list fade-up d2">
      <div
        v-for="(course, idx) in filteredCourses"
        :key="course.id"
        class="course-row fade-up"
        :class="'d' + ((idx % 5) + 1)"
      >
        <div
          class="course-item"
          role="button"
          tabindex="0"
          @click="replaceWithSource(`/courses/${course.id}`, 'courses')"
          @keydown.enter="replaceWithSource(`/courses/${course.id}`, 'courses')"
        >
          <span class="course-icon" :class="'ci-' + ((idx % 6) + 1)">{{ getCourseDisplayName(course).charAt(0) }}</span>
          <div class="course-info">
            <strong class="truncate" data-course-title :title="getCourseDisplayName(course)">{{ getCourseDisplayName(course) }}</strong>
            <span class="course-subline">
              {{ course.subject || '未分类' }} · {{ course.visibility === 'public' ? '公开' : '私有' }} · {{ formatLastPracticed(course) }}
            </span>
          </div>
          <span class="course-stat"><strong>{{ course.question_count ?? 0 }}</strong><small>题</small></span>
          <span class="visibility-label" :class="course.visibility === 'public' ? 'is-public' : 'is-private'">
            {{ course.visibility === 'public' ? '公开' : '私有' }}
          </span>
          <span class="course-recent">{{ formatLastPracticed(course) }}</span>
          <button
            class="practice-action"
            type="button"
            :disabled="!isPracticeReadyCourse(course)"
            @click.stop="goToPractice(course)"
          >
            <Play :size="15" :stroke-width="2.5" />
            练习
          </button>
          <button
            class="more-btn"
            type="button"
            :aria-label="`更多操作：${getCourseDisplayName(course)}`"
            :aria-expanded="openCourseMenuId === course.id"
            @click.stop="toggleCourseMenu(course.id)"
          >
            <MoreHorizontal :size="18" :stroke-width="2.5" />
          </button>
        </div>

        <div v-if="openCourseMenuId === course.id" class="course-menu">
          <button
            class="menu-option"
            type="button"
            :disabled="!isPracticeReadyCourse(course)"
            @click.stop="goToPractice(course)"
          >
            <Play :size="15" :stroke-width="2.5" />
            {{ isPracticeReadyCourse(course) ? '开始练习' : '暂无题目' }}
          </button>
          <button
            class="menu-option"
            type="button"
            @click.stop="replaceWithSource(`/courses/${course.id}`, 'courses')"
          >
            <Eye :size="15" :stroke-width="2.5" />
            查看题目
          </button>
          <div class="menu-divider"></div>
          <button
            class="menu-option"
            type="button"
            :aria-label="`编辑${getCourseDisplayName(course)}`"
            @click.stop="openEdit(course)"
          >
            <Pencil :size="15" :stroke-width="2.5" />
            编辑
          </button>
          <button
            class="menu-option"
            type="button"
            :aria-label="`${course.visibility === 'public' ? '撤回' : '公开'}${getCourseDisplayName(course)}`"
            :disabled="publishLoading === course.id"
            @click.stop="togglePublish(course)"
          >
            <Globe v-if="course.visibility !== 'public'" :size="15" :stroke-width="2.5" />
            <Lock v-else :size="15" :stroke-width="2.5" />
            {{ course.visibility === 'public' ? '撤回公开' : '发布到公共题库' }}
          </button>
          <div class="menu-divider"></div>
          <button
            class="menu-option menu-danger"
            type="button"
            :aria-label="`删除${getCourseDisplayName(course)}`"
            :disabled="deleteLoading === course.id"
            @click.stop="deleteCourse(course)"
          >
            <Trash2 :size="15" :stroke-width="2.5" />
            删除
          </button>
        </div>
      </div>
    </div>

    <button
      v-if="courses.length > 0 && filteredCourses.length > 0"
      class="btn-outline btn-block"
      type="button"
      @click="replaceWithSource('/public-library', 'courses')"
    >
      <Globe :size="17" :stroke-width="2.5" />
      浏览公共题库
    </button>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="ink-card modal-card">
        <div class="modal-head">
          <h3 class="modal-title">{{ isEdit ? '编辑题库' : '创建题库' }}</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="closeForm">
            <X :size="18" :stroke-width="2.5" />
          </button>
        </div>

        <p v-if="formError" class="status-banner status-banner--error">{{ formError }}</p>

        <label class="form-field">
          <span class="field-label">题库名称</span>
          <input v-model="form.name" class="text-input" type="text" placeholder="如：Java 期末复习" />
        </label>
        <label class="form-field">
          <span class="field-label">科目（可选）</span>
          <input v-model="form.subject" class="text-input" type="text" placeholder="如：Java" />
        </label>
        <label class="form-field">
          <span class="field-label">描述（可选）</span>
          <textarea
            v-model="form.description"
            class="text-input form-textarea"
            placeholder="简单描述题库内容"
          />
        </label>

        <div class="modal-actions">
          <Button variant="outline" @click="closeForm">取消</Button>
          <Button :disabled="formLoading" @click="handleSave">
            {{ formLoading ? '保存中...' : isEdit ? '保存修改' : '创建' }}
          </Button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ── Page container ── */
.library-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-bottom: calc(var(--nav-bottom-clearance) + 72px);
}

/* ── Search bar ── */
.search-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px 14px;
}
.search-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}
.search-input {
  flex: 1;
  min-width: 0;
  min-height: 36px;
  border: none;
  background: transparent;
  color: var(--text-main);
  font-size: var(--text-base);
  font-weight: 600;
  outline: none;
}
.search-input::placeholder {
  color: var(--text-placeholder);
}
.search-clear {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--ease-out), color var(--ease-out);
}
.search-clear:hover {
  background: var(--surface-strong);
  color: var(--text-main);
}

/* ── Summary line ── */
.lib-summary {
  margin: 0;
  padding: 0 4px;
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
}

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6) var(--space-4);
  text-align: center;
}
.empty-icon {
  color: var(--text-placeholder);
}
.empty-title {
  font-family: var(--font-sans);
  font-size: var(--text-lg);
  font-weight: 800;
  color: var(--text-main);
}
.empty-desc {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-weight: 600;
}
.empty-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
  flex-wrap: wrap;
  justify-content: center;
}

/* ── Section more button ── */
.section-more {
  cursor: pointer;
}
.section-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Course list ── */
.course-list {
  display: grid;
  gap: var(--space-2);
}

/* ── Course row (single-line card: item + dropdown menu) ── */
.course-row {
  position: relative;
  border-radius: var(--radius-lg);
  background: var(--surface);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-xs);
  overflow: visible;
  transition: box-shadow var(--ease-out);
}
.course-row:hover {
  box-shadow: var(--shadow-card);
}

/* Override global .course-item to act as compact clickable row */
.course-row .course-item {
  cursor: pointer;
  border: none;
  box-shadow: none;
  border-radius: var(--radius-lg);
  min-height: 64px;
  padding: var(--space-2) var(--space-3);
  transition: background var(--ease-out);
}
.course-row .course-item:hover {
  transform: none;
  box-shadow: none;
  background: var(--surface-soft);
}
.course-row .course-item:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}

/* Course icon text character */
.course-icon {
  font-family: var(--font-sans);
  font-size: var(--text-lg);
  font-weight: 900;
}

/* ── More button ── */
.more-btn {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--ease-out), color var(--ease-out);
}
.more-btn:hover {
  background: var(--surface-strong);
  color: var(--text-main);
}

/* ── Dropdown menu (anchored below more-btn) ── */
.course-menu {
  position: absolute;
  right: var(--space-2);
  top: calc(100% + 4px);
  z-index: 30;
  display: grid;
  gap: 2px;
  min-width: 180px;
  padding: 6px;
  border-radius: var(--radius-lg);
  background: var(--surface);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
}
.menu-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 38px;
  padding: 0 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: background var(--ease-out), color var(--ease-out);
}
.menu-option:hover:not(:disabled) {
  background: var(--surface-soft);
  color: var(--text-main);
}
.menu-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.menu-danger {
  color: var(--rose);
}
.menu-danger:hover:not(:disabled) {
  background: var(--rose-soft);
  color: var(--rose);
}
.menu-divider {
  height: 1px;
  margin: 4px 8px;
  background: var(--line-soft);
}

/* ── Buttons ── */
.btn-solid {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #ffffff;
  font-size: var(--text-sm);
  font-weight: 800;
  cursor: pointer;
  transition: transform var(--ease-out), box-shadow var(--ease-out);
  box-shadow: var(--shadow-primary);
}
.btn-solid:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-primary);
}
.btn-solid:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 800;
  cursor: pointer;
  transition: background var(--ease-out), border-color var(--ease-out), color var(--ease-out);
}
.btn-outline:hover:not(:disabled) {
  background: var(--primary-soft);
  border-color: var(--primary);
  color: var(--primary-strong);
}
.btn-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-sm {
  min-height: 36px;
  padding: 0 12px;
  font-size: var(--text-xs);
}
.btn-block {
  width: 100%;
}

/* ── Modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.modal-card {
  width: 100%;
  max-width: 430px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  box-shadow: var(--shadow-modal);
  max-height: calc(100dvh - var(--space-8));
  overflow-y: auto;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-title {
  margin: 0;
  font-family: var(--font-sans);
  font-size: var(--text-xl);
  font-weight: 900;
  color: var(--text-main);
}
.modal-close {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--ease-out), color var(--ease-out);
}
.modal-close:hover {
  background: var(--surface-strong);
  color: var(--text-main);
}
.form-field {
  display: grid;
  gap: 6px;
}
.form-textarea {
  min-height: 72px;
  padding: 10px 14px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.55;
}
.modal-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

/* ── Mobile compact (≤400px / 6.3 inch) ── */
@media (max-width: 400px) {
  .modal-actions {
    grid-template-columns: 1fr;
  }
  .course-menu {
    right: var(--space-1);
    min-width: 160px;
  }
  .course-row .course-item {
    min-height: 60px;
    padding: var(--space-2);
  }
  .empty-actions {
    flex-direction: column;
    width: 100%;
  }
  .empty-actions button {
    width: 100%;
  }
}

/* A-plan overrides: restrained surfaces, clear hierarchy, and 44px touch targets. */
.library-page {
  gap: 16px;
  padding-bottom: calc(var(--nav-bottom-clearance) + 24px);
  font-family: var(--font-sans);
}
.library-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.library-head > div { min-width: 0; }
.eyebrow {
  margin: 0 0 4px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
}
.library-title {
  margin: 0;
  color: var(--text-main);
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
}
.library-count {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}
.primary-action,
.practice-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 44px;
  border: 1px solid var(--primary);
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}
.primary-action { padding: 0 14px; flex-shrink: 0; }
.primary-action:hover,
.practice-action:hover:not(:disabled) { background: var(--primary-strong); }
.library-tools { display: flex; align-items: center; gap: 10px; }
.library-tools .search-bar {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--line-soft);
  border-radius: 6px;
  background: var(--surface);
  box-shadow: none;
}
.search-input { min-height: 28px; font-size: 14px; }
.search-clear { width: 36px; height: 36px; border-radius: 6px; }
.library-tools .seg { flex-shrink: 0; border-radius: 6px; }
.library-tools .seg-item { min-height: 40px; padding: 0 12px; border-radius: 4px; }
.lib-summary { padding: 0; }
.section-head { margin-top: 4px; }
.section-title { font-family: var(--font-sans); font-size: 16px; font-weight: 800; }
.course-list { gap: 8px; }
.course-row {
  border-radius: 6px;
  box-shadow: none;
}
.course-row:hover { box-shadow: var(--shadow-xs); }
.course-row .course-item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto auto minmax(104px, auto) auto auto;
  align-items: center;
  gap: 12px;
  min-height: 72px;
  padding: 10px 12px;
  border-radius: 6px;
}
.course-icon { width: 36px; height: 36px; border-radius: 4px; font-family: var(--font-sans); font-size: 15px; }
.course-info { min-width: 0; }
.course-info strong { font-size: 14px; }
.course-subline { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.course-stat { display: inline-flex; align-items: baseline; gap: 3px; color: var(--text-main); white-space: nowrap; }
.course-stat strong { font-size: 16px; font-weight: 800; }
.course-stat small { color: var(--text-muted); font-size: 11px; }
.visibility-label { min-width: 40px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.visibility-label.is-public { color: var(--primary-strong); }
.visibility-label.is-private { color: var(--text-muted); }
.course-recent { color: var(--text-muted); font-size: 12px; white-space: nowrap; }
.practice-action { min-width: 76px; padding: 0 10px; }
.practice-action:disabled { border-color: var(--line-soft); background: var(--surface-soft); color: var(--text-placeholder); cursor: not-allowed; }
.more-btn { width: 44px; height: 44px; border-radius: 6px; }
.course-menu {
  top: auto;
  right: 10px;
  bottom: 10px;
  min-width: 196px;
  max-width: calc(100% - 20px);
  padding: 6px;
  border-radius: 6px;
}
.menu-option { min-height: 44px; border-radius: 4px; }
.btn-solid { background: var(--primary); border-radius: 6px; box-shadow: none; }
.btn-solid:hover:not(:disabled) { transform: none; box-shadow: none; background: var(--primary-strong); }
.modal-overlay { backdrop-filter: none; -webkit-backdrop-filter: none; }
.modal-card { border-radius: 6px; }
.modal-title { font-family: var(--font-sans); }
.modal-close { width: 44px; height: 44px; border-radius: 6px; }

@media (max-width: 700px) {
  .library-tools { align-items: stretch; flex-direction: column; }
  .library-tools .seg { align-self: flex-start; }
}
@media (max-width: 400px) {
  .library-head { align-items: flex-start; }
  .library-title { font-size: 24px; }
  .primary-action { padding: 0 10px; }
  .course-row .course-item {
    grid-template-columns: 36px minmax(0, 1fr) auto auto;
    gap: 8px;
    min-height: 72px;
    padding: 10px 8px;
  }
  .course-stat { grid-column: 3; grid-row: 1; }
  .practice-action { display: none; }
  .visibility-label, .course-recent { display: none; }
  .course-subline { font-size: 11px; }
  .course-menu { right: 8px; bottom: 8px; min-width: 188px; }
}
</style>
