<script setup>
import { Send } from "@lucide/vue";

defineProps({
  result: { type: Object, default: null },
  canSubmit: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  hasAnswerSelected: { type: Boolean, default: false },
  answerHint: { type: String, default: "" },
  // 多选和文本题保留显式提交；单选与判断题点击选项后立即判定。
  showSubmitButton: { type: Boolean, default: false },
});

defineEmits(["submit"]);

</script>

<template>
  <div
    v-if="showSubmitButton && !result"
    class="practice-action-bar"
  >
    <p v-if="!hasAnswerSelected && !submitting && answerHint" class="practice-action-bar__hint">
      {{ answerHint }}
    </p>

    <div class="practice-action-bar__panel">
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
  gap: 6px;
  width: auto;
  max-width: 100%;
  min-width: 0;
  padding: 4px 0 calc(12px + env(safe-area-inset-bottom));
}

.practice-action-bar__hint {
  margin: 0;
  min-width: 0;
  padding: 7px 10px;
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  color: var(--text-placeholder);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  border: 1px solid var(--line-soft);
}

.practice-action-bar__panel {
  display: grid;
  gap: 8px;
  min-width: 0;
  width: 100%;
  max-width: 100%;
  padding: 8px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.practice-submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-weight: 800;
  box-shadow: var(--shadow-xs);
  transition: box-shadow var(--ease-out), background var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.practice-submit-button:hover:not(:disabled) {
  background: var(--primary-strong);
  box-shadow: var(--shadow-sm);
}

/* 按压反馈：用弹性曲线让按钮回弹更柔和 */
.practice-submit-button:active:not(:disabled) {
  box-shadow: var(--shadow-xs);
}

.practice-submit-button:disabled {
  opacity: 0.48;
}

.practice-submit-button span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 420px) {
  .practice-action-bar__hint {
    display: none;
  }

  .practice-submit-button {
    width: 100%;
    min-height: 42px;
    padding: 9px 10px;
    font-size: 14px;
  }
}
</style>
