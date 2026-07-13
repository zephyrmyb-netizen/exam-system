<script setup>
import { CheckCircle, XCircle } from "@lucide/vue";
import { TRUE_FALSE_FALSE, TRUE_FALSE_TRUE } from "../../utils/question";

const props = defineProps({
  questionType: { type: String, required: true },
  options: { type: Array, default: () => [] },
  selectedAnswer: { type: String, default: "" },
  selectedAnswers: { type: Array, default: () => [] },
  result: { type: Object, default: null },
  correctAnswerDisplay: { type: String, default: "" },
});

const emit = defineEmits(["pick-single", "toggle-multiple"]);

function isSelected(key) {
  return props.questionType === "multiple_choice"
    ? props.selectedAnswers.includes(key)
    : props.selectedAnswer === key;
}

function getOptionState(key) {
  if (!props.result) return "";
  if (key === props.correctAnswerDisplay) return "is-correct";
  if (isSelected(key)) return "is-wrong";
  return "";
}

function pickOption(key) {
  if (props.result) return;
  if (props.questionType === "multiple_choice") {
    emit("toggle-multiple", key);
  } else {
    emit("pick-single", key);
  }
}
</script>

<template>
  <div v-if="questionType === 'true_false'" class="practice-boolean-grid">
    <button
      class="practice-boolean-button practice-boolean-button--true"
      :class="[getOptionState(TRUE_FALSE_TRUE), { 'is-selected': isSelected(TRUE_FALSE_TRUE) && !result }]"
      type="button"
      :aria-pressed="isSelected(TRUE_FALSE_TRUE)"
      :disabled="!!result"
      @click="pickOption(TRUE_FALSE_TRUE)"
    >
      <CheckCircle :size="22" :stroke-width="2.5" />
      <span>{{ TRUE_FALSE_TRUE }}</span>
    </button>
    <button
      class="practice-boolean-button practice-boolean-button--false"
      :class="[getOptionState(TRUE_FALSE_FALSE), { 'is-selected': isSelected(TRUE_FALSE_FALSE) && !result }]"
      type="button"
      :aria-pressed="isSelected(TRUE_FALSE_FALSE)"
      :disabled="!!result"
      @click="pickOption(TRUE_FALSE_FALSE)"
    >
      <XCircle :size="22" :stroke-width="2.5" />
      <span>{{ TRUE_FALSE_FALSE }}</span>
    </button>
  </div>

  <div v-else class="practice-options-grid">
    <button
      v-for="option in options"
      :key="option.key"
      class="practice-option-card"
      :class="[getOptionState(option.key), { 'is-selected': isSelected(option.key) && !result }]"
      type="button"
      :aria-label="`选项 ${option.key}：${option.value}`"
      :aria-pressed="isSelected(option.key)"
      :disabled="!!result"
      @click="pickOption(option.key)"
    >
      <span v-if="questionType === 'multiple_choice'" class="practice-option-card__check">
        {{ isSelected(option.key) ? "✓" : "" }}
      </span>
      <span class="practice-option-card__key">{{ option.key }}</span>
      <span class="practice-option-card__value">{{ option.value }}</span>
    </button>
  </div>
</template>

<style scoped>
.practice-options-grid {
  display: grid;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  /* 允许父级横向滑动手势，垂直滚动仍可用 */
  touch-action: pan-y;
}

.practice-option-card {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: start;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 46px;
  padding: 7px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: var(--surface);
  text-align: left;
  color: var(--text-main);
  transition: border-color var(--ease-out), background var(--ease-out),
              box-shadow var(--ease-out), transform 0.14s ease-out;
  -webkit-tap-highlight-color: transparent;
}

.practice-option-card:hover:not(:disabled) {
  border-color: var(--line-accent);
  background: #fbfdff;
  box-shadow: var(--shadow-xs);
}

.practice-option-card:active:not(:disabled) {
  background: var(--primary-soft);
  transform: scale(0.985);
}

.practice-option-card.is-selected {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: inset 3px 0 0 var(--primary);
}

.practice-option-card__check,
.practice-option-card__key {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
}

.practice-option-card__check {
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--line-strong);
  border-radius: 6px;
  color: var(--primary);
  font-size: 12px;
  font-weight: 800;
}

.practice-option-card.is-selected .practice-option-card__check {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.practice-option-card__key {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 800;
}

.practice-option-card.is-selected .practice-option-card__key {
  background: var(--primary);
  color: #fff;
}

.practice-option-card__value {
  min-width: 0;
  font-size: 14px;
  line-height: 1.42;
  font-weight: 700;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.practice-option-card.is-correct {
  border-color: var(--emerald);
  background: var(--emerald-soft);
}

.practice-option-card.is-correct .practice-option-card__key,
.practice-option-card.is-correct .practice-option-card__check {
  background: var(--emerald);
  border-color: var(--emerald);
  color: #fff;
}

.practice-option-card.is-wrong {
  border-color: var(--rose);
  background: var(--rose-soft);
}

.practice-option-card.is-wrong .practice-option-card__key {
  background: var(--rose);
  color: #fff;
}

.practice-boolean-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  touch-action: pan-y;
}

.practice-boolean-button {
  display: grid;
  place-items: center;
  gap: 4px;
  min-width: 0;
  padding: 10px 10px;
  border: 2px solid var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-main);
  font-size: 14px;
  font-weight: 800;
  transition: border-color var(--ease-out), background var(--ease-out),
              color var(--ease-out), box-shadow var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.practice-boolean-button:hover:not(:disabled) {
  border-color: var(--line-accent);
}

.practice-boolean-button--true:hover:not(:disabled) {
  border-color: var(--emerald);
  background: var(--emerald-soft);
  color: var(--emerald);
}

.practice-boolean-button--false:hover:not(:disabled) {
  border-color: var(--rose);
  background: var(--rose-soft);
  color: var(--rose);
}

.practice-boolean-button.is-selected {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: inset 3px 0 0 var(--primary);
  color: var(--primary-strong);
}

.practice-boolean-button.is-correct {
  border-color: var(--emerald);
  background: var(--emerald-soft);
  color: var(--emerald);
}

.practice-boolean-button.is-wrong {
  border-color: var(--rose);
  background: var(--rose-soft);
  color: var(--rose);
}

.practice-option-card:disabled,
.practice-boolean-button:disabled {
  opacity: 1;
}

@media (min-width: 640px) {
  .practice-options-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 420px) {
  .practice-option-card {
    grid-template-columns: auto minmax(0, 1fr);
    min-height: 44px;
    padding: 7px 9px;
    gap: 7px;
    border-radius: 8px;
  }

  .practice-option-card__check {
    grid-column: 1;
  }

  .practice-option-card__key {
    grid-column: 1;
  }

  .practice-option-card__value {
    grid-column: 2;
    grid-row: 1 / span 2;
    align-self: center;
  }

  .practice-boolean-button {
    min-height: 44px;
    padding: 8px 10px;
    font-size: 13px;
    border-radius: var(--radius-md);
  }
}
</style>
