<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { BookMarked, BookOpen, Clock, RefreshCw, Target, TrendingUp, Zap } from "@lucide/vue";
import ActivityTrendChart from "../components/charts/ActivityTrendChart.vue";
import CourseAnalyticsChart from "../components/charts/CourseAnalyticsChart.vue";
import HeatmapChart from "../components/charts/HeatmapChart.vue";
import TagMasteryChart from "../components/charts/TagMasteryChart.vue";
import TypeAccuracyChart from "../components/charts/TypeAccuracyChart.vue";
import { useStudyOverview } from "../composables/useStudyOverview";
import { useAppNavigation } from "../composables/useAppNavigation";
import { typeLabel } from "../utils/question";
import request, { getErrorMessage } from "../api/request";

const { replaceTo } = useAppNavigation();
const {
  stats,
  review,
  activity,
  typeDistribution,
  tagAccuracy,
  courseAnalytics,
  streak,
  recommendation,
  errorMessage,
  fetchAll,
} = useStudyOverview();

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  return rate === null ? "--" : `${(rate * 100).toFixed(1)}%`;
});

const accuracyColor = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "";
  if (rate >= 0.8) return "green";
  if (rate >= 0.5) return "amber";
  return "rose";
});

const recommendedText = computed(() => {
  const modes = recommendation.value?.recommended_modes || review.value.recommendedModes || [];
  if (!modes.length) return "按题库继续练习";
  return modes.slice(0, 2).join(" / ");
});

interface StudyPlan {
  daily_target: number;
  deadline: string | null;
  today_completed: number;
  today_remaining: number;
  current_streak: number;
}
const plan = ref<StudyPlan | null>(null);
const planSaving = ref(false);
const planLoading = ref(false);
const planMessage = ref("");
const planTarget = ref(10);
const planDeadline = ref("");
const planError = ref("");
async function loadPlan() {
  planLoading.value = true;
  try {
    const { data } = await request.get<StudyPlan | null>("/study-plans/current");
    plan.value = data;
    if (data) {
      planTarget.value = data.daily_target;
      planDeadline.value = data.deadline ? data.deadline.slice(0, 10) : "";
    }
  } catch (error) {
    planError.value = getErrorMessage(error, "加载学习计划失败");
  } finally {
    planLoading.value = false;
  }
}
async function savePlan() {
  if (planSaving.value) return;
  planError.value = "";
  planMessage.value = "";
  if (!Number.isInteger(planTarget.value) || planTarget.value < 1 || planTarget.value > 500) {
    planError.value = "每日题量请输入 1–500 的整数。";
    return;
  }
  planSaving.value = true;
  try {
    const { data } = await request.put<StudyPlan>("/study-plans/current", {
      title: "每日学习计划",
      daily_target: planTarget.value,
      deadline: planDeadline.value ? new Date(`${planDeadline.value}T23:59:59`).toISOString() : null,
    });
    plan.value = data;
    planMessage.value = "学习计划已保存。";
  } catch (error) {
    planError.value = getErrorMessage(error, "保存学习计划失败");
  } finally {
    planSaving.value = false;
  }
}
onMounted(() => {
  void fetchAll();
  void loadPlan();
});
</script>

