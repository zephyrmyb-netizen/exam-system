<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  BookOpen,
  ClipboardList,
  Eye,
  FileText,
  FileUp,
  Globe,
  Lock,
  MoreHorizontal,
  Pencil,
  Play,
  ScanLine,
  Target,
  Trash2,
  TrendingUp,
} from "@lucide/vue";

import { getMyCourses } from "../api/courses";
import request, { getErrorMessage } from "../api/request";
import { useAppNavigation } from "../composables/useAppNavigation";
import { useConfirmDialog } from "../stores/confirmDialog";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { openGlobalSearch } from "../utils/globalSearch";

const { replaceTo } = useAppNavigation();
const confirmDialog = useConfirmDialog();

const courses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");
const openCourseMenuId = ref<number | null>(null);
const publishLoading = ref<number | null>(null);
const deleteLoading = ref<number | null>(null);

const recentCourses = computed(() => {
  const seen = new Set<number | string>();
  return [...courses.value]
    .filter((course) => {
      if (!isPracticeReadyCourse(course) || seen.has(course.id)) return false;
      seen.add(course.id);
      return true;
    })
    .sort((a, b) => {
      const aTime = new Date(a.last_practiced_at || a.created_at || 0).getTime();
      const bTime = new Date(b.last_practiced_at || b.created_at || 0).getTime();
      return bTime - aTime;
    })
    .slice(0, 3);
});

const coreActions = [
  {
    label: "AI 导入",
    desc: "上传 Word/PPT，自动整理题库",
    icon: FileUp,
    to: "/import",
  },
  {
    label: "开始练习",
    desc: "选择题库后开始练习",
    icon: ClipboardList,
    to: "/practice",
  },
  {
    label: "正式考试",
    desc: "进入已有考试安排",
    icon: Target,
    to: "/exams",
  },
  {
    label: "学习概览",
    desc: "查看学习数据",
    icon: TrendingUp,
    to: { name: "study-overview", query: { from: "home" } },
  },
];

function goTo(target: RouteLocationRaw) {
  replaceTo(target);
}

function formatCourseDate(course: Course) {
  const raw = course.last_practiced_at || course.created_at;
  if (!raw) return "暂无记录";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return "暂无记录";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" }).format(date);
}

function toggleCourseMenu(courseId: number) {
  openCourseMenuId.value = openCourseMenuId.value === courseId ? null : courseId;
}

function closeCourseMenu() {
  openCourseMenuId.value = null;
}

function startRecentCoursePractice(course: Course) {
  if (!isPracticeReadyCourse(course)) return;
  closeCourseMenu();
  goTo({ name: "course-practice", params: { courseId: course.id }, query: { from: "home" } });
}

function viewRecentCourse(course: Course, edit = false) {
  closeCourseMenu();
  goTo({
    name: "course-detail",
    params: { courseId: course.id },
    query: edit ? { from: "home", edit: "1" } : { from: "home" },
  });
}

async function toggleRecentCoursePublish(course: Course) {
  closeCourseMenu();
  publishLoading.value = course.id;
  coursesError.value = "";
  try {
    const endpoint = course.visibility === "public" ? "unpublish" : "publish";
    const { data } = await request.post<Course>(`/courses/${course.id}/${endpoint}`);
    course.visibility = data.visibility || (endpoint === "publish" ? "public" : "private");
  } catch (error) {
    coursesError.value = getErrorMessage(error, "操作失败，请稍后重试。");
  } finally {
    publishLoading.value = null;
  }
}

async function deleteRecentCourse(course: Course) {
  closeCourseMenu();
  const confirmed = await confirmDialog.confirm({
    title: "删除题库",
    message: `确定删除「${getCourseDisplayName(course)}」吗？\n其中 ${course.question_count ?? 0} 道题会一起移除。`,
    confirmText: "删除",
    cancelText: "取消",
    tone: "danger",
  });
  if (!confirmed) return;

  deleteLoading.value = course.id;
  coursesError.value = "";
  try {
    await request.delete(`/courses/${course.id}`);
    courses.value = courses.value.filter((item) => item.id !== course.id);
  } catch (error) {
    coursesError.value = getErrorMessage(error, "删除失败，请稍后重试。");
  } finally {
    deleteLoading.value = null;
  }
}

