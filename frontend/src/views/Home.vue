<script setup lang="ts">
defineOptions({ name: "Home" });

import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  BookOpen,
  ClipboardList,
  Copy,
  Eye,
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

import { createCourseShareLink, deleteCourse, publishCourse, unpublishCourse } from "../api/courses";
import { getStreak } from "../api/analytics";
import { getPracticeStats, getTodayReview } from "../api/practice";
import { getErrorMessage } from "../api/request";
import { useAppNavigation } from "../composables/useAppNavigation";
import { useMyCourses } from "../composables/useMyCourses";
import { useConfirmDialog } from "../stores/confirmDialog";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { getCourseIdentity } from "../utils/courseIdentity";
import CountUp from "../components/bits/CountUp.vue";
import GlassIcons from "../components/bits/GlassIcons.vue";
import SpecularButton from "../components/bits/SpecularButton.vue";
import SpotlightCard from "../components/bits/SpotlightCard.vue";
import { openGlobalSearch } from "../utils/globalSearch";

const { replaceTo } = useAppNavigation();
const confirmDialog = useConfirmDialog();

const {
  courses,
  loading: coursesLoading,
  hasLoaded: coursesLoaded,
  errorMessage: coursesError,
  fetchCourses: fetchRecentCourses,
} = useMyCourses();
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
    label: "学习小组",
    desc: "邀请码加入，共享题库与考试",
    icon: TrendingUp,
    to: { name: "study-groups", query: { from: "home" } },
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
  viewRecentCourse(course);
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
    if (course.visibility === "public") {
      const data = await unpublishCourse(course.id);
      course.visibility = data.visibility || "private";
    } else {
      const data = await publishCourse(course.id);
      course.visibility = data.visibility || "public";
    }
  } catch (error) {
    coursesError.value = getErrorMessage(error, "操作失败，请稍后重试。");
  } finally {
    publishLoading.value = null;
  }
}

async function copyRecentCourseShareLink(course: Course) {
  closeCourseMenu();
  coursesError.value = "";
  let link = `${window.location.origin}/courses/${course.id}`;
  try {
    if (course.visibility === "private") {
      let token = course.share_token;
      if (!token) {
        const { token: newToken } = await createCourseShareLink(course.id);
        token = newToken;
        course.share_token = token;
      }
      link = `${window.location.origin}/shared-courses/${token}`;
    }
    await navigator.clipboard.writeText(link);
  } catch {
    window.prompt("\u8bf7\u590d\u5236\u9898\u5e93\u5206\u4eab\u94fe\u63a5", link);
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
    await deleteCourse(course.id);
    courses.value = courses.value.filter((item) => item.id !== course.id);
  } catch (error) {
    coursesError.value = getErrorMessage(error, "删除失败，请稍后重试。");
  } finally {
    deleteLoading.value = null;
  }
}

const GLASS_ACTION_COLORS = ["indigo", "blue", "orange", "green"];
const glassActionItems = coreActions.map((action, index) => ({
  icon: action.icon,
  label: action.label,
  color: GLASS_ACTION_COLORS[index % GLASS_ACTION_COLORS.length],
}));

function onGlassActionSelect(item: { label: string }) {
  const action = coreActions.find((entry) => entry.label === item.label);
  if (action) goTo(action.to);
}

const reviewSummary = ref<{
  dueCount: number;
  wrongCount: number;
  streak: number;
  todayCount: number;
} | null>(null);

const reviewSubline = computed(() => {
  const summary = reviewSummary.value;
  if (!summary) return "";
  const parts: string[] = [];
  if (summary.wrongCount > 0) parts.push(`错题 ${summary.wrongCount} 道待巩固`);
  if (summary.streak > 0) parts.push(`已连续学习 ${summary.streak} 天`);
  if (summary.todayCount > 0) parts.push(`今日已练 ${summary.todayCount} 题`);
  return parts.join(" · ");
});

