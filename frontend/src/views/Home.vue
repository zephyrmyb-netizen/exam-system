<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useStudyOverview } from "../composables/useStudyOverview";
import { getMyCourses } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import {
  BookOpen,
  ChevronRight,
  ClipboardList,
  FileUp,
  History,
  Megaphone,
  Search,
  Sparkles,
  Target,
  TrendingUp,
} from "@lucide/vue";
import { releaseNotes } from "../data/releaseNotes";

const router = useRouter();
const { user } = useAuth();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();
const courses = ref([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const usernameText = computed(() => user.value?.username || user.value?.name || "同学");

const dateText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(new Date()),
);

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "--";
  return `${(rate * 100).toFixed(0)}%`;
});

const statCards = computed(() => [
  { label: "今日已刷", value: stats.value.todayCount, suffix: "题" },
  { label: "总刷题", value: stats.value.totalCount, suffix: "题" },
  { label: "正确率", value: accuracyDisplay.value, suffix: "" },
  { label: "近 7 日", value: stats.value.recentCount7d, suffix: "题" },
]);

const latestNote = computed(() => releaseNotes[0] || null);

const recentCourses = computed(() =>
  [...courses.value]
    .filter(isPracticeReadyCourse)
    .sort((a, b) => {
      const aTime = new Date(a.last_practiced_at || a.created_at || 0).getTime();
      const bTime = new Date(b.last_practiced_at || b.created_at || 0).getTime();
      return bTime - aTime;
    })
    .slice(0, 3),
);

function formatCourseDate(course) {
  const raw = course.last_practiced_at || course.created_at;
  if (!raw) return "暂无记录";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return "暂无记录";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" }).format(date);
}

const heroActions = [
  {
    label: "AI 导入",
    desc: "上传资料生成题库",
    icon: FileUp,
    to: "/import",
    badge: "推荐",
  },
  {
    label: "开始练习",
    desc: "错题、到期、随机练",
    icon: ClipboardList,
    to: "/practice",
  },
  {
    label: "错题本",
    desc: "集中复盘易错题",
    icon: Target,
    to: "/wrongbook",
  },
  {
    label: "学习概览",
    desc: "查看今日进度",
    icon: TrendingUp,
    to: { name: "study-overview", query: { from: "home" } },
  },
];

const studyEntries = [
  {
    label: "学习概览",
    desc: "查看今日数据和薄弱点",
    icon: TrendingUp,
    color: "var(--teal)",
    to: { name: "study-overview", query: { from: "home" } },
  },
  {
    label: "错题本",
    desc: "集中复盘易错题",
    icon: Target,
    color: "var(--rose)",
    to: "/wrongbook",
  },
  {
    label: "练习记录",
    desc: "回看每次作答",
    icon: History,
    color: "var(--amber)",
    to: { name: "practice-history", query: { from: "home" } },
  },
];

