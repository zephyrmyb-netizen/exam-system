<script setup lang="ts">
import { computed } from "vue";
import type { DailyActivity } from "@/types";

const props = defineProps<{
  items: DailyActivity[];
}>();

const cells = computed(() => props.items.slice(-14));
const maxCount = computed(() => Math.max(1, ...cells.value.map((item) => item.count || 0)));

function level(count: number): number {
  if (!count) return 0;
  return Math.max(1, Math.ceil((count / maxCount.value) * 4));
}

function dayLabel(date: string): string {
  const [, , month, day] = date.match(/^(\d{4})-(\d{2})-(\d{2})/) || [];
  return month && day ? `${month}-${day}` : date.slice(5);
}
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <span>刷题热力</span>
      <small>近 {{ cells.length || 0 }} 天</small>
    </div>

    <div v-if="cells.length" class="heatmap-grid">
      <div
        v-for="item in cells"
        :key="item.date"
        class="heatmap-cell"
        :class="`level-${level(item.count)}`"
        data-test="heatmap-cell"
        :title="`${dayLabel(item.date)} · ${item.count} 题`"
      >
        <span>{{ dayLabel(item.date).slice(3) }}</span>
        <strong>{{ item.count }} 题</strong>
      </div>
    </div>

    <p v-else class="chart-empty">暂无刷题热力数据</p>
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
.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 7px;
}
.heatmap-cell {
  display: grid;
  align-content: center;
  gap: 2px;
  min-height: 54px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  text-align: center;
}
.heatmap-cell span {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}
.heatmap-cell strong {
  color: var(--text-main);
  font-size: 11px;
  font-weight: 850;
}
.level-1 { background: #dbeafe; }
.level-2 { background: #bfdbfe; }
.level-3 { background: #93c5fd; }
.level-4 { background: linear-gradient(135deg, var(--primary), var(--teal)); }
.level-4 span,
.level-4 strong {
  color: white;
}
@media (max-width: 420px) {
  .heatmap-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
