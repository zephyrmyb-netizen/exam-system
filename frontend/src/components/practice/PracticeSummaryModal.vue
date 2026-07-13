<script setup>
import { computed } from "vue";
import { ArrowRight, CheckCircle, Clock3, Play, RefreshCw, Target, XCircle } from "@lucide/vue";

const props = defineProps({
  show: { type: Boolean, default: false },
  answeredCount: { type: Number, default: 0 },
  correctCount: { type: Number, default: 0 },
  wrongCount: { type: Number, default: 0 },
  accuracy: { type: Number, default: null },
  durationSeconds: { type: Number, default: null },
  courseName: { type: String, default: "" },
  modeLabel: { type: String, default: "" },
  completed: { type: Boolean, default: false },
  canContinue: { type: Boolean, default: true },
});

const accuracyValue = computed(() => Math.max(0, Math.min(100, Number(props.accuracy) || 0)));

const durationText = computed(() => {
  if (props.durationSeconds === null || props.durationSeconds === undefined) return "--";
  const seconds = Math.max(0, Math.floor(props.durationSeconds));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
});

const performanceLabel = computed(() => {
  if (props.accuracy === null || props.accuracy === undefined) return "完成练习";
  if (props.accuracy >= 80) return "表现优秀";
  if (props.accuracy >= 60) return "继续保持";
  return "继续加油";
});

const encouragement = computed(() => {
  if (props.accuracy === null || props.accuracy === undefined) return "学习记录已同步，继续保持练习节奏。";
  return `正确率达到 ${props.accuracy}%，${props.accuracy >= 80 ? "继续保持！" : "下次会更好。"}`;
});

defineEmits(["end", "continue", "review"]);
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

        <p class="practice-summary__title">{{ completed ? "练习完成！" : "结束练习" }}</p>
        <p v-if="completed" class="practice-summary__subtitle">{{ courseName || "本题库" }} · {{ modeLabel || "练习" }}</p>
        <span v-if="completed" class="practice-summary__badge">{{ performanceLabel }}</span>
        <p class="practice-summary__desc">{{ completed ? encouragement : answeredCount > 0 ? `本次练习已完成 ${answeredCount} 题，是否返回练习设置？` : "还没有完成题目，确定要退出本次练习吗？" }}</p>

        <div v-if="answeredCount > 0" class="practice-summary__score">
          <div class="practice-summary__ring" :style="{ '--summary-score': `${accuracyValue}%` }">
            <span>{{ accuracy !== null ? `${accuracy}%` : "--" }}</span>
            <small>正确率</small>
          </div>
          <div class="practice-summary__score-copy">
            <span><Clock3 :size="14" /> 用时 <strong>{{ durationText }}</strong></span>
            <span><Target :size="14" /> 总题数 <strong>{{ answeredCount }}</strong></span>
          </div>
        </div>

        <div class="practice-summary__details">
          <div class="practice-summary__detail"><span><CheckCircle :size="18" />答对</span><strong class="practice-summary__value--good">{{ correctCount }} 题</strong></div>
          <div class="practice-summary__detail"><span><XCircle :size="18" />答错</span><strong class="practice-summary__value--bad">{{ wrongCount }} 题</strong></div>
          <div class="practice-summary__detail"><span><Target :size="18" />正确率</span><strong>{{ accuracy !== null ? `${accuracy}%` : "--" }}</strong></div>
          <div class="practice-summary__detail practice-summary__duration"><span><Clock3 :size="18" />用时</span><strong>{{ durationText }}</strong></div>
        </div>

        <div class="practice-summary__actions">
          <template v-if="completed">
            <button class="practice-primary-button" type="button" @click="$emit('review')">
              <ArrowRight :size="17" :stroke-width="2.5" />
              <span>查看错题详情</span>
            </button>
            <button class="practice-secondary-button" type="button" @click="$emit('end')">
              <span>返回题库</span>
            </button>
          </template>
          <template v-else>
            <button class="practice-primary-button" type="button" @click="$emit('end')">
              <ArrowRight :size="17" :stroke-width="2.5" />
              <span>结束练习</span>
            </button>
            <button v-if="canContinue" class="practice-secondary-button" type="button" @click="$emit('continue')">
              <Play :size="17" :stroke-width="2.5" />
              <span>继续练习</span>
            </button>
          </template>
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
  padding: max(16px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right)) max(16px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
}

