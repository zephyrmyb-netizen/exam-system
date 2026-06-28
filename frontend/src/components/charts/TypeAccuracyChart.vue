<script setup lang="ts">
import type { TypeDistribution } from "@/types";

defineProps<{
  items: TypeDistribution[];
}>();

const typeLabels: Record<string, string> = {
  single_choice: "单选题",
  multiple_choice: "多选题",
  true_false: "判断题",
  fill_blank: "填空题",
  short_answer: "简答题",
};

function labelOf(type: string): string {
  return typeLabels[type] || type || "未知题型";
}

function percent(rate: number): string {
  return `${Math.round((rate || 0) * 100)}%`;
}
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <span>题型正确率</span>
      <small>按题型拆解</small>
    </div>

    <div v-if="items.length" class="row-list">
      <div v-for="item in items" :key="item.question_type" class="chart-row" data-test="type-row">
        <div class="row-main">
          <strong>{{ labelOf(item.question_type) }}</strong>
          <small>{{ item.total_count }} 题 · 错 {{ item.wrong_count }}</small>
        </div>
        <div class="progress-wrap">
          <span class="progress-bar" :style="{ width: percent(item.accuracy_rate) }"></span>
        </div>
        <b>{{ percent(item.accuracy_rate) }}</b>
      </div>
    </div>

    <p v-else class="chart-empty">暂无题型数据</p>
  </div>
</template>

<style scoped>
.chart-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
}
.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 850;
  color: var(--text-main);
}
.chart-head small,
.chart-empty {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 650;
}
.row-list {
  display: grid;
  gap: var(--space-3);
}
.chart-row {
  display: grid;
  grid-template-columns: minmax(92px, 1fr) minmax(86px, 1.2fr) 42px;
  gap: var(--space-2);
  align-items: center;
}
.row-main {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.row-main strong {
  color: var(--text-main);
  font-size: var(--text-sm);
}
.row-main small {
  color: var(--text-muted);
  font-size: 11px;
}
.progress-wrap {
  height: 9px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  overflow: hidden;
}
.progress-bar {
  display: block;
  height: 100%;
  max-width: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--rose), var(--amber), var(--emerald));
}
.chart-row b {
  justify-self: end;
  color: var(--primary-strong);
  font-size: var(--text-xs);
}
</style>
