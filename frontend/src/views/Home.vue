<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";
import { ArrowRight, BookOpen, ClipboardList, FileText, FileUp, MoreHorizontal, ScanLine, Target, TrendingUp } from "@lucide/vue";

import { getMyCourses } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { useStudyOverview } from "../composables/useStudyOverview";
import { useAppNavigation } from "../composables/useAppNavigation";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { typeLabel } from "../utils/question";
import { openGlobalSearch } from "../utils/globalSearch";

const { replaceTo } = useAppNavigation();
const { recommendation, recommendationAvailable, fetchAll } = useStudyOverview();

const courses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const recommendationMode = computed(() =>
  recommendationAvailable.value === true ? recommendation.value?.recommended_modes?.[0] || "" : "",
);

const recommendationNeedsCourseSelection = computed(() =>
  ["weak_tag_practice", "weak_type_practice", "type_practice"].includes(recommendationMode.value),
);

const recommendationModeLabel = computed(
  () =>
    ({
      spaced_repeat: "到期复习",
      wrong_review: "错题强化",
      weak_tag_practice: "薄弱标签练习",
      weak_type_practice: "薄弱题型练习",
      type_practice: "题型专项",
      random_practice: "随机练习",
    })[recommendationMode.value] || "继续练习",
);

const recommendationTitle = computed(() => {
  if (recommendationAvailable.value !== true) return "推荐暂不可用";
  const item = recommendation.value;
  if (!item) return "暂无个性化推荐";
  const tagName = item.weak_tags?.[0]?.tag_name?.trim();
  if (tagName) return `重点巩固：${tagName}`;
  const questionType = item.weak_types?.[0]?.question_type;
  if (questionType) return `重点巩固：${typeLabel(questionType)}`;
  if (item.due_count > 0) return "今日到期复习";
  return recommendationModeLabel.value;
});

const recommendationDescription = computed(() => {
  if (recommendationAvailable.value !== true) return "学习建议加载失败或尚未完成";
  const item = recommendation.value;
  if (!item) return "完成一些练习后，这里会根据真实学习数据生成建议";
  const details: string[] = [];
  if (item.due_count > 0) details.push(`${item.due_count} 题待复习`);
  if (item.weak_types?.[0]?.question_type) details.push(typeLabel(item.weak_types[0].question_type));
  if (recommendationNeedsCourseSelection.value) {
    details.push(`${recommendationModeLabel.value} · 去题库选择相关内容`);
  } else {
    details.push(recommendationModeLabel.value);
  }
  return details.join(" · ");
});

const recommendationTarget = computed<RouteLocationRaw>(() => {
  if (recommendationAvailable.value !== true) return "/courses";
  if (recommendationMode.value === "spaced_repeat") return { name: "practice-due" };
  if (recommendationMode.value === "wrong_review") return { name: "practice-wrong" };
  if (recommendationMode.value === "random_practice") return { name: "practice" };
  return "/courses";
});

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
    <div v-if="recentCourses.length > 0" class="course-list home-course-list fade-up d3">
      <div v-for="course in recentCourses" :key="course.id" class="course-item">
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
            <span class="course-progress" aria-label="练习覆盖进度">
              <i :style="{ width: `${courseProgress(course)}%` }"></i>
            </span>
          </div>
        </button>
        <button
          class="home-course-more"
          data-home-course-more
          type="button"
          :aria-label="`管理题库：${getCourseDisplayName(course)}`"
          @click.stop="replaceTo('/courses')"
        >
          <MoreHorizontal :size="18" :stroke-width="2.5" />
        </button>
      </div>
    </div>

    <button
      class="home-recommendation fade-up d4"
      data-home-recommendation
      type="button"
      @click="goTo(recommendationTarget)"
    >
      <span class="home-recommendation__spark">✦</span>
      <span class="home-recommendation__copy">
        <small class="home-recommendation__tag">每日一练</small>
        <strong>{{ recommendationTitle }}</strong>
        <small>{{ recommendationDescription }}</small>
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

.course-progress {
  display: block;
  height: 5px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-soft);
}
.course-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
}

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
.home-recommendation__spark {
  color: var(--primary);
  font-size: 24px;
}
.home-recommendation__copy {
  min-width: 0;
}
.home-recommendation strong,
.home-recommendation small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.home-recommendation strong {
  font-size: 14px;
}
.home-recommendation small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
}
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
.home-recommendation :deep(svg) {
  color: var(--primary-strong);
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
.home-page .course-progress {
  height: 4px;
  margin-top: 5px;
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
