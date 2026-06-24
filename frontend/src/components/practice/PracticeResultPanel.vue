<script setup>
import { ArrowRight, BookMarked, CheckCircle, XCircle } from "@lucide/vue";

defineProps({
  result: { type: Object, required: true },
  currentAnswer: { type: String, default: "" },
  correctAnswerDisplay: { type: String, default: "" },
  loading: { type: Boolean, default: false },
});

defineEmits(["next"]);
</script>

<template>
  <div class="practice-result" :class="result.is_correct ? 'practice-result--correct' : 'practice-result--wrong'">
    <div class="practice-result__head">
      <CheckCircle v-if="result.is_correct" :size="22" class="practice-result__icon" />
      <XCircle v-else :size="22" class="practice-result__icon" />
      <span class="practice-result__title">{{ result.is_correct ? "回答正确" : "回答错误" }}</span>
    </div>

    <div class="practice-result__body">
      <div class="practice-result__item">
        <span class="practice-result__label">你的答案</span>
        <span :class="result.is_correct ? 'practice-result__value--ok' : 'practice-result__value--bad'">
          {{ currentAnswer || "（未作答）" }}
        </span>
      </div>
      <div v-if="!result.is_correct" class="practice-result__item">
        <span class="practice-result__label">正确答案</span>
        <span class="practice-result__value--ok">{{ correctAnswerDisplay }}</span>
      </div>
      <div v-if="result.analysis" class="practice-result__analysis">
        <span class="practice-result__label">解析</span>
        <p>{{ result.analysis }}</p>
      </div>
    </div>

    <div
      v-if="!result.is_correct"
      class="practice-result__wrongbook"
      :class="{ 'practice-result__wrongbook--recorded': result.wrongbook_recorded }"
    >
      <BookMarked :size="14" :stroke-width="2.5" />
      <span>{{ result.wrongbook_recorded ? "已记录到错题本" : "已加入错题本" }}</span>
    </div>

    <button class="practice-primary-button" type="button" :disabled="loading" @click="$emit('next')">
      <ArrowRight :size="17" :stroke-width="2.5" />
      <span>{{ loading ? "加载中..." : "下一题" }}</span>
    </button>
  </div>
</template>

<style scoped>
.practice-result {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: var(--radius-xl);
  border: 1px solid transparent;
}

.practice-result--correct {
  background: var(--emerald-soft);
  border-color: var(--emerald-border);
}

.practice-result--wrong {
  background: var(--rose-soft);
  border-color: var(--rose-border);
}

.practice-result__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.practice-result__icon {
  flex-shrink: 0;
}

.practice-result--correct .practice-result__icon,
.practice-result--correct .practice-result__title,
.practice-result__value--ok {
  color: #065f46;
}

.practice-result--wrong .practice-result__icon,
.practice-result--wrong .practice-result__title,
.practice-result__value--bad {
  color: #991b1b;
}

.practice-result__title {
  font-size: 17px;
  font-weight: 800;
}

.practice-result__body {
  display: grid;
  gap: 12px;
}

.practice-result__item,
.practice-result__analysis {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.65);
}

.practice-result__label {
  font-size: 11px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.practice-result__item span:last-child,
.practice-result__analysis p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  font-weight: 700;
  word-break: break-word;
}

.practice-result__analysis p {
  color: var(--text-secondary);
  font-weight: 600;
}

.practice-result__wrongbook {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  justify-self: start;
  padding: 7px 12px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.65);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 700;
}

.practice-result__wrongbook--recorded {
  color: var(--emerald);
  background: rgba(236, 253, 245, 0.9);
}

.practice-primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  min-height: 50px;
  padding: 13px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font-size: var(--text-base);
  font-weight: 800;
  box-shadow: var(--shadow-primary);
  transition: transform var(--ease-out), box-shadow var(--ease-out);
}

.practice-primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.3);
}

.practice-primary-button:disabled {
  opacity: 0.5;
}

@media (max-width: 420px) {
  .practice-result {
    padding: 16px;
  }
}
</style>