async function fetchReviewSummary() {
  const [review, streak, stats] = await Promise.allSettled([getTodayReview(), getStreak(), getPracticeStats()]);
  if (review.status !== "fulfilled" && streak.status !== "fulfilled" && stats.status !== "fulfilled") return;
  reviewSummary.value = {
    dueCount: review.status === "fulfilled" ? review.value.due_count : 0,
    wrongCount: review.status === "fulfilled" ? review.value.wrong_count : 0,
    streak: streak.status === "fulfilled" ? streak.value.current_streak : 0,
    todayCount: stats.status === "fulfilled" ? stats.value.today_count : 0,
  };
}

onMounted(() => {
  void fetchRecentCourses();
  void fetchReviewSummary();
});
</script>

<template>
  <section class="home-page" data-reference-page="home">
    <div class="home-welcome">
      <div>
        <p>把每一天，变成一点进步</p>
        <h1>今天，继续学习</h1>
      </div>
      <button
        type="button"
        class="home-progress"
        aria-label="查看学习数据"
        @click="goTo({ name: 'study-overview', query: { from: 'home' } })"
      >
        <TrendingUp :size="22" />
      </button>
    </div>
    <header class="home-hero fade-up">
      <button class="home-search-entry" data-home-search type="button" @click="openGlobalSearch">
        <span class="home-search-entry__scan" aria-hidden="true">
          <ScanLine :size="20" :stroke-width="2.2" />
        </span>
        <span>搜索题库、文档、作者</span>
      </button>
    </header>

    <nav class="quick-panel fade-up d1" data-testid="home-shortcuts" aria-label="快捷操作">
      <GlassIcons :items="glassActionItems" @select="onGlassActionSelect" />
    </nav>

    <SpotlightCard
      v-if="reviewSummary"
      class-name="review-hero fade-up d2"
      spotlight-color="rgba(255, 255, 255, 0.28)"
      aria-label="今日复习概览"
    >
      <div class="review-hero__body">
        <p class="review-hero__kicker">今日待复习</p>
        <p v-if="reviewSummary.dueCount > 0" class="review-hero__headline">
          <strong><CountUp :to="reviewSummary.dueCount" :duration="1.2" /></strong>
          <span>道题已到期</span>
        </p>
        <p v-else class="review-hero__headline">
          <strong class="review-hero__clear">全部清空</strong>
        </p>
        <p v-if="reviewSubline" class="review-hero__sub">{{ reviewSubline }}</p>
        <p v-else-if="reviewSummary.dueCount === 0" class="review-hero__sub">保持节奏，明天继续。</p>
      </div>
      <SpecularButton
        v-if="reviewSummary.dueCount > 0"
        class="review-hero__cta"
        size="sm"
        :radius="999"
        tint="#ffffff"
        :tint-opacity="1"
        text-color="#0062cc"
        auto-animate
        @click="goTo({ name: 'practice-due' })"
      >
        开始复习
      </SpecularButton>
    </SpotlightCard>

    <div class="section-head fade-up d3" data-testid="home-recent">
      <h3 class="section-title">最近题库</h3>
      <button class="section-more" type="button" @click="replaceTo('/courses')">查看全部</button>
    </div>

    <div
      v-if="coursesLoading && !coursesLoaded"
      class="course-loading-skeleton"
      aria-busy="true"
      aria-label="正在加载题库"
    >
      <span v-for="index in 2" :key="index" class="course-loading-skeleton__row" />
    </div>
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
          :aria-label="`查看题库：${getCourseDisplayName(course)}`"
          @click="viewRecentCourse(course)"
        >
          <span class="course-icon" data-home-course-icon aria-hidden="true" :style="getCourseIdentity(course).style">
            <component :is="getCourseIdentity(course).icon" :size="20" :stroke-width="2.25" />
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
          class="home-course-share"
          data-testid="home-course-share"
          type="button"
          :aria-label="`\u5206\u4eab${getCourseDisplayName(course)}`"
          @click.stop="copyRecentCourseShareLink(course)"
        >
          <Copy :size="16" :stroke-width="2.5" />
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
  gap: 0;
}
.home-welcome {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 0 22px;
}
.home-welcome p {
  margin: 0 0 6px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
}
.home-welcome h1 {
  margin: 0;
  font-size: clamp(24px, 6vw, 30px);
  letter-spacing: -0.04em;
  font-weight: 700;
}
.home-progress {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  color: var(--primary);
  background: var(--surface);
}
.home-hero {
  display: grid;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.review-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 14px 0 4px;
  padding: 18px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary) 0%, #7c3aed 100%);
  color: #ffffff;
  overflow: hidden;
  border: 0;
}
.review-hero::after {
  content: "";
  position: absolute;
  top: -52px;
  right: -52px;
  width: 156px;
  height: 156px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  pointer-events: none;
}
.review-hero__body {
  position: relative;
  z-index: 1;
  min-width: 0;
}
.review-hero__kicker {
  margin: 0 0 4px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  opacity: 0.85;
}
.review-hero__headline {
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 7px;
}
.review-hero__headline strong {
  font-size: 34px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
}
.review-hero__headline strong.review-hero__clear {
  font-size: 26px;
}
.review-hero__headline span {
  font-size: var(--text-sm);
  font-weight: 600;
  opacity: 0.92;
}
.review-hero__sub {
  margin: 7px 0 0;
  font-size: var(--text-xs);
  line-height: 1.5;
  opacity: 0.88;
}
.review-hero__cta {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}
.home-search-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 16px;
  border: 0;
  border-radius: 16px;
  background: var(--surface);
  color: var(--text-muted);
  font-size: var(--text-md);
  text-align: left;
}
.home-search-entry__scan {
  display: grid;
  place-items: center;
  color: var(--primary);
}
.quick-panel {
  margin: 16px 0 12px;
  padding: 16px 10px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  font-size: 15px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 14px 0 12px;
}
.section-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.025em;
}
.section-more {
  min-height: 44px;
  font-size: var(--text-xs);
  font-weight: 500;
}
.home-course-list {
  display: grid;
  gap: 10px;
  overflow: visible;
}
.course-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}
.course-item:hover {
  transform: none;
  box-shadow: var(--shadow-xs);
}
.course-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  min-height: 84px;
  padding: 14px 12px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
}
.course-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 12px;
  background: var(--primary-soft);
  color: var(--primary);
}
.course-info {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 5px;
}
.course-info strong {
  font-size: var(--text-md);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.course-info span {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
}
.home-course-more,
.home-course-share {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 36px;
  height: 44px;
  border: 0;
  padding: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--text-muted);
}
.home-course-more {
  margin-right: 10px;
}
.home-course-share {
  color: var(--primary);
}
.home-course-more:hover,
.home-course-share:hover {
  background: var(--surface-soft);
}
.home-course-item--menu-open {
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
  border-radius: 18px;
  background: var(--glass-nav);
  backdrop-filter: blur(var(--glass-overlay-blur));
  -webkit-backdrop-filter: blur(var(--glass-overlay-blur));
  box-shadow: var(--shadow-elevated);
}
.home-menu-option {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 12px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-main);
  font-size: var(--text-sm);
  font-weight: 500;
  text-align: left;
}
.home-menu-option:hover:not(:disabled) {
  background: var(--surface-soft);
}
.home-menu-option--danger {
  color: var(--rose);
}
.home-menu-divider {
  height: 1px;
  margin: 3px 8px;
  background: var(--line-soft);
}
.empty-state {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 32px 16px;
  text-align: center;
  color: var(--text-muted);
}
.empty-state strong {
  color: var(--text-main);
}
.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
}
.empty-actions {
  display: flex;
  gap: 8px;
}
.empty-btn {
  min-height: 44px;
  padding: 8px 16px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--surface);
  color: var(--text-main);
}
.empty-btn--primary {
  background: var(--primary);
  color: #fff;
}
.course-loading-skeleton {
  display: grid;
  gap: 10px;
}
.course-loading-skeleton__row {
  min-height: 84px;
  border-radius: var(--radius-md);
  background: var(--surface);
}
</style>
