<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  ArrowRight,
  BookOpen,
  ClipboardList,
  FileUp,
  Mic,
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

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了";
  if (hour < 12) return "早上好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

const greetingDate = computed(() => new Intl.DateTimeFormat("zh-CN", {
  month: "long",
  day: "numeric",
  weekday: "short",
}).format(new Date()));

// The home banner stays usable before the account store has finished hydrating.
const greetingName = computed(() => "同学");
const avatarChar = computed(() => "学");

const statCards = computed(() => [
  { label: "今日练习", value: stats.value.todayCount, suffix: "" },
  { label: "总题数", value: stats.value.totalCount, suffix: "" },
  { label: "正确率", value: accuracyDisplay.value, suffix: "" },
  // The current stats API has no streak field. Keep this visibly unavailable
  // instead of deriving a fictional streak from total practice records.
  { label: "连续学习", value: null, suffix: "" },
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

function courseProgress(course: Course) {
  if (!course.question_count) return 0;
  return Math.min(100, Math.round(((course.practice_count || 0) / course.question_count) * 100));
}

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
  <section class="home-page" data-reference-page="home">
    <header class="home-hero fade-up">
      <div class="home-hero__top">
        <div>
          <p class="home-hero__eyebrow">{{ greetingDate }}</p>
          <h1>{{ greeting }}，{{ greetingName }}</h1>
          <p>从一小步开始，今天也会有收获。</p>
        </div>
        <span class="home-hero__avatar" :aria-label="`${greetingName}的头像`">{{ avatarChar }}</span>
      </div>
      <button
        class="home-search-entry"
        data-home-search
        type="button"
        @click="replaceTo('/courses')"
      >
        <Search :size="15" :stroke-width="2.4" />
        <span>搜索题库、课程、题目</span>
        <Mic class="home-search-entry__mic" :size="17" :stroke-width="2.2" aria-hidden="true" />
      </button>
    </header>

    <nav class="quick-grid fade-up d1" aria-label="快捷操作">
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
        <div v-for="card in statCards" :key="card.label" class="overview-stat" :data-stat-streak="card.label === '连续学习' ? true : undefined">
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
    <div v-if="recentCourses.length > 0" class="course-list home-course-list fade-up d3">
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
              {{ course.question_count ?? 0 }} 题 · 已练 {{ course.practice_count ?? 0 }} 次 · {{ formatCourseDate(course) }}
            </span>
            <span class="course-progress" aria-label="练习覆盖进度">
              <i :style="{ width: `${courseProgress(course)}%` }"></i>
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

    <button
      class="home-recommendation fade-up d4"
      data-home-recommendation
      type="button"
      @click="goTo(recentCourses[0] ? `/courses/${recentCourses[0].id}/practice` : '/courses')"
    >
      <span class="home-recommendation__spark">✦</span>
      <span class="home-recommendation__copy">
        <small class="home-recommendation__tag">每日一练</small>
        <strong>{{ recentCourses[0] ? getCourseDisplayName(recentCourses[0]) : "从题库开始" }}</strong>
        <small>{{ recentCourses[0] ? "继续完成今天的练习" : "选择一门题库，开始建立学习节奏" }}</small>
      </span>
      <ArrowRight :size="19" :stroke-width="2.4" aria-hidden="true" />
    </button>
  </section>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.home-hero {
  display: grid;
  gap: 16px;
  margin: -16px -16px 0;
  padding: 20px 18px 18px;
  border-radius: 0 0 28px 28px;
  background: linear-gradient(145deg, #10b981, #0f9d7a 60%, #0d9488);
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.home-hero__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.home-hero p,
.home-hero h1 { margin: 0; }
.home-hero__eyebrow { opacity: .82; font-size: 12px; font-weight: 700; }
.home-hero h1 { margin-top: 3px; font-size: 24px; letter-spacing: 0; }
.home-hero h1 + p { margin-top: 5px; opacity: .86; font-size: 12px; }
.home-hero__avatar {
  display: grid;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  place-items: center;
  border: 1px solid rgba(255,255,255,.42);
  border-radius: 50%;
  background: rgba(255,255,255,.18);
  color: #fff;
  font-weight: 850;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.34);
}

.home-search-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  margin-top: 0;
  border-radius: 8px;
  background: rgba(255,255,255,.96);
  border: 1px solid rgba(255,255,255,.68);
  color: var(--text-placeholder);
  font-size: 12px;
  font-weight: 600;
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: border-color var(--ease-out);
}

.home-search-entry__mic { margin-left: auto; color: var(--primary-strong); }

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

.course-progress {
  display: block;
  height: 5px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-soft);
}
.course-progress i { display: block; height: 100%; border-radius: inherit; background: var(--primary); }

.home-recommendation {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  width: 100%;
  margin-top: 4px;
  padding: 15px;
  border: 0;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary-soft), #eff6ff);
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
}
.home-recommendation__spark { color: var(--primary); font-size: 24px; }
.home-recommendation__copy { min-width: 0; }
.home-recommendation strong,
.home-recommendation small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-recommendation strong { font-size: 14px; }
.home-recommendation small { margin-top: 3px; color: var(--text-muted); font-size: 11px; }
.home-recommendation .home-recommendation__tag {
  display: inline-flex;
  width: fit-content;
  margin: 0 0 4px;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
}
.home-recommendation :deep(svg) { color: var(--primary-strong); }

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

.home-hero { padding-inline: 20px; border-radius: 0 0 24px 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.home-hero__avatar { border: 2px solid rgba(255,255,255,.72); }
.home-search-entry { border-color: rgba(255,255,255,.42); background: rgba(255,255,255,.18); color: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,.35); }
.home-search-entry span { color: rgba(255,255,255,.9); }
.quick { border-color: var(--glass-border); background: var(--glass-card); box-shadow: var(--shadow-card), var(--glass-inner-highlight); }
.quick:nth-child(2) .quick-ico { color: #2563eb; background: #eff6ff; }
.quick:nth-child(3) .quick-ico { color: #d97706; background: #fffbeb; }
.quick:nth-child(4) .quick-ico { color: #dc2626; background: #fef2f2; }
.overview-surface, .home-course-list .course-item, .home-recommendation { border-color: var(--glass-border); background: var(--glass-card); box-shadow: var(--shadow-card), var(--glass-inner-highlight); backdrop-filter: blur(18px) saturate(150%); -webkit-backdrop-filter: blur(18px) saturate(150%); }
.home-recommendation { border-radius: 12px; }
</style>