.practice-summary__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.38);
}

.practice-summary__panel {
  position: relative;
  z-index: 1;
  display: grid;
  gap: var(--space-3);
  width: min(100%, 360px);
  padding: 20px 18px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-modal);
  text-align: center;
}

.practice-summary__icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin: 0 auto;
  border-radius: 50%;
}

.practice-summary__icon--good {
  color: var(--emerald);
  background: var(--emerald-soft);
}

.practice-summary__icon--keep {
  color: var(--text-muted);
  background: var(--surface-soft);
}

.practice-summary__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
  color: var(--text-main);
}

.practice-summary__subtitle { margin: -4px 0 0; color: var(--text-muted); font-size: 13px; font-weight: 650; }
.practice-summary__badge { display: inline-flex; justify-self: center; padding: 5px 12px; border: 1px solid var(--primary-border); border-radius: var(--radius-full); background: var(--primary-soft); color: var(--primary-strong); font-size: 12px; font-weight: 800; }
.practice-summary__desc {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.65;
  color: var(--text-muted);
}

.practice-summary__score {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 14px;
  padding: 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-soft);
  text-align: left;
}
.practice-summary__score-copy { display: grid; gap: 10px; color: var(--text-secondary); font-size: 13px; }
.practice-summary__score-copy span { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding-bottom: 8px; border-bottom: 1px solid var(--line-soft); }
.practice-summary__score-copy span:last-child { padding-bottom: 0; border-bottom: 0; }
.practice-summary__score-copy svg { color: var(--text-muted); }
.practice-summary__ring {
  display: grid;
  width: 72px;
  height: 72px;
  place-items: center;
  align-content: center;
  border-radius: 50%;
  background: conic-gradient(var(--primary) var(--summary-score), var(--line-soft) 0);
  color: var(--text-main);
  box-shadow: inset 0 0 0 7px var(--surface);
}
.practice-summary__ring span { font-size: 15px; font-weight: 900; line-height: 1; }
.practice-summary__ring small { margin-top: 3px; color: var(--text-muted); font-size: 9px; font-weight: 750; }

.practice-summary__value--good {
  color: var(--emerald);
}

.practice-summary__value--bad {
  color: var(--rose);
}

.practice-summary__details { overflow: hidden; border: 1px solid var(--line-soft); border-radius: var(--radius-lg); background: var(--surface); }
.practice-summary__detail { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 12px; border-bottom: 1px solid var(--line-soft); color: var(--text-secondary); font-size: 13px; font-weight: 700; }
.practice-summary__detail:last-child { border-bottom: 0; }
.practice-summary__detail span { display: inline-flex; align-items: center; gap: 7px; }
.practice-summary__detail span svg { color: var(--text-muted); }
.practice-summary__detail strong { color: var(--text-main); font-size: 14px; }

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
  border-radius: var(--radius-full);
  font-size: var(--text-base);
  font-weight: 800;
  transition: box-shadow 0.17s ease-out, border-color 0.17s ease-out, background 0.17s ease-out;
}

.practice-primary-button {
  border: none;
  background: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-xs);
}

.practice-secondary-button {
  border: 1.5px solid var(--line-strong);
  background: var(--surface);
  color: var(--text-main);
}

.practice-primary-button:hover,
.practice-secondary-button:hover {
  box-shadow: var(--shadow-xs);
}

.practice-secondary-button:hover {
  border-color: var(--line-accent);
  background: var(--primary-soft);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.17s ease-out, transform 0.17s ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 420px) {
  .practice-summary__panel {
    padding: var(--space-5) var(--space-4);
  }

  .practice-summary__score { gap: 12px; padding: 10px; }
}
</style>