<template>
  <section class="overview-page">
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <p class="section-label">学习数据</p>
    <form class="plan-card" data-testid="study-plan" @submit.prevent="savePlan">
      <div>
        <strong>学习计划</strong>
        <p v-if="plan">
          今日 {{ plan.today_completed }} / {{ plan.daily_target }} 题，待练 {{ plan.today_remaining }} 题 · 连续
          {{ plan.current_streak }} 天
        </p>
        <p v-else>设置每日目标或考试截止日期。</p>
      </div>
      <label>每日题量<input v-model.number="planTarget" type="number" min="1" max="500" /></label
      ><label>截止日<input v-model="planDeadline" type="date" /></label
      ><button type="submit" :disabled="planSaving || planLoading">{{ planSaving ? "保存中…" : "保存计划" }}</button>
      <p v-if="planError" class="error-message" role="alert">{{ planError }}</p>
      <p v-if="planMessage" role="status">{{ planMessage }}</p>
    </form>
    <div class="stat-grid">
      <div class="stat-card">
        <Zap :size="16" :stroke-width="2.5" class="stat-icon teal" />
        <span class="stat-val">{{ stats.todayCount !== null ? stats.todayCount : "--" }}</span>
        <span class="stat-lbl">今日练习</span>
      </div>
      <div class="stat-card">
        <TrendingUp :size="16" :stroke-width="2.5" class="stat-icon blue" />
        <span class="stat-val">{{ stats.totalCount !== null ? stats.totalCount : "--" }}</span>
        <span class="stat-lbl">累计练习</span>
      </div>
      <div class="stat-card" :class="accuracyColor">
        <Target :size="16" :stroke-width="2.5" class="stat-icon" :class="accuracyColor" />
        <span class="stat-val" :class="accuracyColor">{{ accuracyDisplay }}</span>
        <span class="stat-lbl">正确率</span>
      </div>
      <div class="stat-card">
        <BookMarked :size="16" :stroke-width="2.5" class="stat-icon rose" />
        <span class="stat-val rose">{{ stats.wrongCount !== null ? stats.wrongCount : "--" }}</span>
        <span class="stat-lbl">错题数</span>
      </div>
      <div class="stat-card">
        <Clock :size="16" :stroke-width="2.5" class="stat-icon amber" />
        <span class="stat-val amber">{{ stats.recentCount7d !== null ? stats.recentCount7d : "--" }}</span>
        <span class="stat-lbl">近 7 天</span>
      </div>
      <div class="stat-card">
        <BookOpen :size="16" :stroke-width="2.5" class="stat-icon blue" />
        <span class="stat-val blue">{{ stats.coursesCount !== null ? stats.coursesCount : "--" }}</span>
        <span class="stat-lbl">我的题库</span>
      </div>
    </div>

    <div class="insight-strip">
      <div class="insight-card">
        <span class="insight-label">连续学习</span>
        <strong>{{ streak.current_streak }} 天</strong>
        <small>最长 {{ streak.longest_streak }} 天</small>
      </div>
      <div class="insight-card">
        <span class="insight-label">今日建议</span>
        <strong>{{ recommendedText }}</strong>
        <small>{{ recommendation?.due_count ?? review.dueCount ?? 0 }} 题待复习</small>
      </div>
    </div>

    <p class="section-label">学习趋势</p>
    <ActivityTrendChart :items="activity" />
    <HeatmapChart :items="activity" />

    <div class="chart-grid">
      <TypeAccuracyChart :items="typeDistribution" />
      <TagMasteryChart :items="tagAccuracy" />
    </div>

    <CourseAnalyticsChart v-if="courseAnalytics.length" :items="courseAnalytics" />

    <p class="section-label">复习建议</p>
    <div class="review-card">
      <div class="review-row">
        <span class="review-lbl">今日待复习</span>
        <span class="review-val">{{ review.dueCount !== null ? review.dueCount : "--" }} 题</span>
      </div>
      <div v-if="review.wrongCount !== null" class="review-row">
        <span class="review-lbl">错题数</span>
        <span class="review-val">{{ review.wrongCount }} 题</span>
      </div>
      <div v-if="review.weakTypes.length > 0" class="review-row review-row--stack">
        <span class="review-lbl">薄弱题型</span>
        <span class="review-tags">
          <span v-for="weakType in review.weakTypes" :key="weakType.question_type" class="weak-chip">
            {{ typeLabel(weakType.question_type) }}
            <span class="weak-rate">{{ (weakType.error_rate * 100).toFixed(0) }}%</span>
          </span>
        </span>
      </div>
      <div class="review-actions">
        <button
          v-if="review.dueCount !== null && review.dueCount > 0"
          class="primary-button"
          type="button"
          @click="replaceTo('/practice/due')"
        >
          <RefreshCw :size="15" :stroke-width="2.5" />
          到期复习
        </button>
        <button class="ghost-button" type="button" @click="replaceTo('/practice/wrong')">
          <RefreshCw :size="15" :stroke-width="2.5" />
          错题强化
        </button>
        <button class="ghost-button" type="button" @click="replaceTo('/practice')">开始练习</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.overview-page {
  display: grid;
  gap: var(--space-4);
}

.section-label {
  margin: 0 0 2px 4px;
  font-size: var(--text-xs);
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.plan-card {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  align-items: end;
  gap: 10px;
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
}
.plan-card strong {
  color: var(--text-main);
}
.plan-card p {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
}
.plan-card label {
  display: grid;
  gap: 4px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 800;
}
.plan-card input {
  min-height: 44px;
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 0 8px;
  background: var(--surface-soft);
  font: inherit;
}
.plan-card button {
  min-height: 44px;
  border: 0;
  border-radius: 10px;
  padding: 0 12px;
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 800;
}
@media (max-width: 620px) {
  .plan-card {
    grid-template-columns: 1fr 1fr;
  }
  .plan-card > div,
  .plan-card p {
    grid-column: 1/-1;
  }
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.stat-card {
  display: grid;
  gap: 3px;
  padding: var(--space-3) 8px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  text-align: center;
}

.stat-icon {
  justify-self: center;
  margin-bottom: 1px;
}
.stat-icon.teal {
  color: var(--teal);
}
.stat-icon.blue {
  color: var(--primary);
}
.stat-icon.rose {
  color: var(--rose);
}
.stat-icon.amber {
  color: var(--amber);
}
.stat-icon.green {
  color: var(--emerald);
}

.stat-val {
  color: var(--text-main);
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.stat-val.blue {
  color: var(--primary-strong);
}
.stat-val.rose {
  color: var(--rose);
}
.stat-val.amber {
  color: var(--amber);
}
.stat-val.green {
  color: var(--emerald);
}

.stat-lbl {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.green .stat-val {
  color: var(--emerald);
}
.amber .stat-val {
  color: var(--amber);
}
.rose .stat-val {
  color: var(--rose);
}

.insight-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

.insight-card {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--surface), var(--primary-soft));
}

.insight-label,
.insight-card small {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.insight-card strong {
  overflow: hidden;
  color: var(--text-main);
  font-size: var(--text-md);
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-grid {
  display: grid;
  gap: var(--space-3);
}

.review-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--amber-border);
  border-radius: var(--radius-lg);
  background: var(--amber-soft);
}

.review-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.review-row--stack {
  align-items: flex-start;
}

.review-lbl,
.review-val {
  color: var(--amber-strong);
  font-size: var(--text-sm);
  font-weight: 800;
}

.review-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px;
}

.weak-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--amber-soft);
  color: var(--amber-strong);
  font-size: 11px;
  font-weight: 700;
}

.weak-rate {
  color: #b45309;
  font-weight: 800;
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 38px;
  padding: 8px 14px;
  font-size: var(--text-sm);
}

@media (min-width: 640px) {
  .chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .stat-val {
    font-size: 1.375rem;
  }
}

@media (max-width: 420px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }
  .stat-card {
    padding: var(--space-2) 4px;
  }
  .stat-val {
    font-size: 1rem;
  }
  .insight-strip {
    grid-template-columns: 1fr;
  }
}
</style>
