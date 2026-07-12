<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  BookOpen,
  ClipboardList,
  FileUp,
  Search,
  Target,
  TrendingUp,
} from "@lucide/vue";

import { getMyCourses } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { useStudyOverview } from "../composables/useStudyOverview";
import { useAppNavigation } from "../composables/useAppNavigation";
import { useAuth } from "../stores/auth";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";

const { replaceTo } = useAppNavigation();
const { user } = useAuth();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();

const courses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const usernameText = computed(() => user.value?.username || "同学");

const dateText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(new Date()),
);

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

void statCards.value;

const heatmapData = computed(() => {
  const today = Number(stats.value.todayCount || 0);
  const recent = Number(stats.value.recentCount7d || 0);
  const base = Math.max(Math.floor(Math.max(recent - today, 0) / 6), 0);
  const remainder = Math.max(recent - today - base * 5, 0);
  return [base, base, base, base, base, remainder, today];
});

function heatmapClass(count: number): string {
  if (count >= 10) return "bg-blue-600";
  if (count >= 5) return "bg-blue-400";
  if (count > 0) return "bg-blue-200";
  return "bg-slate-200";
}

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

const heroActions = [
  {
    label: "AI 导入",
    desc: "上传 Word/PPT，自动整理题库",
    icon: FileUp,
    to: "/import",
    badge: "推荐",
  },
  {
    label: "开始练习",
    desc: "先选题库，再进入专业练习",
    icon: ClipboardList,
    to: "/practice",
  },
  {
    label: "正式考试",
    desc: "选择考试并提交成绩",
    icon: Target,
    to: "/exams",
  },
  {
    label: "学习概览",
    desc: "查看今日进度和正确率",
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
    <!-- Page Head -->
    <header class="page-head fade-up">
      <h2 class="ph-title">学习宝</h2>
      <p class="ph-sub">Scholar's Atelier · 墨韵书房</p>
      <span class="ph-date">{{ dateText }}</span>
    </header>

    <!-- Search entry (data-home-search required by UX tests) -->
    <button
      class="home-search-entry fade-up"
      data-home-search
      type="button"
      @click="replaceTo('/courses')"
    >
      <Search :size="15" :stroke-width="2.4" />
      <span>搜索题库、课程、题目</span>
    </button>

    <!-- Hero Banner -->
    <div class="hero-banner fade-up d1">
      <div class="hero-top">
        <p class="hero-greeting">
          {{ new Date().getHours() < 12 ? "Good morning" : "Good evening" }}
        </p>
        <span class="hero-date">{{ dateText }}</span>
      </div>
      <h3
        class="hero-title truncate"
        data-home-greeting
        :title="`${usernameText}，开始复习吧`"
      >
        {{ new Date().getHours() < 12 ? "早安" : "午安" }}，{{ usernameText }}
      </h3>
      <div class="hero-stats">
        <div class="hero-num">
          <strong>{{ stats.todayCount ?? "--" }}</strong>
          <span>今日练习</span>
        </div>
        <div class="hero-num">
          <strong>{{ stats.totalCount ?? "--" }}</strong>
          <span>累计题数</span>
        </div>
        <div class="hero-num">
          <strong>{{ accuracyDisplay }}</strong>
          <span>正确率</span>
        </div>
      </div>
    </div>

    <!-- Status messages -->
    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <!-- Quick Grid (4 colored icon buttons) -->
    <nav class="quick-grid fade-up d2">
      <button
        v-for="(item, idx) in heroActions"
        :key="item.label"
        class="quick"
        :class="['q-indigo', 'q-gold', 'q-rose', 'q-jade'][idx]"
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

    <!-- Section I: 学习连续 -->
    <div class="section-head fade-up d3">
      <span class="num">I</span>
      <h3 class="section-title">学习连续</h3>
      <button
        class="section-more"
        type="button"
        @click="goTo({ name: 'study-overview', query: { from: 'home' } })"
      >
        查看统计 ›
      </button>
    </div>
    <div class="streak-card fade-up d3">
      <div class="streak-main">
        <strong>{{ stats.recentCount7d ?? 0 }} 题</strong>
        <span>近 7 日累计</span>
      </div>
      <div class="streak-side">
        <strong>{{ stats.todayCount ?? 0 }}</strong>
        <span>今日</span>
      </div>
    </div>

    <!-- 7-day Heatmap -->
    <div class="heatmap fade-up d3">
      <span class="heatmap-label">7日</span>
      <div class="heatmap-bars">
        <span
          v-for="(count, index) in heatmapData"
          :key="index"
          class="heatmap-bar"
          :class="heatmapClass(count)"
          :title="`${count} 题`"
        />
      </div>
    </div>

    <!-- Section II: 最近题库 -->
    <div class="section-head fade-up d4">
      <span class="num">II</span>
      <h3 class="section-title">最近题库</h3>
      <button
        class="section-more"
        type="button"
        @click="replaceTo('/courses')"
      >
        查看全部 ›
      </button>
    </div>

    <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
    <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

    <!-- Empty state -->
    <div
      v-if="!coursesLoading && !coursesError && recentCourses.length === 0"
      class="empty-state fade-up d4"
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
    <div v-if="recentCourses.length > 0" class="course-list fade-up d4">
      <div
        v-for="(course, idx) in recentCourses"
        :key="course.id"
        class="course-item"
      >
        <button
          class="course-main"
          type="button"
          @click="goTo(`/courses/${course.id}`)"
        >
          <span class="course-icon" :class="`ci-${idx + 1}`">
            <BookOpen :size="22" :stroke-width="2.2" />
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
}

/* ── Search entry (kept for data-home-search test hook) ── */
.home-search-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  margin-top: var(--space-2);
  border-radius: 999px;
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
  border-color: var(--gold-border);
}

.home-search-entry :deep(svg) {
  color: var(--text-placeholder);
}

/* ── Quick grid description (visually hidden, kept in DOM for tests/a11y) ── */
.quick-label {
  font-size: 11px;
  font-weight: 700;
  text-align: center;
}

.quick-desc {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ── Heatmap (page-specific, not in component library) ── */
.heatmap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: var(--space-2);
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-soft);
}

.heatmap-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
}

.heatmap-bars {
  display: flex;
  flex: 1;
  gap: 4px;
}

.heatmap-bar {
  height: 16px;
  flex: 1;
  border-radius: 4px;
}

/* Heatmap bar colors — bridge Tailwind utility classes to design tokens */
.heatmap-bar.bg-blue-600 { background: var(--primary-strong); }
.heatmap-bar.bg-blue-400 { background: var(--primary); }
.heatmap-bar.bg-blue-200 { background: var(--primary-border); }
.heatmap-bar.bg-slate-200 { background: var(--line-soft); }

/* ── Course list layout ── */
.course-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.course-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.course-action {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  border: none;
  box-shadow: var(--shadow-primary);
  cursor: pointer;
  white-space: nowrap;
  transition: transform var(--ease-out), box-shadow var(--ease-out);
}

.course-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(67, 56, 202, 0.3);
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
  font-family: var(--font-serif);
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
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 700;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background var(--ease-out), border-color var(--ease-out);
}

.empty-btn--primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #ffffff;
  border-color: transparent;
  box-shadow: var(--shadow-primary);
  transition: transform var(--ease-out), box-shadow var(--ease-out);
}

.empty-btn--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(67, 56, 202, 0.3);
}
</style>
