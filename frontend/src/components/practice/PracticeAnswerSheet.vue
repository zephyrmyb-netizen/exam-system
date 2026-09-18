<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { Flag } from "@lucide/vue";

import type { PracticeSessionQuestion } from "../../composables/usePracticeSession";
import BottomSheet from "../ui/BottomSheet.vue";

const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    items: PracticeSessionQuestion[];
    currentIndex: number;
    totalQuestions?: number;
  }>(),
  { totalQuestions: 0 },
);

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  jump: [index: number];
}>();

const onlyUnanswered = ref(false);
const answerSheetRoot = ref<HTMLElement | null>(null);

const isAnswered = (item: PracticeSessionQuestion) => item.answer.trim().length > 0;

const answeredCount = computed(() => props.items.filter(isAnswered).length);
const markedCount = computed(() => props.items.filter((item) => item.marked).length);
const visibleItems = computed(() =>
  props.items.map((item, index) => ({ item, index })).filter(({ item }) => !onlyUnanswered.value || !isAnswered(item)),
);
const unansweredCount = computed(() => Math.max(0, props.items.length - answeredCount.value));
const progressLabel = computed(() => {
  const total = props.totalQuestions > 0 ? props.totalQuestions : props.items.length;
  return `${answeredCount.value}/${total}`;
});

function close(): void {
  emit("update:modelValue", false);
}

function jumpTo(index: number): void {
  emit("jump", index);
  close();
}

watch(
  () => props.modelValue,
  async (opened) => {
    if (!opened) return;
    await nextTick();
    answerSheetRoot.value
      ?.querySelector("[data-current-question='true']")
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  },
);
</script>

<template>
  <BottomSheet :model-value="modelValue" title="答题卡" @update:model-value="emit('update:modelValue', $event)">
    <section ref="answerSheetRoot" class="practice-answer-sheet" data-practice-answer-card>
      <div class="practice-answer-sheet__summary" aria-label="答题卡进度">
        <span
          >已答 <strong>{{ answeredCount }}</strong></span
        >
        <span
          >待答 <strong>{{ unansweredCount }}</strong></span
        >
        <span
          >标记 <strong>{{ markedCount }}</strong></span
        >
      </div>

      <p class="practice-answer-sheet__progress">当前练习进度 {{ progressLabel }}</p>

      <label class="practice-answer-sheet__filter">
        <input v-model="onlyUnanswered" type="checkbox" />
        <span>只看未答题</span>
      </label>

      <div v-if="visibleItems.length" class="practice-answer-sheet__grid" aria-label="练习答题卡">
        <button
          v-for="{ item, index } in visibleItems"
          :key="item.question.id"
          class="practice-answer-sheet__number"
          :class="{
            'practice-answer-sheet__number--answered': isAnswered(item),
            'practice-answer-sheet__number--current': index === currentIndex,
          }"
          type="button"
          :aria-label="`第 ${item.sessionOrder} 题${item.result ? '，已答' : '，待答'}${item.marked ? '，已标记' : ''}`"
          :data-session-question="index"
          :data-current-question="index === currentIndex"
          @click="jumpTo(index)"
        >
          <span>{{ item.sessionOrder }}</span>
          <Flag
            v-if="item.marked"
            class="practice-answer-sheet__mark"
            :size="11"
            :stroke-width="3"
            fill="currentColor"
          />
        </button>
      </div>

      <p v-else class="practice-answer-sheet__empty">当前没有符合条件的题目。</p>
    </section>
  </BottomSheet>
</template>

<style scoped>
.practice-answer-sheet {
  position: relative;
  display: grid;
  gap: 14px;
  padding: 0 2px 4px;
}

.practice-answer-sheet__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  background: var(--surface-card);
}

.practice-answer-sheet__summary span {
  display: grid;
  gap: 2px;
  padding: 12px 6px;
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
}

.practice-answer-sheet__summary span + span {
  border-left: 1px solid var(--glass-border);
}

.practice-answer-sheet__summary strong {
  color: var(--text-primary);
  font-size: 18px;
  line-height: 1;
}

.practice-answer-sheet__progress {
  margin: -4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
}

.practice-answer-sheet__filter {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 700;
}

.practice-answer-sheet__filter input {
  width: 18px;
  height: 18px;
  accent-color: var(--emerald);
}

.practice-answer-sheet__grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  max-height: min(42dvh, 330px);
  padding: 2px;
  overflow-y: auto;
}

.practice-answer-sheet__number {
  position: relative;
  display: grid;
  width: 100%;
  min-width: 44px;
  aspect-ratio: 1;
  place-items: center;
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  background: var(--surface-card);
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 800;
}

.practice-answer-sheet__number--answered {
  border-color: var(--emerald);
  background: var(--emerald);
  color: #fff;
}

.practice-answer-sheet__number--current {
  outline: 3px solid color-mix(in srgb, var(--primary) 35%, transparent);
  outline-offset: 2px;
}

.practice-answer-sheet__mark {
  position: absolute;
  top: 4px;
  right: 4px;
  color: #f59e0b;
}

.practice-answer-sheet__number--answered .practice-answer-sheet__mark {
  color: #fff3c4;
}

.practice-answer-sheet__empty {
  margin: 8px 0;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
}
</style>
