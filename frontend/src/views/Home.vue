<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  BookOpen,
  ClipboardList,
  FileUp,
  MessageCircle,
  Search,
  Target,
  TrendingUp,
} from "@lucide/vue";

import { getMyCourses } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { useStudyOverview } from "../composables/useStudyOverview";
import { useAppNavigation } from "../composables/useAppNavigation";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";

const { replaceTo } = useAppNavigation();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();

const courses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null || rate === undefined) return "--";
  return `${(rate * 100).toFixed(0)}%`;
});

const statCards = computed(() => [
  { label: "今日已刷", value: stats.value.todayCount, suffix: "题" },
  { label: "总刷题", value: stats.value.totalCount, suffix: "题" },
  { label: "正确率", value: accuracyDisplay.value, suffix: "" },
  { label: "近 7 日", value: stats.value.recentCount7d, suffix: "题" },
]);

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
  fetchAll();
  fetchRecentCourses();
});
</script>

<template>
  <section class="home-page">
    <button
      class="home-search-entry fade-up"
      data-home-search
      type="button"
      @click="replaceTo('/courses')"
    >
      <Search :size="15" :stroke-width="2.4" />
      <span>搜索题库、课程、题目</span>
    </button>

    <nav class="quick-grid fade-up d1" aria-label="核心入口">
      <button
        v-for="item in coreActions"
        :key="item.label"
        class="quick"
        type="button"
        @click="goTo(item.to)"
      >
        <span class="quick-ico">
          <component :is="item.icon" :size="18" :stroke-width="2.3" />
        </span>
        <span class="quick-label">{{ item.label }}</span>
        <span class="quick-desc">{{ item.desc }}</span>
      </button>
    </nav>

    <button
      class="home-ai-chat fade-up d2"
      data-home-ai-chat
      type="button"
      aria-label="打开 AI 学习助手"
      @click="goTo('/chat')"
    >
      <span class="home-ai-chat__icon" aria-hidden="true">
        <MessageCircle :size="19" :stroke-width="2.2" />
      </span>
      <span class="home-ai-chat__copy">
        <strong>AI 学习助手</strong>
        <span>问知识点、讲题目、做复习</span>
      </span>
      <span class="home-ai-chat__action" aria-hidden="true">去对话</span>
    </button>

    <div class="section-head fade-up d3">
      <h3 class="section-title">学习概览</h3>
      <button
        class="section-more"
        type="button"
        @click="goTo({ name: 'study-overview', query: { from: 'home' } })"
      >
        查看全部
      </button>
    </div>
    <div class="overview-surface fade-up d3">
      <p v-if="loading" class="overview-state">学习数据加载中...</p>
      <p v-else-if="errorMessage" class="overview-state overview-state--error">{{ errorMessage }}</p>
      <div v-else class="overview-grid">
        <div v-for="card in statCards" :key="card.label" class="overview-stat">
          <strong>{{ card.value ?? "--" }}</strong>
          <span>{{ card.label }}{{ card.suffix }}</span>
        </div>
      </div>
    </div>

    <div class="section-head fade-up d3">
      <h3 class="section-title">最近题库</h3>
      <button
        class="section-more"
        type="button"
        @click="replaceTo('/courses')"
      >
        查看全部
      </button>
    </div>

    <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
    <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

    <!-- Empty state -->
    <div
      v-if="!coursesLoading && !coursesError && recentCourses.length === 0"
      class="empty-state fade-up d3"
    >
      <BookOpen :size="36" :stroke-width="1.7" />
      <strong>还没有可练习题库</strong>
      <p>导入资料后，这里会显示最近学习的题库。</p>
      <div class="empty-actions">
        <button class="empty-btn empty-btn--primary" type="button" @click="goTo('/import')">
          去导入
        </button>
        <button class="empty-btn" type="button" @click="goTo('/courses')">浏览题库</button>
      </div>
    </div>

    <!-- Course list -->
    <div v-if="recentCourses.length > 0" class="course-list fade-up d3">
      <div
        v-for="course in recentCourses"
        :key="course.id"
        class="course-item"
      >
        <button
          class="course-main"
          type="button"
          @click="goTo(`/courses/${course.id}`)"
        >
          <span class="course-icon">
            <BookOpen :size="18" :stroke-width="2.2" />
          </span>
          <div class="course-info">
            <strong>{{ getCourseDisplayName(course) }}</strong>
            <span>
              {{ course.question_count ?? 0 }} 题 ·
              {{ course.visibility === "public" ? "公开" : "私有" }} ·
              {{ formatCourseDate(course) }}
            </span>
          </div>
        </button>
        <button
          class="course-action"
          type="button"
          :aria-label="`开始练习：${getCourseDisplayName(course)}`"
          @click="goTo(`/courses/${course.id}/practice`)"
        >
          开始练习
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.home-search-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  margin-top: var(--space-2);
  border-radius: 8px;
  background: var(--surface);
  border: 1px solid var(--line-soft);
  color: var(--text-placeholder);
  font-size: 12px;
  font-weight: 600;
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: border-color var(--ease-out);
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

.quick {
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

.home-ai-chat {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 68px;
  margin: var(--space-3) 0 var(--space-5);
  padding: 10px 12px;
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-main);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  text-align: left;
  transition: border-color var(--ease-out), background var(--ease-out), transform var(--ease-out);
}

.home-ai-chat:hover { border-color: var(--primary); background: var(--primary-soft); }
.home-ai-chat:active { transform: scale(0.99); }

.home-ai-chat__icon {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 12px;
  background: var(--primary-soft);
  color: var(--primary);
}

.home-ai-chat__copy {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.home-ai-chat__copy strong { font-size: var(--text-sm); font-weight: 800; }
.home-ai-chat__copy span { overflow: hidden; color: var(--text-muted); font-size: var(--text-xs); text-overflow: ellipsis; white-space: nowrap; }
.home-ai-chat__action { margin-left: auto; color: var(--primary); font-size: var(--text-xs); font-weight: 800; white-space: nowrap; }

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

.overview-state--error { color: var(--rose); }

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.overview-stat {
  min-width: 0;
  padding: 6px 4px;
  text-align: center;
}

.overview-stat strong,
.overview-stat span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-stat strong { color: var(--text-main); font-size: var(--text-lg); }
.overview-stat span { margin-top: 4px; color: var(--text-muted); font-size: var(--text-xs); }

/* ── Course list layout ── */
.course-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.course-item {
  border-radius: 8px;
}

.course-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
  min-height: 44px;
  background: transparent;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.course-action {
  flex-shrink: 0;
  min-height: 44px;
  padding: 6px 12px;
  border-radius: 8px;
  background: var(--primary);
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  border: none;
  box-shadow: none;
  cursor: pointer;
  white-space: nowrap;
  transition: transform var(--ease-out), box-shadow var(--ease-out);
}

.course-action:hover {
  background: var(--primary-strong);
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
  transition: background var(--ease-out), border-color var(--ease-out);
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
  .overview-grid { gap: 0; }
  .overview-stat strong { font-size: var(--text-base); }
  .course-item { gap: 8px; }
  .course-action { padding-inline: 10px; }
}
</style>
