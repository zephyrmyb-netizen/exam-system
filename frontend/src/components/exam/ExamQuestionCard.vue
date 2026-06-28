<script setup lang="ts">
import type { ExamQuestion } from "@/types";

const props = defineProps<{
  question: ExamQuestion;
  answer: string;
  index: number;
  total: number;
}>();

const emit = defineEmits<{
  answer: [value: string];
}>();

const optionEntries = () => Object.entries(props.question.options || {});

function onTextInput(event: Event) {
  emit("answer", (event.target as HTMLTextAreaElement).value);
}
</script>

<template>
  <article class="exam-question-card">
    <div class="question-meta">
      <span>第 {{ index + 1 }} / {{ total }} 题</span>
      <span>{{ question.question_type }}</span>
      <span>{{ question.score }} 分</span>
    </div>

    <h2>{{ question.question }}</h2>

    <div v-if="optionEntries().length" class="option-grid">
      <button
        v-for="[key, value] in optionEntries()"
        :key="key"
        type="button"
        class="option-button"
        :class="{ active: answer === key }"
        @click="emit('answer', key)"
      >
        <strong>{{ key }}</strong>
        <span>{{ value }}</span>
      </button>
    </div>

    <label v-else class="text-answer">
      <span>你的答案</span>
      <textarea
        :value="answer"
        rows="6"
        placeholder="在这里输入答案"
        @input="onTextInput"
      />
    </label>
  </article>
</template>

<style scoped>
.exam-question-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 800;
}

.question-meta span {
  padding: 4px 8px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
}

h2 {
  margin: 0;
  color: var(--text-main);
  font-size: clamp(22px, 5vw, 30px);
  line-height: 1.35;
}

.option-grid {
  display: grid;
  gap: var(--space-2);
}

.option-button {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-2);
  min-height: 58px;
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
  color: var(--text-main);
  text-align: left;
  font: inherit;
  font-weight: 760;
}

.option-button strong {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--primary);
}

.option-button.active {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: 0 12px 30px rgba(59, 130, 246, 0.14);
}

.option-button.active strong {
  background: var(--primary);
  color: #fff;
}

.text-answer {
  display: grid;
  gap: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 800;
}

.text-answer textarea {
  width: 100%;
  resize: vertical;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  padding: 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
  line-height: 1.6;
}
</style>
