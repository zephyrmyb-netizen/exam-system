<script setup lang="ts">
import { Bookmark, ListOrdered, Play, Shuffle, XCircle } from "@lucide/vue";

import type { Course } from "../../types";
import BottomSheet from "../ui/BottomSheet.vue";

export type PracticeMode = "sequential" | "random" | "wrong" | "bookmark";

const props = defineProps<{
  modelValue: boolean;
  course: Course | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  select: [mode: PracticeMode];
}>();

const modes = [
  { key: "sequential", label: "顺序练习", description: "按题目顺序逐题完成", icon: ListOrdered, needsQuestions: true },
  { key: "random", label: "随机练习", description: "随机排列题目进行练习", icon: Shuffle, needsQuestions: true },
  { key: "wrong", label: "错题强化", description: "集中回顾当前题库的错题", icon: XCircle, needsQuestions: false },
  { key: "bookmark", label: "收藏题目", description: "查看收藏的重点题目", icon: Bookmark, needsQuestions: false },
] as const;

function isDisabled(mode: (typeof modes)[number]) {
  return mode.needsQuestions && (props.course?.question_count ?? 0) <= 0;
}

function selectMode(mode: PracticeMode) {
  const target = modes.find((item) => item.key === mode);
  if (!target || isDisabled(target)) return;
  emit("select", mode);
}
</script>

<template>
  <BottomSheet :model-value="modelValue" title="选择练习模式" @update:model-value="emit('update:modelValue', $event)">
    <section v-if="course" class="practice-mode-sheet" data-testid="practice-mode-sheet">
      <p class="practice-mode-sheet__summary">{{ course.question_count ?? 0 }} 道题目</p>
      <button
        v-for="mode in modes"
        :key="mode.key"
        class="practice-mode-sheet__option"
        :data-practice-mode="mode.key"
        type="button"
        :disabled="isDisabled(mode)"
        @click="selectMode(mode.key)"
      >
        <span class="practice-mode-sheet__icon"><component :is="mode.icon" :size="20" :stroke-width="2.25" /></span>
        <span class="practice-mode-sheet__copy">
          <strong>{{ mode.label }}</strong>
          <small>{{ mode.description }}</small>
        </span>
        <Play :size="18" :stroke-width="2.4" aria-hidden="true" />
      </button>
    </section>
  </BottomSheet>
</template>

<style scoped>
.practice-mode-sheet {
  display: grid;
  gap: 10px;
  padding-bottom: var(--space-2);
}

.practice-mode-sheet__summary {
  margin: 0 2px 2px;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 650;
}

.practice-mode-sheet__option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 74px;
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  color: var(--text-main);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition:
    border-color var(--ease-out),
    background var(--ease-out),
    transform var(--ease-out);
}

.practice-mode-sheet__option:hover:not(:disabled) {
  border-color: var(--line-accent);
  background: var(--primary-soft);
}

.practice-mode-sheet__option:active:not(:disabled) {
  transform: scale(0.99);
}

.practice-mode-sheet__option:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

.practice-mode-sheet__icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.practice-mode-sheet__copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.practice-mode-sheet__copy strong {
  font-size: var(--text-base);
  font-weight: 800;
}

.practice-mode-sheet__copy small {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
}

.practice-mode-sheet__option > :last-child {
  color: var(--primary-strong);
}
</style>
