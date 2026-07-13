<script setup lang="ts">
import { computed, ref } from "vue";

import Button from "./button/Button.vue";

type FilterTabItem = {
  value: string;
  label: string;
  disabled?: boolean;
};

const props = withDefaults(defineProps<{
  modelValue: string;
  items: FilterTabItem[];
  label?: string;
}>(), {
  label: "筛选",
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  change: [value: string];
}>();

const tabListRef = ref<HTMLElement | null>(null);
const effectiveActiveValue = computed(() => {
  const activeItem = props.items.find((item) => item.value === props.modelValue && !item.disabled);
  return activeItem?.value ?? props.items.find((item) => !item.disabled)?.value;
});

function isActive(item: FilterTabItem): boolean {
  return !item.disabled && item.value === effectiveActiveValue.value;
}

function select(item: FilterTabItem) {
  if (item.disabled || item.value === props.modelValue) return;
  emit("update:modelValue", item.value);
  emit("change", item.value);
}

function moveSelection(event: KeyboardEvent) {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  const buttons = Array.from(
    tabListRef.value?.querySelectorAll<HTMLElement>('[role="tab"]:not(:disabled)') || [],
  );
  if (!buttons.length) return;

  event.preventDefault();
  const currentIndex = Math.max(0, buttons.indexOf(event.currentTarget as HTMLElement));
  let targetIndex = currentIndex;
  if (event.key === "Home") targetIndex = 0;
  if (event.key === "End") targetIndex = buttons.length - 1;
  if (event.key === "ArrowLeft") targetIndex = (currentIndex - 1 + buttons.length) % buttons.length;
  if (event.key === "ArrowRight") targetIndex = (currentIndex + 1) % buttons.length;

  const targetButton = buttons[targetIndex];
  const targetItem = props.items.find((item) => item.value === targetButton.dataset.tabValue);
  if (!targetItem) return;
  targetButton.focus();
  select(targetItem);
}
</script>

<template>
  <div ref="tabListRef" class="filter-tabs" role="tablist" :aria-label="label">
    <Button
      v-for="item in items"
      :key="item.value"
      variant="ghost"
      size="sm"
      :class="isActive(item) ? 'filter-tabs__tab filter-tabs__tab--active' : 'filter-tabs__tab'"
      type="button"
      role="tab"
      :data-tab-value="item.value"
      :aria-selected="isActive(item)"
      :tabindex="isActive(item) ? 0 : -1"
      :disabled="item.disabled"
      @click="select(item)"
      @keydown="moveSelection"
    >
      {{ item.label }}
    </Button>
  </div>
</template>

<style scoped>
.filter-tabs {
  display: flex;
  max-width: 100%;
  gap: 2px;
  padding: 4px;
  overflow-x: auto;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-full);
  background: var(--glass-card);
  box-shadow: var(--shadow-xs), var(--glass-inner-highlight);
  scrollbar-width: none;
}

.filter-tabs::-webkit-scrollbar {
  display: none;
}

.filter-tabs > .filter-tabs__tab {
  min-width: max-content;
  min-height: 36px;
  flex: 1 0 auto;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
  transition: color var(--ease-out), background var(--ease-out), box-shadow var(--ease-out);
}

.filter-tabs > .filter-tabs__tab--active {
  background: var(--surface);
  color: var(--primary-strong);
  box-shadow: var(--shadow-xs);
}
</style>
