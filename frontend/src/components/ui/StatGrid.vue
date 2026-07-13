<script setup lang="ts">
import Card from "./card/Card.vue";

type StatGridItem = {
  label: string;
  value: string | number | null | undefined;
  detail?: string;
  tone?: "default" | "primary" | "danger";
};

withDefaults(defineProps<{
  items: StatGridItem[];
  label?: string;
}>(), {
  label: "统计数据",
});
</script>

<template>
  <div class="stat-grid" role="list" :aria-label="label">
    <Card
      v-for="item in items"
      :key="item.label"
      class="stat-grid__item"
      :class="`stat-grid__item--${item.tone || 'default'}`"
      role="listitem"
    >
      <strong class="stat-grid__value">{{ item.value ?? "--" }}</strong>
      <span v-if="item.detail" class="stat-grid__detail">{{ item.detail }}</span>
      <span class="stat-grid__label">{{ item.label }}</span>
    </Card>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(88px, 1fr));
  gap: var(--space-2);
  min-width: 0;
}

.stat-grid__item {
  display: grid;
  grid-template-columns: auto auto;
  align-content: center;
  justify-content: center;
  min-width: 0;
  min-height: 84px;
  padding: var(--space-3) var(--space-2);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  text-align: center;
  box-shadow: var(--shadow-xs);
}

.stat-grid__value {
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  line-height: 1.15;
}

.stat-grid__detail {
  align-self: end;
  margin: 0 0 2px 2px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.stat-grid__label {
  grid-column: 1 / -1;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 650;
}

.stat-grid__item--primary .stat-grid__value {
  color: var(--primary-strong);
}

.stat-grid__item--danger .stat-grid__value {
  color: var(--rose);
}
</style>
