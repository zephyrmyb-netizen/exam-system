<script setup lang="ts">
import type { CourseAnalytics } from "@/types";

defineProps<{
  items: CourseAnalytics[];
}>();

function percent(rate: number): string {
  return `${((rate || 0) * 100).toFixed(1)}%`;
}
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <span>课程使用</span>
      <small>题库练习表现</small>
    </div>

    <div v-if="items.length" class="course-list">
      <div v-for="item in items" :key="item.course_id" class="course-row" data-test="course-row">
        <div class="course-main">
          <strong>{{ item.course_name }}</strong>
          <small>{{ item.question_count }} 题 · {{ item.practice_count }} 次练习</small>
        </div>
        <div class="course-meter">
          <span :style="{ width: percent(item.accuracy_rate) }"></span>
        </div>
        <b>{{ percent(item.accuracy_rate) }}</b>
      </div>
    </div>

    <p v-else class="chart-empty">暂无课程使用数据</p>
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
.course-list {
  display: grid;
  gap: var(--space-3);
}
.course-row {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) minmax(90px, 1fr) 52px;
  gap: var(--space-2);
  align-items: center;
}
.course-main {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.course-main strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-main);
  font-size: var(--text-sm);
}
.course-main small {
  color: var(--text-muted);
  font-size: 11px;
}
.course-meter {
  height: 9px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  overflow: hidden;
}
.course-meter span {
  display: block;
  height: 100%;
  max-width: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--primary), var(--emerald));
}
.course-row b {
  justify-self: end;
  color: var(--primary-strong);
  font-size: var(--text-xs);
}
</style>
