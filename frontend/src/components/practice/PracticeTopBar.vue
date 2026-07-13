<script setup>
import { ChevronLeft, LogOut } from "@lucide/vue";

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
    </div>

    <button class="practice-end-button" type="button" aria-label="结束练习" @click="$emit('end')">
      <LogOut :size="16" :stroke-width="2.5" />
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
  min-height: 40px;
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

.practice-icon-button,
.practice-end-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  width: 40px;
  border: 1px solid var(--line-soft);
  border-radius: 6px;
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
  color: var(--primary-strong);
  border-color: var(--line-accent);
  background: var(--primary-soft);
}

.practice-end-button__label {
  display: none;
}

@media (min-width: 420px) {
  .practice-end-button {
    width: auto;
    padding: 0 12px;
    border-radius: 6px;
    gap: 4px;
  }

  .practice-end-button__label {
    display: inline;
    font-size: 12px;
    font-weight: 800;
  }
}

</style>
