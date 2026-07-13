<script setup lang="ts">
import { computed } from "vue";
import type { ExamQuestion } from "@/types";
import { normalizeMultipleChoiceKeys, toggleMultipleChoiceKey } from "@/utils/question";

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
const selectedOptionKeys = computed(() => props.question.question_type === "multiple_choice"
  ? new Set(normalizeMultipleChoiceKeys(props.answer))
  : new Set(props.answer ? [props.answer] : []));

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

function selectOption(key: string) {
  emit("answer", props.question.question_type === "multiple_choice"
    ? toggleMultipleChoiceKey(props.answer, key)
    : key);
}
</script>

<template>
  <article class="exam-question-card" :aria-label="`第 ${index + 1} 题，共 ${total} 题`">
    <div class="question-meta">
      <span class="question-type">{{ questionTypeLabel }}</span>
      <span class="question-score">{{ question.score ?? "--" }} 分</span>
    </div>

    <h2>{{ question.question }}</h2>

    <div v-if="optionEntries.length" class="option-grid">
      <button
        v-for="[key, value] in optionEntries"
        :key="key"
        type="button"
        class="option-button"
        :class="{ active: selectedOptionKeys.has(key) }"
        :aria-pressed="selectedOptionKeys.has(key)"
        @click="selectOption(key)"
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
  gap: var(--space-3);
  padding: var(--space-5);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
  -webkit-backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
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

.question-type {
  color: var(--primary-strong);
  background: var(--primary-soft) !important;
}

.question-score {
  color: var(--text-muted);
}

h2 {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-size: var(--text-base);
  font-weight: 650;
  line-height: 1.65;
}

.option-grid {
  display: grid;
  gap: 10px;
}

.option-button {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-2);
  min-height: 60px;
  padding: 12px;
  border: 2px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-main);
  text-align: left;
  font: inherit;
  font-size: var(--text-md);
  font-weight: 600;
  line-height: 1.5;
  transition: transform var(--ease-spring), border-color var(--ease-out), background var(--ease-out), box-shadow var(--ease-out);
}

.option-button strong {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-secondary);
}

.option-button span { min-width: 0; overflow-wrap: anywhere; }
.option-button:active { transform: scale(.99); }

.option-button.active {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: 0 0 0 3px var(--primary-glow), var(--glass-inner-highlight);
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
  min-height: 144px;
  resize: vertical;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  padding: 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
  line-height: 1.6;
}

@media (max-width: 340px) {
  .exam-question-card { padding: var(--space-4); }
}
</style>
