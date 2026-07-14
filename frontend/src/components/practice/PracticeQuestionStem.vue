<script setup>
import { typeLabel } from "../../utils/question";

defineProps({
  question: { type: Object, required: true },
});

const difficultyLabels = {
  easy: "简单",
  normal: "中等",
  hard: "困难",
};
</script>

<template>
  <header class="practice-stem">
    <div class="practice-stem__meta">
      <span class="practice-stem__tag">{{ typeLabel(question.type) }}</span>
      <span
        v-if="question.difficulty && difficultyLabels[question.difficulty]"
        class="practice-stem__difficulty"
      >
        <i aria-hidden="true"></i>
        {{ difficultyLabels[question.difficulty] }}
      </span>
      <span v-if="question.subject || question.chapter" class="practice-stem__context">
        {{ [question.subject, question.chapter].filter(Boolean).join(" · ") }}
      </span>
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
  padding: 6px 2px 4px;
}

.practice-stem__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
  min-width: 0;
}

.practice-stem__tag,
.practice-stem__difficulty,
.practice-stem__hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 800;
  line-height: 1.3;
}

.practice-stem__context {
  min-width: 0;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.practice-stem__tag {
  background: var(--primary-soft);
  color: var(--primary-strong);
  border: 1px solid var(--primary-border);
}

.practice-stem__difficulty {
  color: var(--amber);
  background: var(--amber-soft);
}

.practice-stem__difficulty i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
}

.practice-stem__hint {
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.practice-stem__title {
  margin: 0;
  min-width: 0;
  font-size: 1.06rem;
  line-height: 1.62;
  font-weight: 700;
  color: var(--text-main);
  word-break: break-word;
  overflow-wrap: anywhere;
}

@media (max-width: 420px) {
  .practice-stem {
    padding: 4px 1px 3px;
  }

  .practice-stem__meta {
    gap: 5px;
  }

  .practice-stem__tag,
  .practice-stem__difficulty,
  .practice-stem__hint {
    padding: 2px 8px;
    font-size: 11px;
  }

  .practice-stem__title {
    font-size: 1rem;
    line-height: 1.44;
  }
}
</style>
