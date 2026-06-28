<script setup lang="ts">
import type { TagAccuracy } from "@/types";

defineProps<{
  items: TagAccuracy[];
}>();

function percent(rate: number): string {
  return `${Math.round((rate || 0) * 100)}%`;
}
</script>

<template>
  <div class="chart-card">
    <div class="chart-head">
      <span>知识点掌握</span>
      <small>优先补弱项</small>
    </div>

    <div v-if="items.length" class="tag-list">
      <div v-for="item in items" :key="item.tag_id" class="tag-row" data-test="tag-row">
        <div class="tag-name">
          <strong>{{ item.tag_name }}</strong>
          <small>{{ item.total_count }} 次练习</small>
        </div>
        <div class="tag-meter">
          <span :style="{ width: percent(item.accuracy_rate) }"></span>
        </div>
        <b>{{ percent(item.accuracy_rate) }}</b>
      </div>
    </div>

    <p v-else class="chart-empty">暂无知识点数据</p>
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
.tag-list {
  display: grid;
  gap: var(--space-3);
}
.tag-row {
  display: grid;
  grid-template-columns: minmax(90px, 1fr) minmax(92px, 1.2fr) 42px;
  gap: var(--space-2);
  align-items: center;
}
.tag-name {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.tag-name strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-main);
  font-size: var(--text-sm);
}
.tag-name small {
  color: var(--text-muted);
  font-size: 11px;
}
.tag-meter {
  height: 9px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  overflow: hidden;
}
.tag-meter span {
  display: block;
  height: 100%;
  max-width: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--primary), var(--teal));
}
.tag-row b {
  justify-self: end;
  color: var(--primary-strong);
  font-size: var(--text-xs);
}
</style>
