<script setup lang="ts">
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
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";

const router = useRouter();

const stats = ref({ todayCount: null as number | null, totalCount: null as number | null, wrongCount: null as number | null });
const review = ref({ dueCount: null as number | null, wrongCount: null as number | null, weakTypes: [] as any[] });
const reviewError = ref("");
const statsLoading = ref(false);

const recentCourses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const wrongCount = computed(() => review.value.wrongCount ?? stats.value.wrongCount ?? 0);
const hasWrongQuestions = computed(() => wrongCount.value > 0);
const hasDueQuestions = computed(() => (review.value.dueCount ?? 0) > 0);
const hasRecentCourses = computed(() => recentCourses.value.length > 0);
const primaryCourse = computed(() => recentCourses.value[0] || null);

const heroTitle = computed(() => (primaryCourse.value ? "继续上次练习" : "先选择题库"));
const heroDesc = computed(() => {
  if (!primaryCourse.value) {
    return "练习前先选择一门题库，避免进入空练习。";
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
    description: "按课程进入练习设置",
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

function goToMode(card: { disabled: boolean; to: string }) {
  if (!card.disabled) router.push(card.to);
}

async function fetchStatsReview() {
  reviewError.value = "";
  statsLoading.value = true;
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
      reviewError.value = getErrorMessage((rejected as PromiseRejectedResult).reason, "学习数据暂时不可用");
    }
  } catch (error) {
    reviewError.value = getErrorMessage(error, "学习数据暂时不可用");
  } finally {
    statsLoading.value = false;
  }
}

async function fetchRecentCourses() {
  coursesLoading.value = true;
  coursesError.value = "";
  try {
    const { data } = await request.get<Course[] | { items: Course[] }>("/courses/mine");
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
      :loading="statsLoading"
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
.hub { display: grid; gap: var(--space-3); }
.hub-warning { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); padding: var(--space-2) var(--space-3); border: 1px solid var(--amber-border); border-radius: var(--radius-sm); background: var(--amber-soft); color: var(--amber); font-size: var(--text-xs); font-weight: 700; }
.hub-warning button { border: none; background: transparent; color: inherit; font-weight: 800; cursor: pointer; }
.modes { display: grid; gap: var(--space-2); }
.hub-section { display: grid; gap: var(--space-2); }
.hub-section-head { display: flex; align-items: center; justify-content: space-between; }
.hub-section-label { color: var(--text-main); font-size: var(--text-sm); font-weight: 800; }
.hub-section-link { border: none; background: transparent; color: var(--primary-strong); font-size: var(--text-xs); font-weight: 800; cursor: pointer; }
.recent-list { display: grid; gap: var(--space-2); }
.recent-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid var(--line-soft); border-radius: var(--radius-md); background: var(--surface); }
.recent-body { display: flex; align-items: center; gap: var(--space-2); min-width: 0; cursor: pointer; }
.recent-icon { display: grid; place-items: center; width: 34px; height: 34px; border-radius: var(--radius-sm); flex-shrink: 0; }
.icon-private { background: var(--primary-soft); color: var(--primary); }
.icon-public { background: var(--emerald-soft); color: var(--emerald); }
.recent-info { display: grid; gap: 1px; min-width: 0; }
.recent-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--text-sm); color: var(--text-main); font-weight: 750; }
.recent-meta { display: inline-flex; align-items: center; gap: 3px; color: var(--text-muted); font-size: 11px; font-weight: 600; }
.recent-button { display: inline-flex; align-items: center; justify-content: center; gap: 4px; min-height: 32px; padding: 0 10px; border: none; border-radius: var(--radius-sm); background: var(--primary); color: #fff; font-size: 11px; font-weight: 800; cursor: pointer; }
.hub-guidance { display: grid; place-items: center; gap: var(--space-2); padding: var(--space-6) var(--space-4); border: 1px dashed var(--line-strong); border-radius: var(--radius-md); background: var(--surface); text-align: center; }
.hub-guidance-title { margin: 0; color: var(--text-main); font-size: var(--text-md); font-weight: 850; }
.hub-guidance-hint { margin: 0; color: var(--text-muted); font-size: var(--text-xs); font-weight: 600; }
.hub-guidance-actions, .hub-guidance-alts { display: flex; flex-wrap: wrap; gap: var(--space-2); justify-content: center; }
.primary-button, .ghost-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 38px; padding: 0 13px; border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 800; cursor: pointer; }
.primary-button { border: none; background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color: #fff; box-shadow: var(--shadow-primary); }
.ghost-button { border: 1px solid var(--line-strong); background: var(--surface); color: var(--text-main); }
</style>