function goTo(target) {
  if (typeof target === "string") {
    router.push(target);
    return;
  }
  router.push(target);
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

function startCoursePractice(course) {
  router.push(`/courses/${course.id}/practice`);
}

onMounted(() => {
  fetchAll();
  fetchRecentCourses();
});
</script>

<template>
  <section class="home-page">
    <div class="home-hero">
      <div class="home-hero-top">
        <div>
          <p class="home-kicker">{{ dateText }}</p>
          <h1>{{ usernameText }}，开始复习吧</h1>
        </div>
        <button class="home-mini-button" type="button" @click="router.push('/announcements?from=home')">
          <Megaphone :size="18" :stroke-width="2.4" />
        </button>
      </div>

      <button class="home-search" type="button" @click="router.push('/courses')">
        <Search :size="18" :stroke-width="2.3" />
        <span>搜索题库、科目、题目</span>
      </button>

      <div class="hero-action-grid">
        <button
          v-for="item in heroActions"
          :key="item.label"
          class="hero-action"
          type="button"
          @click="goTo(item.to)"
        >
          <span v-if="item.badge" class="action-badge">{{ item.badge }}</span>
          <span class="hero-action-icon">
            <component :is="item.icon" :size="24" :stroke-width="2.2" />
          </span>
          <span class="hero-action-label">{{ item.label }}</span>
          <span class="hero-action-desc">{{ item.desc }}</span>
        </button>
      </div>
    </div>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <button class="study-card" type="button" @click="goTo({ name: 'study-overview', query: { from: 'home' } })">
      <div class="section-title-row">
        <div>
          <p class="section-kicker">我的学习空间</p>
          <h2>学习概览</h2>
        </div>
        <ChevronRight :size="18" :stroke-width="2.5" />
      </div>

      <div class="home-stats-grid">
        <div v-for="item in statCards" :key="item.label" class="home-stat">
          <strong>
            {{ item.value !== null && item.value !== undefined && item.value !== "" ? item.value : "--" }}
            <small v-if="item.suffix">{{ item.suffix }}</small>
          </strong>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </button>

    <section class="learning-space">
      <div class="section-title-row section-title-row--plain">
        <div>
          <p class="section-kicker">我的学习空间</p>
          <h2>最近题库</h2>
        </div>
        <button class="section-link-button" type="button" @click="goTo('/courses')">
          查看全部
          <ChevronRight :size="15" :stroke-width="2.5" />
        </button>
      </div>

      <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
      <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

      <div v-if="!coursesLoading && !coursesError && recentCourses.length === 0" class="home-empty-panel">
        <BookOpen :size="38" :stroke-width="1.8" />
        <strong>还没有题库</strong>
        <span>导入资料后，首页会显示最近学习的题库。</span>
        <div class="home-empty-actions">
          <button class="empty-primary" type="button" @click="goTo('/import')">去导入</button>
          <button class="empty-secondary" type="button" @click="goTo('/courses')">浏览题库</button>
        </div>
      </div>

      <div v-if="recentCourses.length > 0" class="recent-course-list">
        <article v-for="course in recentCourses" :key="course.id" class="recent-course">
          <button class="recent-course-main" type="button" @click="goTo(`/courses/${course.id}`)">
            <span class="recent-course-icon">
              <BookOpen :size="20" :stroke-width="2.2" />
            </span>
            <span class="recent-course-copy">
              <strong>{{ getCourseDisplayName(course) }}</strong>
              <small>
                {{ course.question_count ?? 0 }} 题
                <span>·</span>
                {{ course.visibility === "public" ? "公开" : "私有" }}
                <span>·</span>
                {{ formatCourseDate(course) }}
              </small>
            </span>
          </button>
          <button class="recent-course-action" type="button" @click="startCoursePractice(course)">
            开始练习
          </button>
        </article>
      </div>
    </section>

    <div class="section-title-row section-title-row--plain">
      <div>
        <p class="section-kicker">继续学习</p>
        <h2>常用入口</h2>
      </div>
    </div>

    <div class="study-entry-list">
      <button
        v-for="item in studyEntries"
        :key="item.label"
        class="study-entry"
        type="button"
        @click="goTo(item.to)"
      >
        <span class="study-entry-icon" :style="{ color: item.color }">
          <component :is="item.icon" :size="22" :stroke-width="2.25" />
        </span>
        <span class="study-entry-copy">
          <strong>{{ item.label }}</strong>
          <small>{{ item.desc }}</small>
        </span>
        <ChevronRight :size="16" :stroke-width="2.5" />
      </button>
    </div>

    <button
      v-if="latestNote"
      class="release-strip"
      type="button"
      @click="goTo({ name: 'announcements', query: { from: 'home' } })"
    >
      <Sparkles :size="16" :stroke-width="2.4" />
      <span>{{ latestNote.version }} {{ latestNote.title }}</span>
      <ChevronRight :size="16" :stroke-width="2.5" />
    </button>
  </section>
</template>

<style scoped>
.home-page {
  display: grid;
  gap: var(--space-4);
}

.home-hero {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  color: #fff;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.26), transparent 28%),
    linear-gradient(160deg, #1d9bf0 0%, #2563eb 58%, #1e40af 100%);
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.25);
  overflow: hidden;
}

.home-hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.home-kicker,
.section-kicker {
  margin: 0;
  font-size: var(--text-xs);
  font-weight: 800;
  color: rgba(255, 255, 255, 0.76);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.home-hero h1 {
  margin: 4px 0 0;
  font-size: clamp(24px, 7vw, 34px);
  line-height: 1.1;
  letter-spacing: 0;
}

.home-mini-button {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(12px);
}

.home-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  min-height: 50px;
  padding: 0 var(--space-4);
  border: none;
  border-radius: var(--radius-full);
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
  text-align: left;
}

.home-search span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.hero-action-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.hero-action {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 5px;
  min-height: 100px;
  padding: var(--space-3) 4px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: var(--radius-lg);
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.hero-action-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.18);
}

