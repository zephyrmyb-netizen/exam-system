<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { Send } from "@lucide/vue";

defineProps({
  result: { type: Object, default: null },
  canSubmit: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  hasAnswerSelected: { type: Boolean, default: false },
  answerHint: { type: String, default: "" },
  // 仅文本题（fill_blank / short_answer）需要保留「提交答案」按钮；
  // 选择题改为点击即提交，不再走 ActionBar。
  isTextQuestion: { type: Boolean, default: false },
});

defineEmits(["submit"]);

const keyboardOffset = ref(0);

function handleViewportResize() {
  if (window.visualViewport) {
    const diff = window.innerHeight - window.visualViewport.height;
    keyboardOffset.value = diff > 120 ? diff : 0;
  }
}

onMounted(() => {
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", handleViewportResize);
  }
});

onUnmounted(() => {
  if (window.visualViewport) {
    window.visualViewport.removeEventListener("resize", handleViewportResize);
  }
});
</script>

<template>
  <div
    v-if="isTextQuestion && !result"
    class="practice-action-bar"
    :style="{ bottom: keyboardOffset ? `${keyboardOffset}px` : 'var(--practice-sticky-bottom)' }"
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
  position: fixed;
  left: max(8px, env(safe-area-inset-left));
  right: max(8px, env(safe-area-inset-right));
  bottom: var(--practice-sticky-bottom);
  z-index: 8;
  width: auto;
  max-width: 100%;
  min-width: 0;
}

.practice-action-bar__hint {
  margin: 0;
  min-width: 0;
  padding: 7px 10px;
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
  gap: 8px;
  min-width: 0;
  width: 100%;
  max-width: 100%;
  padding: 8px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(14px);
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
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font-weight: 800;
  box-shadow: var(--shadow-primary);
  transition: transform var(--ease-spring), box-shadow var(--ease-out),
              border-color var(--ease-out), background var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.practice-submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.3);
}

/* 按压反馈：用弹性曲线让按钮回弹更柔和 */
.practice-submit-button:active:not(:disabled) {
  transform: scale(0.96);
  transition: transform 0.08s cubic-bezier(0.34, 1.56, 0.64, 1);
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

@media (min-width: 760px) {
  .practice-action-bar {
    left: 50%;
    right: auto;
    width: min(612px, calc(100% - 28px));
    transform: translateX(-50%);
  }
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
