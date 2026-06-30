<script setup>
import { Library, Play } from "@lucide/vue";
import { typeLabel } from "../../utils/question";

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  hasPrimaryCourse: { type: Boolean, default: false },
  todayCount: { type: Number, default: null },
  totalCount: { type: Number, default: null },
  wrongCount: { type: Number, default: null },
  dueCount: { type: Number, default: null },
  weakTypes: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

defineEmits(["primary"]);

function displayNumber(value, emptyValue = "--") {
  return value !== null && value !== undefined ? value : emptyValue;
}
</script>

<template>
  <div class="overview-card">
    <div class="overview-hero">
      <div class="overview-copy">
        <span class="overview-kicker">练习中心</span>
        <h2>{{ title }}</h2>
        <p>{{ description }}</p>
      </div>
      <button class="overview-button" type="button" @click="$emit('primary')">
        <Play v-if="hasPrimaryCourse" :size="15" :stroke-width="2.8" />
        <Library v-else :size="15" :stroke-width="2.8" />
        {{ hasPrimaryCourse ? "继续练习" : "选择题库" }}
      </button>
    </div>

    <div class="overview-stats">
      <div class="overview-stat">
        <span class="overview-stat-value">{{ loading ? "..." : displayNumber(todayCount) }}</span>
        <span class="overview-stat-label">今日练习</span>
      </div>
      <div class="overview-stat">
        <span class="overview-stat-value">{{ loading ? "..." : displayNumber(totalCount) }}</span>
        <span class="overview-stat-label">累计</span>
      </div>
      <div class="overview-stat">
        <span class="overview-stat-value">{{ loading ? "..." : displayNumber(wrongCount, 0) }}</span>
        <span class="overview-stat-label">错题</span>
      </div>
      <div class="overview-stat">
        <span class="overview-stat-value" :class="{ 'stat-accent': dueCount > 0 }">
          {{ loading ? "..." : displayNumber(dueCount) }}
        </span>
        <span class="overview-stat-label">到期</span>
      </div>
    </div>

    <div v-if="weakTypes.length > 0" class="overview-weak">
      <span class="overview-weak-label">薄弱题型</span>
      <span v-for="item in weakTypes" :key="item.question_type" class="overview-weak-chip">
        {{ typeLabel(item.question_type) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.overview-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-md);
  background:
    radial-gradient(circle at 100% 0%, rgba(59, 130, 246, 0.16), transparent 34%),
    linear-gradient(135deg, #ffffff, #f3f7ff);
}

.overview-hero {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: var(--space-3);
}

.overview-copy { min-width: 0; }
.overview-kicker { display: inline-flex; margin-bottom: 3px; color: var(--primary-strong); font-size: 11px; font-weight: 800; }
.overview-hero h2 { margin: 0; color: var(--text-main); font-size: clamp(22px, 5.6vw, 30px); line-height: 1.1; font-weight: 900; }
.overview-hero p { margin: 6px 0 0; color: var(--text-muted); font-size: var(--text-xs); font-weight: 650; line-height: 1.45; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.overview-button { display: inline-flex; align-items: center; justify-content: center; gap: 4px; min-width: 92px; min-height: 40px; border: none; border-radius: var(--radius-full); background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color: #fff; font-size: var(--text-xs); font-weight: 850; cursor: pointer; box-shadow: var(--shadow-primary); }
.overview-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-2); padding-top: var(--space-2); }
.overview-stat { display: grid; gap: 1px; }
.overview-stat-value { font-size: 18px; font-weight: 800; color: var(--text-main); }
.overview-stat-label { font-size: 11px; font-weight: 600; color: var(--text-muted); }
.stat-accent { color: var(--teal); }
.overview-weak { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.overview-weak-label { font-size: 11px; font-weight: 700; color: var(--text-muted); }
.overview-weak-chip { padding: 2px 7px; border-radius: 999px; background: var(--rose-soft); color: var(--rose); font-size: 11px; font-weight: 700; }

@media (max-width: 420px) {
  .overview-card { padding: var(--space-3); }
  .overview-hero { grid-template-columns: 1fr; }
  .overview-button { width: 100%; }
  .overview-stats { gap: 6px; }
  .overview-stat-value { font-size: 16px; }
}
</style>