.hero-action-label {
  font-size: var(--text-sm);
  font-weight: 800;
  line-height: 1.2;
}

.hero-action-desc {
  max-width: 100%;
  color: rgba(255, 255, 255, 0.74);
  font-size: 10px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
}

.action-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  padding: 2px 5px;
  border-radius: var(--radius-full);
  color: #1d4ed8;
  background: #fef3c7;
  font-size: 9px;
  font-weight: 900;
}

.study-card,
.release-strip,
.study-entry {
  width: 100%;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  font: inherit;
  text-align: left;
}

.study-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-xl);
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.section-title-row h2 {
  margin: 2px 0 0;
  color: var(--text-main);
  font-size: var(--text-xl);
  line-height: 1.15;
}

.section-title-row--plain {
  padding: var(--space-1) 2px 0;
}

.section-title-row--plain .section-kicker,
.study-card .section-kicker {
  color: var(--text-placeholder);
}

.home-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.home-stat {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding: var(--space-3) 4px;
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  text-align: center;
}

.home-stat strong {
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-size: var(--text-lg);
  line-height: 1;
}

.home-stat small {
  margin-left: 1px;
  color: var(--text-muted);
  font-size: 10px;
}

.home-stat span {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.learning-space {
  display: grid;
  gap: var(--space-3);
}

.section-link-button {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  border: none;
  color: var(--primary-strong);
  background: transparent;
  font-size: var(--text-sm);
  font-weight: 800;
}

.home-empty-panel {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  padding: var(--space-6) var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  color: var(--text-muted);
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: var(--shadow-sm);
  text-align: center;
}

.home-empty-panel strong {
  color: var(--text-main);
  font-size: var(--text-lg);
}

.home-empty-panel span {
  max-width: 260px;
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1.5;
}

.home-empty-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.empty-primary,
.empty-secondary {
  min-height: 40px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 800;
}

.empty-primary {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
}

.empty-secondary {
  border: 1px solid var(--line-strong);
  color: var(--primary-strong);
  background: var(--surface);
}

.recent-course-list {
  display: grid;
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.recent-course {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-bottom: 1px solid var(--line-soft);
}

.recent-course:last-child {
  border-bottom: none;
}

.recent-course-main {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  border: none;
  background: transparent;
  text-align: left;
}

.recent-course-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  color: var(--primary-strong);
  background: var(--primary-soft);
}

.recent-course-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.recent-course-copy strong {
  overflow: hidden;
  color: var(--text-main);
  font-size: var(--text-base);
  font-weight: 850;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-course-copy small {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-course-action {
  min-height: 36px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-full);
  color: #fff;
  background: var(--primary);
  font-size: var(--text-xs);
  font-weight: 900;
  white-space: nowrap;
}

.study-entry-list {
  display: grid;
  gap: var(--space-2);
}

.study-entry {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  min-height: 72px;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
}

.study-entry-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  background: var(--surface-soft);
}

.study-entry-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.study-entry-copy strong {
  color: var(--text-main);
  font-size: var(--text-base);
}

.study-entry-copy small {
  overflow: hidden;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.release-strip {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 48px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-lg);
  color: var(--primary-strong);
  background: var(--primary-soft);
}

.release-strip span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: 800;
}

@media (max-width: 420px) {
  .home-hero {
    padding: var(--space-4);
  }

  .hero-action-grid {
    gap: 6px;
  }

  .hero-action {
    min-height: 90px;
    padding: var(--space-3) 2px;
  }

  .hero-action-desc {
    display: none;
  }

  .home-stats-grid {
    gap: 6px;
  }

  .home-stat strong {
    font-size: var(--text-base);
  }

  .recent-course {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .recent-course-action {
    width: 100%;
  }
}
</style>
