<script setup>
import { ChevronLeft, X } from "@lucide/vue";

defineProps({
  courseName: { type: String, default: "" },
  modeLabel: { type: String, default: "" },
});

defineEmits(["back", "end"]);
</script>

<template>
  <div class="practice-topbar">
    <button class="practice-icon-button" type="button" aria-label="返回" @click="$emit('back')">
      <ChevronLeft :size="18" :stroke-width="2.5" />
    </button>

    <div class="practice-topbar__center">
      <span class="practice-topbar__title">{{ courseName || modeLabel || "练习" }}</span>
      <span v-if="modeLabel" class="practice-topbar__mode">{{ modeLabel }}</span>
    </div>

    <button class="practice-end-button" type="button" aria-label="结束练习" @click="$emit('end')">
      <X :size="16" :stroke-width="2.5" />
      <span class="practice-end-button__label">结束练习</span>
    </button>
  </div>
</template>

<style scoped>
.practice-topbar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 36px;
  overflow: hidden;
}

.practice-topbar__center {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
  flex: 1;
}

.practice-topbar__title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: 800;
  color: var(--text-secondary);
}

.practice-topbar__mode {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: #fef3c7;
  color: #92400e;
  font-size: 10px;
  font-weight: 800;
}

.practice-icon-button,
.practice-end-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  width: 34px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: var(--surface);
  color: var(--text-muted);
  transition: all var(--ease-out);
  flex-shrink: 0;
}

.practice-icon-button:hover,
.practice-end-button:hover {
  border-color: var(--line-accent);
  background: var(--surface-soft);
}

.practice-end-button:hover {
  color: var(--rose);
  border-color: var(--rose-border);
  background: var(--rose-soft);
}

.practice-end-button__label {
  display: none;
}

@media (min-width: 640px) {
  .practice-end-button {
    width: auto;
    padding: 0 12px;
    border-radius: var(--radius-full);
    gap: 4px;
  }

  .practice-end-button__label {
    display: inline;
    font-size: 12px;
    font-weight: 800;
  }
}
</style>
