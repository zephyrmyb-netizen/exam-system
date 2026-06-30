<script setup lang="ts">
import { computed } from "vue";
import type { DailyActivity } from "@/types";

const props = defineProps<{
  items: DailyActivity[];
}>();

const normalized = computed(() => props.items.slice(-14));
const maxCount = computed(() => Math.max(1, ...normalized.value.map((item) => item.count || 0)));

function dayLabel(date: string): string {
  const [, , month, day] = date.match(/^(\d{4})-(\d{2})-(\d{2})/) || [];
  return month && day ? `${month}-${day}` : date.slice(5);
}
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <span>练习趋势</span>
      <small>近 {{ normalized.length || 0 }} 天</small>
    </div>

    <div v-if="normalized.length" class="activity-bars">
      <div v-for="item in normalized" :key="item.date" class="activity-item">
        <div class="bar-track">
          <span
            class="bar-fill"
            data-test="activity-bar"
            :style="{ height: `${Math.max(8, (item.count / maxCount) * 100)}%` }"
          ></span>
        </div>
        <strong>{{ item.count }}</strong>
        <small>{{ dayLabel(item.date) }}</small>
      </div>
    </div>

    <p v-else class="chart-empty">暂无练习趋势</p>
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
.activity-bars {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(28px, 1fr));
  gap: 8px;
  align-items: end;
  min-height: 132px;
}
.activity-item {
  display: grid;
  gap: 5px;
  justify-items: center;
  min-width: 0;
}
.bar-track {
  position: relative;
  width: 100%;
  max-width: 26px;
  height: 86px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  overflow: hidden;
}
.bar-fill {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: var(--radius-full);
  background: linear-gradient(180deg, var(--primary), var(--teal));
}
.activity-item strong {
  color: var(--text-main);
  font-size: 12px;
  font-weight: 850;
}
.activity-item small {
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}
</style>