async function fetchRecentCourses() {
  coursesLoading.value = true;
  coursesError.value = "";

  try {
    courses.value = await getMyCourses();
  } catch (error) {
    coursesError.value = getErrorMessage(error, "题库加载失败，请稍后重试。");
  } finally {
    coursesLoading.value = false;
  }
}

onMounted(() => {
  fetchRecentCourses();
});
</script>

<template>
  <section class="home-page" data-reference-page="home">
    <header class="home-hero fade-up">
      <button class="home-search-entry" data-home-search type="button" @click="openGlobalSearch">
        <span class="home-search-entry__scan" aria-hidden="true">
          <ScanLine :size="20" :stroke-width="2.2" />
        </span>
        <span>搜索题库、文档、作者</span>
      </button>
    </header>

    <nav class="quick-grid fade-up d1" data-testid="home-shortcuts" aria-label="快捷操作">
      <button v-for="item in coreActions" :key="item.label" class="quick" type="button" @click="goTo(item.to)">
        <span class="quick-ico">
          <component :is="item.icon" :size="18" :stroke-width="2.3" />
        </span>
        <span class="quick-label">{{ item.label }}</span>
        <span class="quick-desc">{{ item.desc }}</span>
      </button>
    </nav>

    <div class="section-head fade-up d3" data-testid="home-recent">
      <h3 class="section-title">最近题库</h3>
      <button class="section-more" type="button" @click="replaceTo('/courses')">查看全部</button>
    </div>

    <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
    <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

    <!-- Empty state -->
    <div v-if="!coursesLoading && !coursesError && recentCourses.length === 0" class="empty-state fade-up d3">
      <BookOpen :size="36" :stroke-width="1.7" />
      <strong>还没有可练习题库</strong>
      <p>导入资料后，这里会显示最近学习的题库。</p>
      <div class="empty-actions">
        <button class="empty-btn empty-btn--primary" type="button" @click="goTo('/import')">去导入</button>
        <button class="empty-btn" type="button" @click="goTo('/courses')">浏览题库</button>
      </div>
    </div>

    <!-- Course list -->
    <div
      v-if="recentCourses.length > 0"
      class="course-list home-course-list fade-up d3"
      :class="{ 'home-course-list--menu-open': openCourseMenuId !== null }"
    >
      <div
        v-for="course in recentCourses"
        :key="course.id"
        class="course-item"
        :class="{ 'home-course-item--menu-open': openCourseMenuId === course.id }"
      >
        <button
          class="course-main"
          type="button"
          :aria-label="`开始练习：${getCourseDisplayName(course)}`"
          @click="goTo({ name: 'course-practice', params: { courseId: course.id }, query: { from: 'home' } })"
        >
          <span class="course-icon" data-home-course-icon aria-hidden="true">
            <FileText :size="20" :stroke-width="2.25" />
          </span>
          <div class="course-info">
            <strong>{{ getCourseDisplayName(course) }}</strong>
            <span>
              {{ course.question_count ?? 0 }} 题 · 已练 {{ course.practice_count ?? 0 }} 次 ·
              {{ formatCourseDate(course) }}
            </span>
          </div>
        </button>
        <button
          class="home-course-more"
          data-home-course-more
          type="button"
          :aria-label="`管理题库：${getCourseDisplayName(course)}`"
          :aria-expanded="openCourseMenuId === course.id"
          @click.stop="toggleCourseMenu(course.id)"
        >
          <MoreHorizontal :size="18" :stroke-width="2.5" />
        </button>
        <div v-if="openCourseMenuId === course.id" class="home-course-menu">
          <button class="home-menu-option" type="button" @click.stop="startRecentCoursePractice(course)">
            <Play :size="15" :stroke-width="2.5" />
            开始练习
          </button>
          <button class="home-menu-option" type="button" @click.stop="viewRecentCourse(course, true)">
            <Eye :size="15" :stroke-width="2.5" />
            查看题目
          </button>
          <div class="home-menu-divider"></div>
          <button class="home-menu-option" type="button" @click.stop="viewRecentCourse(course)">
            <Pencil :size="15" :stroke-width="2.5" />
            编辑
          </button>
          <button
            class="home-menu-option"
            type="button"
            :disabled="publishLoading === course.id"
            @click.stop="toggleRecentCoursePublish(course)"
          >
            <Globe v-if="course.visibility !== 'public'" :size="15" :stroke-width="2.5" />
            <Lock v-else :size="15" :stroke-width="2.5" />
            {{ course.visibility === "public" ? "撤回公开" : "发布到公共题库" }}
          </button>
          <div class="home-menu-divider"></div>
          <button
            class="home-menu-option home-menu-option--danger"
            type="button"
            :disabled="deleteLoading === course.id"
            @click.stop="deleteRecentCourse(course)"
          >
            <Trash2 :size="15" :stroke-width="2.5" />
            {{ deleteLoading === course.id ? "删除中..." : "删除" }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 0 !important;
}

