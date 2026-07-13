<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { Award, ArrowRight, CheckCircle, Clock3, Play, RefreshCw, Target, XCircle } from "@lucide/vue";

const props = withDefaults(defineProps<{
  show?: boolean;
  answeredCount?: number;
  correctCount?: number;
  wrongCount?: number;
  accuracy?: number | null;
  durationSeconds?: number | null;
  courseName?: string;
  modeLabel?: string;
  completed?: boolean;
  canContinue?: boolean;
}>(), {
  show: false,
  answeredCount: 0,
  correctCount: 0,
  wrongCount: 0,
  accuracy: null,
  durationSeconds: null,
  courseName: "",
  modeLabel: "",
  completed: false,
  canContinue: true,
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

const emit = defineEmits<{
  end: [];
  continue: [];
  review: [];
}>();
const panelRef = ref<HTMLElement | null>(null);
let previouslyFocused: HTMLElement | null = null;
let documentListenersAttached = false;

const focusableSelector = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function focusableElements(): HTMLElement[] {
  if (!panelRef.value) return [];
  return Array.from(panelRef.value.querySelectorAll<HTMLElement>(focusableSelector));
}

function restoreFocus() {
  if (previouslyFocused instanceof HTMLElement && document.contains(previouslyFocused)) {
    previouslyFocused.focus();
  }
  previouslyFocused = null;
}

async function focusDialog() {
  await nextTick();
  const [first] = focusableElements();
  (first || panelRef.value)?.focus();
}

function focusInsideDialog() {
  const [first] = focusableElements();
  (first || panelRef.value)?.focus();
}

function handleDocumentFocusIn(event: { composedPath: () => unknown[] }) {
  const panel = panelRef.value;
  if (!props.show || !panel) return;
  if (event.composedPath().includes(panel)) return;
  focusInsideDialog();
}

function handleDocumentKeydown(event: KeyboardEvent) {
  if (!props.show) return;

  if (event.key === "Escape") {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!props.completed && props.canContinue) {
      emit("continue");
    }
    return;
  }

  if (event.key !== "Tab") return;
  const focusable = focusableElements();
  if (!focusable.length) {
    event.preventDefault();
    panelRef.value?.focus();
    return;
  }

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const activeElement = document.activeElement;
  const focusIsOutside = !panelRef.value?.contains(activeElement);
  if (event.shiftKey && (activeElement === first || focusIsOutside)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (activeElement === last || focusIsOutside)) {
    event.preventDefault();
    first.focus();
  }
}

function attachDocumentListeners() {
  if (documentListenersAttached) return;
  document.addEventListener("keydown", handleDocumentKeydown, true);
  document.addEventListener("focusin", handleDocumentFocusIn, true);
  documentListenersAttached = true;
}

function detachDocumentListeners() {
  if (!documentListenersAttached) return;
  document.removeEventListener("keydown", handleDocumentKeydown, true);
  document.removeEventListener("focusin", handleDocumentFocusIn, true);
  documentListenersAttached = false;
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      previouslyFocused = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
      attachDocumentListeners();
      void focusDialog();
    } else {
      detachDocumentListeners();
      restoreFocus();
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  detachDocumentListeners();
  restoreFocus();
});
</script>

<template>
  <transition name="fade">
    <div v-if="show" class="practice-summary">
      <div class="practice-summary__backdrop" aria-hidden="true"></div>
      <div
        ref="panelRef"
        class="practice-summary__panel"
        data-reference-page="practice-complete"
        role="dialog"
        aria-modal="true"
        aria-labelledby="practice-summary-title"
        aria-describedby="practice-summary-description"
        tabindex="-1"
      >
        <div
          class="practice-summary__icon"
          :class="answeredCount > 0 && accuracy !== null && accuracy >= 60
            ? 'practice-summary__icon--good'
            : 'practice-summary__icon--keep'"
        >
          <CheckCircle v-if="answeredCount > 0 && accuracy !== null && accuracy >= 60" :size="36" />
          <RefreshCw v-else :size="36" />
        </div>

        <p id="practice-summary-title" class="practice-summary__title">{{ completed ? "练习完成！" : "结束练习" }}</p>
        <p v-if="completed" class="practice-summary__subtitle">{{ courseName || "本题库" }} · {{ modeLabel || "练习" }}</p>
        <span v-if="completed" class="practice-summary__badge"><Award :size="14" />{{ performanceLabel }}</span>
        <p id="practice-summary-description" class="practice-summary__desc">{{ completed ? encouragement : answeredCount > 0 ? `本次练习已完成 ${answeredCount} 题，你可以继续练习或结束本次会话。` : "还没有完成题目，你可以继续练习或结束本次会话。" }}</p>

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
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.practice-summary__panel {
  position: relative;
  z-index: 1;
  display: grid;
  gap: var(--space-3);
  width: min(100%, 360px);
  max-height: calc(100dvh - max(32px, env(safe-area-inset-top)) - max(32px, env(safe-area-inset-bottom)));
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 24px 20px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  background: var(--glass-card);
  box-shadow: var(--shadow-modal), var(--glass-inner-highlight);
  text-align: center;
  backdrop-filter: blur(var(--glass-overlay-blur)) saturate(180%);
  -webkit-backdrop-filter: blur(var(--glass-overlay-blur)) saturate(180%);
  scrollbar-width: thin;
}

.practice-summary__icon {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  margin: 0 auto;
  border-radius: 50%;
}

.practice-summary__icon--good {
  color: #fff;
  background: var(--emerald);
  box-shadow: var(--shadow-primary);
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
.practice-summary__badge { display: inline-flex; align-items: center; gap: 5px; justify-self: center; padding: 5px 12px; border: 1px solid var(--primary-border); border-radius: var(--radius-full); background: var(--primary-soft); color: var(--primary-strong); font-size: 12px; font-weight: 800; }
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
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  box-shadow: var(--glass-inner-highlight);
  text-align: left;
}
.practice-summary__score-copy { display: grid; gap: 10px; color: var(--text-secondary); font-size: 13px; }
.practice-summary__score-copy span { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding-bottom: 8px; border-bottom: 1px solid var(--line-soft); }
.practice-summary__score-copy span:last-child { padding-bottom: 0; border-bottom: 0; }
.practice-summary__score-copy svg { color: var(--text-muted); }
.practice-summary__ring {
  display: grid;
  width: 84px;
  height: 84px;
  place-items: center;
  align-content: center;
  border-radius: 50%;
  background: conic-gradient(var(--primary) var(--summary-score), var(--line-soft) 0);
  color: var(--text-main);
  box-shadow: inset 0 0 0 8px var(--surface);
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

@media (max-width: 360px) {
  .practice-summary {
    padding: max(10px, env(safe-area-inset-top)) max(10px, env(safe-area-inset-right)) max(10px, env(safe-area-inset-bottom)) max(10px, env(safe-area-inset-left));
  }

  .practice-summary__panel {
    gap: 9px;
    padding: 16px 13px;
  }

  .practice-summary__icon {
    width: 58px;
    height: 58px;
  }

  .practice-summary__score {
    grid-template-columns: 76px minmax(0, 1fr);
  }

  .practice-summary__ring {
    width: 72px;
    height: 72px;
  }

  .practice-summary__detail {
    padding: 9px 10px;
  }
}
</style>
