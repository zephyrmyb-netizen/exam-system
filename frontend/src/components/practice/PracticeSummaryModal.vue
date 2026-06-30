<script setup>
import { ArrowRight, CheckCircle, Play, RefreshCw } from "@lucide/vue";

defineProps({
  show: { type: Boolean, default: false },
  answeredCount: { type: Number, default: 0 },
  correctCount: { type: Number, default: 0 },
  wrongCount: { type: Number, default: 0 },
  accuracy: { type: Number, default: null },
  canContinue: { type: Boolean, default: true },
});

defineEmits(["end", "continue"]);
</script>

<template>
  <transition name="fade">
    <div v-if="show" class="practice-summary">
      <div class="practice-summary__backdrop"></div>
      <div class="practice-summary__panel">
        <div
          class="practice-summary__icon"
          :class="answeredCount > 0 && accuracy !== null && accuracy >= 60
            ? 'practice-summary__icon--good'
            : 'practice-summary__icon--keep'"
        >
          <CheckCircle v-if="answeredCount > 0 && accuracy !== null && accuracy >= 60" :size="36" />
          <RefreshCw v-else :size="36" />
        </div>

        <p class="practice-summary__title">本次练习结束</p>
        <p class="practice-summary__desc">
          {{
            answeredCount > 0
              ? `本次练习已完成 ${answeredCount} 题，是否返回练习设置？`
              : "还没有完成题目，确定要退出本次练习吗？"
          }}
        </p>

        <div class="practice-summary__stats">
          <div class="practice-summary__stat">
            <span class="practice-summary__value">{{ answeredCount }}</span>
            <span class="practice-summary__label">答题</span>
          </div>
          <div class="practice-summary__stat">
            <span class="practice-summary__value practice-summary__value--good">{{ correctCount }}</span>
            <span class="practice-summary__label">正确</span>
          </div>
          <div class="practice-summary__stat">
            <span class="practice-summary__value practice-summary__value--bad">{{ wrongCount }}</span>
            <span class="practice-summary__label">错误</span>
          </div>
          <div class="practice-summary__stat">
            <span
              class="practice-summary__value"
              :class="{
                'practice-summary__value--good': accuracy !== null && accuracy >= 70,
                'practice-summary__value--bad': accuracy !== null && accuracy < 40,
              }"
            >
              {{ accuracy !== null ? `${accuracy}%` : "--" }}
            </span>
            <span class="practice-summary__label">正确率</span>
          </div>
        </div>

        <div class="practice-summary__actions">
          <button class="practice-primary-button" type="button" @click="$emit('end')">
            <ArrowRight :size="17" :stroke-width="2.5" />
            <span>结束练习</span>
          </button>
          <button v-if="canContinue" class="practice-secondary-button" type="button" @click="$emit('continue')">
            <Play :size="17" :stroke-width="2.5" />
            <span>继续练习</span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.practice-summary {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
}

.practice-summary__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.practice-summary__panel {
  position: relative;
  z-index: 1;
  display: grid;
  gap: var(--space-3);
  width: min(100%, 360px);
  padding: var(--space-6) var(--space-5);
  border-radius: var(--radius-2xl);
  background: var(--surface);
  box-shadow: var(--shadow-modal);
  text-align: center;
}

.practice-summary__icon {
  display: grid;
  place-items: center;
  width: 60px;
  height: 60px;
  margin: 0 auto;
  border-radius: 50%;
}

.practice-summary__icon--good {
  color: var(--emerald);
  background: var(--emerald-soft);
}

.practice-summary__icon--keep {
  color: #d97706;
  background: #fef3c7;
}

.practice-summary__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
  color: var(--text-main);
}

.practice-summary__desc {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.65;
  color: var(--text-muted);
}

.practice-summary__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.practice-summary__stat {
  display: grid;
  gap: 4px;
}

.practice-summary__value {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main);
}

.practice-summary__value--good {
  color: var(--emerald);
}

.practice-summary__value--bad {
  color: var(--rose);
}

.practice-summary__label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
}

.practice-summary__actions {
  display: grid;
  gap: 8px;
}

.practice-primary-button,
.practice-secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  min-height: 48px;
  padding: 12px 18px;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 800;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out), background var(--ease-out);
}

.practice-primary-button {
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.practice-secondary-button {
  border: 1.5px solid var(--line-strong);
  background: var(--surface);
  color: var(--text-main);
}

.practice-primary-button:hover,
.practice-secondary-button:hover {
  transform: translateY(-1px);
}

.practice-secondary-button:hover {
  border-color: var(--line-accent);
  background: var(--primary-soft);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 420px) {
  .practice-summary__panel {
    padding: var(--space-5) var(--space-4);
  }

  .practice-summary__stats {
    gap: 6px;
  }

  .practice-summary__value {
    font-size: 17px;
  }
}
</style>
