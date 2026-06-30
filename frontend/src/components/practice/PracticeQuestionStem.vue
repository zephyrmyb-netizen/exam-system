<script setup>
import { typeLabel } from "../../utils/question";

defineProps({
  question: { type: Object, required: true },
});
</script>

<template>
  <header class="practice-stem">
    <div class="practice-stem__meta">
      <span class="practice-stem__tag">{{ typeLabel(question.type) }}</span>
      <span v-if="question.subject" class="practice-stem__tag">{{ question.subject }}</span>
      <span v-if="question.chapter" class="practice-stem__tag">{{ question.chapter }}</span>
      <span v-if="question.type === 'multiple_choice'" class="practice-stem__hint">
        多选题，请选择所有正确选项
      </span>
    </div>
    <h2 class="practice-stem__title">{{ question.question }}</h2>
  </header>
</template>

<style scoped>
.practice-stem {
  display: grid;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(191, 219, 254, 0.8);
  border-radius: var(--radius-xl);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.92), rgba(255, 255, 255, 0.96));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.practice-stem__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  min-width: 0;
}

.practice-stem__tag,
.practice-stem__hint {
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 800;
  line-height: 1.3;
}

.practice-stem__tag {
  background: rgba(255, 255, 255, 0.9);
  color: var(--text-secondary);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.practice-stem__hint {
  background: #fef3c7;
  color: #92400e;
}

.practice-stem__title {
  margin: 0;
  min-width: 0;
  font-size: clamp(1rem, 0.96rem + 0.45vw, 1.22rem);
  line-height: 1.45;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--text-main);
  word-break: break-word;
}

@media (max-width: 420px) {
  .practice-stem {
    padding: 10px;
    border-radius: var(--radius-lg);
  }

  .practice-stem__meta {
    gap: 5px;
  }

  .practice-stem__tag,
  .practice-stem__hint {
    padding: 2px 8px;
    font-size: 11px;
  }
}
</style>
