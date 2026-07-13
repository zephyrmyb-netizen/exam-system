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
  gap: 6px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 4px 2px 2px;
}

.practice-stem__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
  min-width: 0;
}

.practice-stem__tag,
.practice-stem__hint {
  padding: 2px 8px;
  border-radius: 4px;
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
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.practice-stem__title {
  margin: 0;
  min-width: 0;
  font-size: 1rem;
  line-height: 1.42;
  font-weight: 800;
  color: var(--text-main);
  word-break: break-word;
}

@media (max-width: 420px) {
  .practice-stem {
    padding: 2px 1px;
  }

  .practice-stem__meta {
    gap: 5px;
  }

  .practice-stem__tag,
  .practice-stem__hint {
    padding: 2px 8px;
    font-size: 11px;
  }

  .practice-stem__title {
    font-size: 0.96rem;
    line-height: 1.38;
  }
}
</style>
