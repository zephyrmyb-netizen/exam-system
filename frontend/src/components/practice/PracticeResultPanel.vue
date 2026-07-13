<script setup>
import { computed } from "vue";
import { BookMarked, CheckCircle, ChevronLeft, XCircle } from "@lucide/vue";

const props = defineProps({
  result: { type: Object, required: true },
  currentAnswer: { type: String, default: "" },
  correctAnswerDisplay: { type: String, default: "" },
  loading: { type: Boolean, default: false },
});

const swipeHint = computed(() =>
  props.loading ? "加载中" : "向左滑动进入下一题",
);
</script>

<template>
  <div
    class="practice-result"
    :class="result.is_correct ? 'practice-result--correct' : 'practice-result--wrong'"
    role="status"
    aria-live="polite"
  >
    <div class="practice-result__head">
      <CheckCircle v-if="result.is_correct" :size="22" class="practice-result__icon" />
      <XCircle v-else :size="22" class="practice-result__icon" />
      <span class="practice-result__title">{{ result.is_correct ? "答对了" : "答错了" }}</span>
    </div>

    <p v-if="result.is_correct" class="practice-result__next">正确，正在进入下一题</p>

    <div v-else class="practice-result__body">
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
        <span class="practice-result__label">查看解析</span>
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

    <div v-if="!result.is_correct" class="practice-swipe-hint">
      <ChevronLeft :size="15" :stroke-width="2.5" class="practice-swipe-hint__icon" />
      <span>{{ swipeHint }}</span>
    </div>
  </div>
</template>

<style scoped>
.practice-result {
  display: grid;
  gap: 7px;
  padding: 10px 11px;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
}

.practice-result--correct {
  background: var(--emerald-soft);
  border-color: var(--emerald);
}

.practice-result--wrong {
  background: var(--rose-soft);
  border-color: var(--rose);
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
  font-size: 15px;
  font-weight: 800;
}

.practice-result__next {
  margin: 0;
  color: #065f46;
  font-size: 13px;
  font-weight: 700;
}

.practice-result__body {
  display: grid;
  gap: 6px;
}

.practice-result__item,
.practice-result__analysis {
  display: grid;
  gap: 4px;
  padding: 7px 9px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.62);
}

.practice-result__label {
  font-size: 11px;
  font-weight: 800;
  line-height: 1.3;
  color: var(--text-muted);
}

.practice-result__item span:last-child,
.practice-result__analysis p {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
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
  padding: 6px 10px;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
}

.practice-result__wrongbook--recorded {
  color: var(--emerald);
  background: var(--emerald-soft);
}

.practice-swipe-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  justify-self: start;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--surface-soft);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
  opacity: 0.72;
}

.practice-swipe-hint__icon {
}

@media (max-width: 420px) {
  .practice-result {
    padding: 10px;
    gap: 8px;
  }
}
</style>
