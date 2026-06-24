<script setup>
import { Send, Shuffle } from "@lucide/vue";

defineProps({
  result: { type: Object, default: null },
  canSubmit: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  hasAnswerSelected: { type: Boolean, default: false },
  answerHint: { type: String, default: "" },
});

defineEmits(["submit", "skip"]);
</script>

<template>
  <div v-if="!result" class="practice-action-bar">
    <p v-if="!hasAnswerSelected && !submitting && answerHint" class="practice-action-bar__hint">
      {{ answerHint }}
    </p>

    <div class="practice-action-bar__panel">
      <button class="practice-skip-button" type="button" @click="$emit('skip')">
        <span>不会，换一题</span>
        <Shuffle :size="13" :stroke-width="2.5" />
      </button>

      <button class="practice-submit-button" type="button" :disabled="!canSubmit" @click="$emit('submit')">
        <Send :size="17" :stroke-width="2.5" />
        <span>{{ submitting ? "提交中..." : "提交答案" }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.practice-action-bar {
  display: grid;
  gap: 10px;
  position: sticky;
  bottom: var(--practice-sticky-bottom);
  z-index: 8;
}

.practice-action-bar__hint {
  margin: 0;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(248, 250, 253, 0.92);
  color: var(--text-placeholder);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  border: 1px solid rgba(226, 232, 240, 0.9);
  backdrop-filter: blur(8px);
}

.practice-action-bar__panel {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(14px);
}

.practice-submit-button,
.practice-skip-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 48px;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-weight: 800;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out), background var(--ease-out);
}

.practice-submit-button {
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.practice-submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.3);
}

.practice-submit-button:disabled {
  opacity: 0.48;
}

.practice-skip-button {
  border: 1px solid var(--line-soft);
  background: var(--surface-soft);
  color: var(--text-muted);
  white-space: nowrap;
}

.practice-skip-button:hover {
  border-color: var(--line-accent);
  color: var(--text-secondary);
}

@media (max-width: 420px) {
  .practice-action-bar__panel {
    grid-template-columns: 1fr;
  }
}
</style>
