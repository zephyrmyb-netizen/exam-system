<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  BookMarked,
  BookOpen,
  GraduationCap,
  Layers,
  Library,
  ListChecks,
  Play,
  RefreshCw,
  Upload,
} from "@lucide/vue";

import request, { getErrorMessage } from "../api/request";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import PracticeModeCard from "../components/practice/PracticeModeCard.vue";
import PracticeOverviewCard from "../components/practice/PracticeOverviewCard.vue";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";

const router = useRouter();

const stats = ref({ todayCount: null, totalCount: null, wrongCount: null });
const review = ref({ dueCount: null, wrongCount: null, weakTypes: [] });
const reviewError = ref("");

const recentCourses = ref([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const wrongCount = computed(() => review.value.wrongCount ?? stats.value.wrongCount ?? 0);
const hasWrongQuestions = computed(() => wrongCount.value > 0);
const hasDueQuestions = computed(() => (review.value.dueCount ?? 0) > 0);
const hasRecentCourses = computed(() => recentCourses.value.length > 0);
const primaryCourse = computed(() => recentCourses.value[0] || null);

const heroTitle = computed(() => (primaryCourse.value ? "继续上次练习" : "开始一次练习"));
const heroDesc = computed(() => {
  if (!primaryCourse.value) {
    return "先选择题库，或导入资料生成题库。";
  }

  const count = primaryCourse.value.question_count ?? 0;
  return `${getCourseDisplayName(primaryCourse.value)} · ${count} 题`;
});

const modeCards = computed(() => [
  {
    key: "course",
    icon: Library,
    iconColor: "var(--primary)",
    title: "选择题库练习",
    description: "按题库进入练习设置",
    cta: true,
    showArrow: true,
    disabled: false,
    to: "/courses",
  },
  {
    key: "wrong",
    icon: RefreshCw,
    iconColor: "var(--rose)",
    title: "错题强化",
    description: hasWrongQuestions.value ? `${wrongCount.value} 道待复习` : "暂无错题",
    disabled: !hasWrongQuestions.value,
    to: "/practice/wrong",
  },
  {
    key: "due",
    icon: BookMarked,
    iconColor: "var(--teal)",
    title: "到期复习",
    description: hasDueQuestions.value ? `${review.value.dueCount} 道今日到期` : "暂无到期题目",
    disabled: !hasDueQuestions.value,
    to: "/practice/due",
  },
  {
    key: "history",
    icon: ListChecks,
    iconColor: "var(--amber)",
    title: "练习记录",
    description: "查看答题历史",
    disabled: false,
    to: "/practice/history",
  },
]);

function openPrimaryPractice() {
  if (primaryCourse.value) {
    router.push(`/courses/${primaryCourse.value.id}/practice`);
    return;
  }

  router.push("/courses");
}

function goToMode(card) {
  if (!card.disabled) {
    router.push(card.to);
  }
}

async function fetchStatsReview() {
  reviewError.value = "";
  try {
    const [statsResult, reviewResult, weakResult] = await Promise.allSettled([
      getPracticeStats(),
      getTodayReview(),
      getWeakTypes(),
    ]);

    if (statsResult.status === "fulfilled") {
      const data = statsResult.value;
      stats.value.todayCount = data.today_count ?? null;
      stats.value.totalCount = data.total_count ?? null;
      stats.value.wrongCount = data.wrong_count ?? null;
    }

    if (reviewResult.status === "fulfilled") {
      const data = reviewResult.value;
      review.value.dueCount = data.due_count ?? null;
      review.value.wrongCount = data.wrong_count ?? null;
    }

    if (weakResult.status === "fulfilled" && Array.isArray(weakResult.value)) {
      review.value.weakTypes = weakResult.value.slice(0, 3);
    }

    const rejected = [statsResult, reviewResult, weakResult].find((item) => item.status === "rejected");
    if (rejected) {
      reviewError.value = getErrorMessage(rejected.reason, "学习数据暂时不可用");
    }
  } catch (error) {
    reviewError.value = getErrorMessage(error, "学习数据暂时不可用");
  }
}

async function fetchRecentCourses() {
  coursesLoading.value = true;
  coursesError.value = "";
  try {
    const { data } = await request.get("/courses/mine");
    const items = Array.isArray(data) ? data : data.items || [];
    recentCourses.value = items.filter(isPracticeReadyCourse).slice(0, 3);
  } catch (error) {
    recentCourses.value = [];
    coursesError.value = getErrorMessage(error, "题库列表暂时不可用");
  } finally {
    coursesLoading.value = false;
  }
}

function retryFailedRequest() {
  if (reviewError.value) {
    fetchStatsReview();
    return;
  }

  fetchRecentCourses();
}

onMounted(() => {
  fetchStatsReview();
  fetchRecentCourses();
});
</script>

<template>
  <section class="hub">
    <PracticeOverviewCard
      :title="heroTitle"
      :description="heroDesc"
      :has-primary-course="Boolean(primaryCourse)"
      :today-count="stats.todayCount"
      :total-count="stats.totalCount"
      :wrong-count="wrongCount"
      :due-count="review.dueCount"
      :weak-types="review.weakTypes"
      @primary="openPrimaryPractice"
    />

    <div v-if="reviewError || coursesError" class="hub-warning">
      <span>{{ reviewError || coursesError }}</span>
      <button type="button" @click="retryFailedRequest">重试</button>
    </div>

    <div class="modes" aria-label="练习入口">
      <PracticeModeCard
        v-for="card in modeCards"
        :key="card.key"
        :icon="card.icon"
        :icon-color="card.iconColor"
        :title="card.title"
        :description="card.description"
        :cta="card.cta"
        :disabled="card.disabled"
        :show-arrow="card.showArrow"
        @select="goToMode(card)"
      />
    </div>

    <div v-if="hasRecentCourses" class="hub-section">
      <div class="hub-section-head">
        <span class="hub-section-label">最近可练习</span>
        <button class="hub-section-link" type="button" @click="router.push('/courses')">查看全部</button>
      </div>

      <div class="recent-list">
        <div v-for="course in recentCourses" :key="course.id" class="recent-row">
          <div class="recent-body" @click="router.push(`/courses/${course.id}`)">
            <div class="recent-icon" :class="course.visibility === 'public' ? 'icon-public' : 'icon-private'">
              <BookOpen :size="16" :stroke-width="2" />
            </div>
            <div class="recent-info">
              <span class="recent-name">{{ getCourseDisplayName(course) }}</span>
              <span class="recent-meta">
                <Layers :size="10" :stroke-width="2" />
                {{ course.question_count ?? 0 }} 题
              </span>
            </div>
          </div>
          <button class="recent-button" type="button" @click="router.push(`/courses/${course.id}/practice`)">
            <Play :size="12" :stroke-width="2.5" />
            练习
          </button>
        </div>
      </div>
    </div>

    <div v-if="!coursesLoading && !hasRecentCourses" class="hub-guidance">
      <GraduationCap :size="44" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p class="hub-guidance-title">选择一个题库开始练习</p>
      <p class="hub-guidance-hint">还没有题库？先去导入题目创建一个题库。</p>
      <div class="hub-guidance-actions">
        <button class="primary-button" type="button" @click="router.push('/courses')">
          <Library :size="16" :stroke-width="2.5" />
          去题库选择
        </button>
        <button class="ghost-button" type="button" @click="router.push('/import')">
          <Upload :size="16" :stroke-width="2.5" />
          导入题目
        </button>
      </div>
      <div v-if="hasWrongQuestions || stats.totalCount" class="hub-guidance-alts">
        <button v-if="hasWrongQuestions" class="ghost-button" type="button" @click="router.push('/practice/wrong')">
          错题强化
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hub {
  display: grid;
  gap: var(--space-3);
}

.hub-warning {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 8px 10px;
  border: 1px solid var(--amber-border);
  border-radius: var(--radius-md);
  background: var(--amber-soft);
  color: #92400e;
  font-size: var(--text-xs);
  font-weight: 700;
}

.hub-warning button {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: #92400e;
  font: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.modes {
  display: grid;
  gap: 6px;
}

.hub-section {
  display: grid;
  gap: var(--space-2);
}

.hub-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hub-section-label {
  font-size: var(--text-xs);
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hub-section-link {
  padding: 0;
  border: none;
  background: none;
  color: var(--primary);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.hub-section-link:hover {
  color: var(--primary-strong);
}

.recent-list {
  display: grid;
  gap: 6px;
}

.recent-row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.recent-body {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  cursor: pointer;
}

.recent-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.icon-private {
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.icon-public {
  background: var(--emerald-soft);
  color: var(--emerald);
}

.recent-info {
  display: grid;
  gap: 1px;
  min-width: 0;
}

.recent-name {
  overflow: hidden;
  color: var(--text-main);
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-meta {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 600;
}

.recent-button {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-full);
  background: var(--primary-soft);
  color: var(--primary-strong);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
}

.hub-guidance {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-4);
  color: var(--text-muted);
  text-align: center;
}

.hub-guidance p {
  margin: 0;
}

.hub-guidance-title {
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-weight: 700;
}

.hub-guidance-hint {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.hub-guidance-actions,
.hub-guidance-alts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.hub-guidance-alts {
  margin-top: var(--space-1);
}

.hub-guidance-alts button {
  min-height: 32px;
  padding: 6px 12px;
  font-size: var(--text-xs);
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
</style>
