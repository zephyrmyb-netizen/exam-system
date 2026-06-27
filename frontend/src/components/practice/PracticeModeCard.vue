<script setup>
import { ChevronRight } from "@lucide/vue";

defineProps({
  icon: {
    type: [Object, Function],
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  iconColor: {
    type: String,
    default: "var(--primary)",
  },
  cta: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  showArrow: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["select"]);
</script>

<template>
  <button
    class="mode-card"
    :class="{ 'mode-card--cta': cta, 'mode-card--disabled': disabled }"
    type="button"
    :disabled="disabled"
    @click="$emit('select')"
  >
    <component :is="icon" :size="18" :stroke-width="2.5" class="mode-icon" :style="{ color: iconColor }" />
    <span class="mode-text">
      <span class="mode-title">{{ title }}</span>
      <span class="mode-description">{{ description }}</span>
    </span>
    <ChevronRight
      v-if="showArrow"
      :size="16"
      :stroke-width="2.5"
      class="mode-arrow"
    />
  </button>
</template>

<style scoped>
.mode-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 64px;
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out);
}

.mode-card:hover:not(.mode-card--disabled) {
  border-color: var(--line-accent);
  box-shadow: var(--shadow-xs);
}

.mode-card:active:not(.mode-card--disabled) {
  transform: scale(0.985);
}

.mode-card--cta {
  border-color: var(--primary-border);
  background: linear-gradient(135deg, #fafcff, #f0f6ff);
}

.mode-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-icon {
  flex-shrink: 0;
}

.mode-text {
  display: grid;
  gap: 1px;
  min-width: 0;
  flex: 1;
}

.mode-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-main);
}

.mode-description {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.mode-arrow {
  color: var(--text-placeholder);
  flex-shrink: 0;
}
</style>
