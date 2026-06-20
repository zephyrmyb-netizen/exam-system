<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useStudyOverview } from "../composables/useStudyOverview";
import { typeLabel } from "../utils/question";
import {
  TrendingUp, Target, Zap, BookMarked, RefreshCw, Clock,
  BookOpen,
} from "@lucide/vue";

const router = useRouter();
const { stats, review, loading, fetchAll } = useStudyOverview();

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "--";
  return `${(rate * 100).toFixed(1)}%`;
});

const accuracyColor = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "";
  if (rate >= 0.8) return "green";
  if (rate >= 0.5) return "amber";
  return "rose";
});

onMounted(() => { if (stats.value.todayCount === null) fetchAll(); });
</script>

<template>
  <section class="overview-page">
    <!-- Learning Stats -->
    <p class="section-label">学习数据</p>
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
        <span class="stat-lbl">近 7 天练习</span>
      </div>
      <div class="stat-card">
        <BookOpen :size="16" :stroke-width="2.5" class="stat-icon blue" />
        <span class="stat-val blue">{{ stats.coursesCount !== null ? stats.coursesCount : "--" }}</span>
        <span class="stat-lbl">我的题库</span>
      </div>
    </div>

    <!-- Review & Weak Types -->
    <p class="section-label">复习建议</p>
    <div class="review-card">
      <div class="review-row">
        <span class="review-lbl">今日待复习</span>
        <span class="review-val">{{ review.dueCount !== null ? review.dueCount : "--" }} 题</span>
      </div>
      <div v-if="review.weakTypes.length > 0" class="review-row">
        <span class="review-lbl">薄弱题型</span>
        <span class="review-tags">
          <span v-for="wt in review.weakTypes" :key="wt.question_type" class="weak-chip">
            {{ typeLabel(wt.question_type) }}
            <span class="weak-rate">{{ (wt.error_rate * 100).toFixed(0) }}%</span>
          </span>
        </span>
      </div>
      <div class="review-actions">
        <button class="primary-button" type="button" @click="router.push('/practice/wrong')">
          <RefreshCw :size="15" :stroke-width="2.5" style="margin-right:4px" />
          错题强化
        </button>
        <button class="ghost-button" type="button" @click="router.push('/practice')">
          开始练习
        </button>
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

/* ── Stat Grid ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.stat-card {
  display: grid;
  gap: 3px;
  padding: var(--space-3) 8px;
  border-radius: var(--radius-lg);
  background: var(--surface);
  border: 1px solid var(--line-soft);
  text-align: center;
}

.stat-icon {
  justify-self: center;
  margin-bottom: 1px;
}
.stat-icon.teal { color: var(--teal); }
.stat-icon.blue { color: var(--primary); }
.stat-icon.rose { color: var(--rose); }
.stat-icon.amber { color: var(--amber); }
.stat-icon.green { color: var(--emerald); }

.stat-val {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.stat-val.blue { color: var(--primary-strong); }
.stat-val.rose { color: var(--rose); }
.stat-val.amber { color: var(--amber); }
.stat-val.green { color: var(--emerald); }

.stat-lbl {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 600;
}

.green .stat-val { color: var(--emerald); }
.amber .stat-val { color: var(--amber); }
.rose .stat-val { color: var(--rose); }

/* ── Review Card ── */
.review-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--amber-soft);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #fffbeb, #fff7ed);
}

.review-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.review-lbl {
  font-size: var(--text-sm);
  font-weight: 600;
  color: #92400e;
}

.review-val {
  font-size: var(--text-sm);
  font-weight: 800;
  color: #92400e;
}

.review-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.weak-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #fef3c7;
  color: #92400e;
  font-size: 10px;
  font-weight: 700;
}

.weak-rate {
  color: #b45309;
  font-weight: 800;
}

.review-actions {
  display: flex;
  gap: var(--space-2);
}

.primary-button, .ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  padding: 8px 14px;
  min-height: 38px;
}

/* ── Responsive ── */
@media (min-width: 640px) {
  .stat-grid {
    grid-template-columns: repeat(3, 1fr);
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
}
</style>
