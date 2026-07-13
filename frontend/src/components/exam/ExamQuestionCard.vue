<script setup lang="ts">
import { computed } from "vue";
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

const optionEntries = computed(() => Object.entries(props.question.options || {}));

const questionTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    single_choice: "单选题",
    multiple_choice: "多选题",
    true_false: "判断题",
    fill_blank: "填空题",
    short_answer: "简答题",
  };
  return labels[props.question.question_type] || props.question.question_type || "题目";
});

function onTextInput(event: Event) {
  emit("answer", (event.target as HTMLTextAreaElement).value);
}
</script>

<template>
  <article class="exam-question-card">
    <div class="question-meta">
      <span class="question-number">第 {{ index + 1 }} / {{ total }} 题</span>
      <span>{{ questionTypeLabel }}</span>
      <span>{{ question.score || "--" }} 分</span>
    </div>

    <h2>{{ question.question }}</h2>

    <div v-if="optionEntries.length" class="option-grid">
      <button
        v-for="[key, value] in optionEntries"
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
  border-radius: var(--radius-xl);
  background: color-mix(in srgb, var(--surface) 92%, transparent);
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

.question-number { color: var(--primary-strong); background: var(--primary-soft) !important; }

h2 {
  margin: 0;
  color: var(--text-main);
  font-size: min(30px, 7vw);
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
  border-radius: var(--radius-md);
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
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.14);
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
  border-radius: var(--radius-md);
  padding: 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
  line-height: 1.6;
}

@media (prefers-color-scheme: dark) {
  .exam-question-card { background: color-mix(in srgb, var(--surface) 96%, transparent); }
}
</style>