.home-hero {
  display: grid;
  margin: 0;
  padding: 8px 0 4px;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  color: var(--text-primary);
  box-shadow: none !important;
}

.home-search-entry {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 46px;
  padding: 0 11px;
  margin-top: 0;
  border: 1px solid #e3eaf2 !important;
  border-radius: var(--radius-full);
  background: #ffffff !important;
  color: #64748b;
  font-size: 15px;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(71, 85, 105, 0.08) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  cursor: pointer;
  transition: border-color var(--ease-out);
}

.home-search-entry__mic {
  margin-left: auto;
  color: var(--primary-strong);
}

.home-search-entry:hover {
  border-color: var(--primary-border);
}

.home-search-entry :deep(svg) {
  color: var(--text-placeholder);
}

.quick-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.home-page .quick {
  min-height: 116px;
  padding: var(--space-3) 8px;
  border-radius: 8px;
  font-size: var(--text-sm);
}

.quick-ico {
  background: var(--primary);
  box-shadow: none;
}

.quick-label {
  font-size: var(--text-sm);
  font-weight: 700;
  text-align: center;
}

.quick-desc {
  max-width: 100%;
  overflow: hidden;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.4;
  text-overflow: ellipsis;
  text-align: center;
  white-space: nowrap;
}

.overview-surface {
  min-height: 92px;
  margin-bottom: var(--space-5);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.overview-state {
  display: grid;
  min-height: 68px;
  margin: 0;
  place-items: center;
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-align: center;
}

.overview-state--error {
  color: var(--rose);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-2);
}

.overview-grid :deep(.stat-grid__item) {
  min-height: 64px;
  padding: 6px 4px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  box-shadow: none;
}

.overview-grid :deep(.stat-grid__value) {
  font-size: var(--text-lg);
}

/* ── Course list layout ── */
.course-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.course-item {
  display: flex;
  align-items: center;
  border-radius: 8px;
}

.home-course-list .course-icon {
  background: var(--primary);
}

.course-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  width: auto;
  min-width: 0;
  min-height: 44px;
  background: transparent;
  border: none;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  color: inherit;
}
.home-course-more {
  display: grid;
  width: 32px;
  min-width: 32px;
  height: 32px;
  margin-right: 10px;
  padding: 0;
  place-items: center;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}
.home-course-more:hover {
  background: var(--surface-soft);
  color: var(--text-main);
}
.home-course-list--menu-open {
  overflow: visible !important;
}
.home-course-item--menu-open {
  position: relative;
  z-index: 90;
}
.home-course-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 10px;
  z-index: 100;
  display: grid;
  gap: 2px;
  min-width: 196px;
  max-width: calc(100% - 20px);
  padding: 6px;
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.home-menu-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 44px;
  padding: 0 12px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}
.home-menu-option:hover:not(:disabled) {
  background: var(--surface-soft);
  color: var(--text-main);
}
.home-menu-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.home-menu-option--danger {
  color: var(--rose);
}
.home-menu-option--danger:hover:not(:disabled) {
  background: var(--rose-soft);
  color: var(--rose);
}
.home-menu-divider {
  height: 1px;
  margin: 4px 8px;
  background: var(--line-soft);
}


/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 16px;
  text-align: center;
  color: var(--text-muted);
}

.empty-state :deep(svg) {
  color: var(--text-muted);
  opacity: 0.5;
}

.empty-state strong {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: 800;
  color: var(--text-main);
}

.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.empty-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.empty-btn {
  min-height: 44px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    background var(--ease-out),
    border-color var(--ease-out);
}

.empty-btn--primary {
  background: var(--primary);
  color: #ffffff;
  border-color: transparent;
  box-shadow: none;
  transition: background var(--ease-out);
}

.empty-btn--primary:hover {
  background: var(--primary-strong);
}

@media (max-width: 420px) {
  .overview-grid {
    gap: 0;
  }
  .overview-grid :deep(.stat-grid__value) {
    font-size: var(--text-base);
  }
  .course-item {
    gap: 8px;
  }
}

.home-search-entry {
  color: #64748b;
}
.home-search-entry span {
  color: inherit;
}
.home-search-entry__scan {
  display: grid;
  place-items: center;
  min-width: 38px;
  height: 24px;
  border-right: 1px solid #e2e8f0;
  color: #218bf2;
}
.quick {
  border-color: var(--glass-border);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
}
.quick:nth-child(2) .quick-ico {
  color: #2563eb;
  background: #eff6ff;
}
.quick:nth-child(3) .quick-ico {
  color: #d97706;
  background: #fffbeb;
}
.quick:nth-child(4) .quick-ico {
  color: #dc2626;
  background: #fef2f2;
}
.overview-surface,
.home-course-list .course-item,
.home-recommendation {
  border-color: var(--glass-border);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
}
.home-recommendation {
  border-radius: 12px;
}

/* Keep the home header compact: search is the only content in this band. */
.home-hero {
  min-height: 0 !important;
  gap: 0;
  padding: 8px 0 4px !important;
  box-shadow: none !important;
}
.home-hero h1 {
  margin-top: 2px;
  font-size: 22px;
  line-height: 1.22;
}
.home-search-entry {
  min-height: 46px !important;
  border-radius: var(--radius-full);
  background: #ffffff !important;
  color: #64748b !important;
}
.home-search-entry span,
.home-search-entry :deep(svg) {
  color: inherit !important;
}
.home-search-entry__scan,
.home-search-entry__scan :deep(svg) {
  color: #218bf2 !important;
}
.quick-grid {
  position: relative;
  z-index: 1;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0 !important;
  margin: 4px 0 0;
  padding: 8px 2px;
  border-radius: var(--radius-lg);
}
.quick {
  min-height: 76px !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 4px;
  padding: 4px 2px !important;
  border-radius: 0 !important;
}
.home-page .quick:nth-child(odd),
.home-page .quick:nth-child(n + 3) {
  border: 0 !important;
}
.quick-ico {
  width: 36px;
  height: 36px;
}
.quick-label {
  font-size: 11px;
  text-align: center;
  white-space: nowrap;
}
.quick-desc {
  display: none;
}
.overview-surface {
  min-height: 92px;
  margin: 10px 0 2px;
  padding: 10px 8px;
  border-radius: var(--radius-lg);
}
.home-page .section-head,
.home-course-list,
.home-page > .status-banner,
.home-page > .empty-state {
  margin-inline: 0;
}
.home-page .section-head {
  margin-block: 8px 6px;
}
.home-course-list {
  margin-top: 0;
}
.home-recommendation {
  margin: 16px 0;
  width: 100%;
}

/* 首页统一使用圆角方形的内容与图标底座；搜索和进度条保留胶囊形。 */
.home-page .quick-grid,
.home-page .home-course-list .course-item,
.home-page .home-recommendation {
  border-radius: 16px !important;
}
.home-page .quick-ico,
.home-page .course-icon {
  border-radius: 12px !important;
}
.home-page .course-action,
.home-page .home-recommendation__tag {
  border-radius: 10px;
}

/* Keep the homepage dense enough for the first screen without losing touch targets. */
.home-page .quick-grid {
  padding: 6px 2px;
}
.home-page .quick {
  min-height: 68px !important;
  gap: 3px;
}
.home-page .quick-ico {
  width: 32px;
  height: 32px;
}
.home-page .quick-ico :deep(svg) {
  width: 17px;
  height: 17px;
}
.home-page .home-course-list {
  gap: 8px;
}
.home-page .home-course-list .course-item {
  padding: 0;
}
.home-page .home-course-list .course-main {
  gap: 10px;
  min-height: 76px;
  padding: 8px 12px;
}
.home-page .home-course-list .course-icon {
  width: 40px;
  height: 40px;
}
.home-page .home-course-list .course-icon :deep(svg) {
  width: 19px;
  height: 19px;
}
.home-page .home-course-list .course-info {
  gap: 1px;
}
.home-page .home-course-list .course-info strong {
  font-size: 15px;
}
.home-page .home-recommendation {
  gap: 9px;
  margin: 10px 0 12px;
  padding: 11px 13px;
}
.home-page .home-recommendation__spark {
  font-size: 20px;
}
</style>
