<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronLeft, ChevronRight, LayoutGrid, Send } from "@lucide/vue";

import ExamQuestionCard from "@/components/exam/ExamQuestionCard.vue";
import BottomSheet from "@/components/ui/BottomSheet.vue";
import { useKeyboardShortcuts } from "@/composables/useKeyboardShortcuts";
import { useSwipe } from "@/composables/useSwipe";
import { useConfirmDialog } from "@/stores/confirmDialog";
import { useExamStore } from "@/stores/exam";
import { toggleMultipleChoiceKey } from "@/utils/question";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const confirmDialog = useConfirmDialog();
const pageRef = ref<HTMLElement | null>(null);
const showAnswerSheet = ref(false);
const timerExpiredAutoAttempted = ref(false);
const examId = computed(() => Number(route.params.examId));
const currentAnswer = computed(() => {
  const question = store.currentQuestion;
  return question ? store.answers[String(question.question_id)] || "" : "";
});
const timerCircumference = 113.1;
const timerProgress = computed(() => {
  const seconds = store.remainingSeconds;
  const totalSeconds = store.currentExam?.time_limit ? store.currentExam.time_limit * 60 : null;
  if (seconds === null || !totalSeconds) return 0;
  return Math.min(1, Math.max(0, seconds / totalSeconds));
});
const timerDashOffset = computed(() => timerCircumference * (1 - timerProgress.value));
let componentActive = false;

function formatRemaining(seconds: number | null) {
  if (seconds === null) return "--:--";
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

function answer(value: string) {
  if (!store.currentQuestion) return;
  store.setAnswer(store.currentQuestion.question_id, value);
}

async function submit(): Promise<boolean> {
  if (store.submitting) return false;
  try {
    const result = await store.submitCurrentExam();
    const acceptedResult = store.result;
    if (!componentActive || !acceptedResult || acceptedResult.exam_id !== result.exam_id) return false;
    if (acceptedResult.submission_id !== undefined && result.submission_id !== undefined
      && acceptedResult.submission_id !== result.submission_id) return false;
    router.replace({ name: "exam-result", params: { examId: result.exam_id } });
    return true;
  } catch {
    // store.error 已由 store 设置，留在当前页让用户重试。
    return false;
  }
}

async function exitExam() {
  if (store.submitting) return;
  const confirmed = await confirmDialog.confirm({
    title: "退出考试",
    message: "退出后本次未交卷的答案不会保存。",
    confirmText: "退出",
    tone: "warning",
  });
  if (!confirmed || store.submitting) return;

  store.reset();
  router.replace({ name: "exam-detail", params: { examId: examId.value } });
}

function selectOption(index: number) {
  if (showAnswerSheet.value) return;
  const question = store.currentQuestion;
  if (!question?.options) return;
  const key = Object.keys(question.options)[index];
  if (!key) return;
  answer(question.question_type === "multiple_choice"
    ? toggleMultipleChoiceKey(store.answers[String(question.question_id)], key)
    : key);
}

function jumpFromAnswerSheet(index: number) {
  store.jumpTo(index);
  showAnswerSheet.value = false;
}

async function syncTimer() {
  store.syncRemainingSeconds();
  if (store.remainingSeconds === 0 && !timerExpiredAutoAttempted.value) {
    timerExpiredAutoAttempted.value = true;
    await submit();
  }
}

const shortcuts = useKeyboardShortcuts({
  next: () => {
    if (!showAnswerSheet.value) store.next();
  },
  prev: () => {
    if (!showAnswerSheet.value) store.prev();
  },
  selectOption,
});

useSwipe(pageRef, {
  onSwipeLeft: () => {
    if (!showAnswerSheet.value) store.next();
  },
  onSwipeRight: () => {
    if (!showAnswerSheet.value) store.prev();
  },
});

let timerHandle: number | undefined;

onMounted(async () => {
  componentActive = true;
  shortcuts.bind();
  try {
    await store.startAttempt(examId.value);
  } catch {
    return;
  }
  if (!componentActive) return;
  await syncTimer();
  if (!componentActive) return;
  timerHandle = window.setInterval(syncTimer, 1000);
});

onUnmounted(() => {
  componentActive = false;
  shortcuts.unbind();
  if (timerHandle) window.clearInterval(timerHandle);
  if (!store.result) store.reset();
});
</script>

<template>
  <section ref="pageRef" class="exam-take-page" data-reference-page="exam-take">
    <p v-if="store.loading" class="info-message">正在进入考试...</p>

    <div v-else-if="store.error" class="empty-panel">
      <p class="error-message">{{ store.error }}</p>
      <button type="button" class="back-btn" @click="router.replace({ name: 'exams' })">
        <ArrowLeft :size="16" /> 返回考试列表
      </button>
    </div>

    <template v-else-if="store.currentExam && store.currentQuestion">
      <header class="exam-topbar">
        <button
          class="exam-exit"
          type="button"
          aria-label="退出考试"
          :disabled="store.submitting"
          :aria-disabled="store.submitting"
          @click="exitExam"
        >
          <ArrowLeft :size="20" :stroke-width="2.25" />
        </button>
        <div class="exam-heading">
          <strong>{{ store.currentExam.title }}</strong>
          <span>第 {{ store.currentIndex + 1 }} 题 / 共 {{ store.totalQuestions }} 题</span>
        </div>
        <button class="exam-answer-card-trigger" type="button" aria-label="打开答题卡" @click="showAnswerSheet = true">
          <LayoutGrid :size="20" :stroke-width="2.25" />
          <span>{{ store.answeredCount }}/{{ store.totalQuestions }}</span>
        </button>
        <div
          class="exam-timer-ring"
          :class="{ urgent: store.remainingSeconds !== null && store.remainingSeconds <= 60 }"
          data-exam-countdown
          :aria-label="`剩余时间 ${formatRemaining(store.remainingSeconds)}`"
        >
          <svg width="44" height="44" viewBox="0 0 44 44" aria-hidden="true">
            <circle class="exam-timer-ring__track" cx="22" cy="22" r="18" />
            <circle
              class="exam-timer-ring__progress"
              cx="22"
              cy="22"
              r="18"
              :stroke-dasharray="timerCircumference"
              :stroke-dashoffset="timerDashOffset"
            />
          </svg>
          <span>{{ formatRemaining(store.remainingSeconds) }}</span>
        </div>
      </header>

      <ExamQuestionCard
        :question="store.currentQuestion"
        :answer="currentAnswer"
        :index="store.currentIndex"
        :total="store.totalQuestions"
        @answer="answer"
      />

      <div v-if="store.submissionError" class="submit-error-banner" role="alert" data-exam-submit-error>
        <p>{{ store.submissionError }}</p>
        <button type="button" :disabled="store.submitting" data-exam-submit-retry @click="submit">
          {{ store.submitting ? "重试中..." : "重新交卷" }}
        </button>
      </div>

      <footer class="exam-actions">
        <div class="question-nav">
          <button type="button" :disabled="store.currentIndex === 0" @click="store.prev">
            <ChevronLeft :size="18" /> 上一题
          </button>
          <button type="button" :disabled="store.currentIndex >= store.totalQuestions - 1" @click="store.next">
            下一题 <ChevronRight :size="18" />
          </button>
        </div>
        <button class="submit-button" type="button" :disabled="store.submitting" @click="submit">
          <Send :size="18" />
          {{ store.submitting ? "提交中..." : "交卷" }}
        </button>
      </footer>

      <BottomSheet v-model="showAnswerSheet" title="答题卡">
        <div data-exam-answer-sheet>
          <div class="answer-sheet__summary">
            <span>共 {{ store.totalQuestions }} 题</span>
            <strong>完成 {{ store.progress }}%</strong>
          </div>
          <div class="answer-sheet__progress" aria-hidden="true"><i :style="{ width: `${store.progress}%` }"></i></div>
          <div class="answer-map">
            <button
              v-for="(question, index) in store.currentExam.questions"
              :key="question.question_id"
              type="button"
              :data-question-id="question.question_id"
              :class="{ active: index === store.currentIndex, answered: Boolean(store.answers[String(question.question_id)]?.trim()) }"
              @click="jumpFromAnswerSheet(index)"
            >
              {{ index + 1 }}
            </button>
          </div>
          <div class="answer-sheet__legend">
            <span><i class="answered"></i>已答 {{ store.answeredCount }}</span>
            <span><i class="current"></i>当前</span>
            <span><i></i>未答 {{ Math.max(store.totalQuestions - store.answeredCount, 0) }}</span>
          </div>
        </div>
      </BottomSheet>
    </template>

    <article v-else-if="store.currentExam" class="empty-panel" data-exam-empty>
      <LayoutGrid :size="36" />
      <h1>暂无可作答题目</h1>
      <p>这份试卷当前没有返回题目，请返回考试详情后重试。</p>
      <button type="button" class="back-btn" @click="router.replace({ name: 'exam-detail', params: { examId } })">
        <ArrowLeft :size="16" /> 返回考试详情
      </button>
    </article>
  </section>
</template>

<style scoped>
.exam-take-page {
  display: grid;
  gap: var(--space-4);
  min-height: 100%;
  padding: 0 var(--space-4) calc(92px + var(--safe-area-bottom));
}

.empty-panel {
  display: grid;
  gap: var(--space-3);
  place-items: center;
  padding: 56px var(--space-4);
  color: var(--text-muted);
  text-align: center;
}

.empty-panel h1,
.empty-panel p {
  margin: 0;
}

.empty-panel h1 {
  color: var(--text-main);
  font-size: var(--text-xl);
}

.back-btn,
.exam-exit,
.exam-answer-card-trigger,
.question-nav button,
.submit-button,
.answer-map button {
  cursor: pointer;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 20px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-full);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 700;
}

.submit-error-banner {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--state-error-border);
  border-radius: var(--radius-md);
  background: var(--state-error-soft);
  color: var(--state-error);
}

.submit-error-banner p {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1.45;
}

.submit-error-banner button {
  min-height: 38px;
  flex: 0 0 auto;
  padding: 0 14px;
  border: 1px solid currentColor;
  border-radius: var(--radius-full);
  background: transparent;
  color: inherit;
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 800;
}

.submit-error-banner button:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.exam-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 68px;
  margin: 0 calc(-1 * var(--space-4));
  padding: max(10px, var(--safe-area-top)) 12px 10px;
  border-bottom: 1px solid var(--glass-border);
  background: var(--glass-header);
  box-shadow: var(--shadow-xs);
  backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
  -webkit-backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
}

.exam-heading {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-align: center;
}

.exam-heading strong {
  max-width: 100%;
  overflow: hidden;
  color: var(--text-main);
  font-size: var(--text-md);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exam-heading span {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.exam-exit,
.exam-answer-card-trigger {
  display: grid;
  position: relative;
  place-items: center;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
}

.exam-answer-card-trigger span {
  position: absolute;
  right: -3px;
  bottom: -1px;
  display: grid;
  place-items: center;
  min-width: 24px;
  height: 16px;
  padding: 0 4px;
  border-radius: var(--radius-full);
  background: var(--primary);
  box-shadow: 0 0 0 2px var(--surface);
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  line-height: 1;
}

.exam-exit:active,
.exam-answer-card-trigger:active,
.question-nav button:active,
.submit-button:active,
.answer-map button:active {
  transform: scale(.94);
}

.exam-exit:disabled {
  cursor: not-allowed;
  opacity: .48;
}

.exam-timer-ring {
  display: grid;
  position: relative;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  place-items: center;
  color: var(--primary-strong);
}

.exam-timer-ring svg {
  position: absolute;
  inset: 0;
  transform: rotate(-90deg);
}

.exam-timer-ring circle {
  fill: none;
  stroke-width: 3;
}

.exam-timer-ring__track {
  stroke: var(--line-soft);
}

.exam-timer-ring__progress {
  stroke: currentColor;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s linear;
}

.exam-timer-ring span {
  position: relative;
  z-index: 1;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.exam-timer-ring.urgent {
  color: var(--state-error);
  animation: exam-tick 2.4s ease-in-out infinite;
}

.exam-actions {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 50%;
  z-index: 30;
  display: grid;
  width: min(100%, var(--shell-max));
  grid-template-columns: minmax(0, 1fr) minmax(96px, .72fr);
  gap: 10px;
  padding: 12px max(12px, var(--space-4)) max(12px, var(--safe-area-bottom));
  border-top: 1px solid var(--glass-border);
  background: var(--glass-header);
  box-shadow: 0 -2px 12px rgba(15, 23, 42, .06);
  backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
  -webkit-backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
  transform: translateX(-50%);
}

.question-nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.question-nav button,
.submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
  min-height: 48px;
  border-radius: var(--radius-full);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 800;
  transition: transform var(--ease-spring), opacity var(--ease-out);
}

.question-nav button {
  border: 1px solid var(--line-soft);
  background: var(--surface-soft);
  color: var(--text-secondary);
}

.question-nav button:disabled,
.submit-button:disabled {
  cursor: not-allowed;
  opacity: .48;
}

.submit-button {
  border: 0;
  background: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.answer-sheet__summary,
.answer-sheet__legend {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.answer-sheet__summary strong {
  color: var(--primary-strong);
}

.answer-sheet__progress {
  height: 4px;
  margin: var(--space-2) 0 var(--space-4);
  overflow: hidden;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
}

.answer-sheet__progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
}

.answer-map {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.answer-map button {
  aspect-ratio: 1;
  min-width: 0;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  color: var(--text-muted);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  transition: transform var(--ease-spring), background var(--ease-out), border-color var(--ease-out);
}

.answer-map button.answered {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
}

.answer-map button.active {
  border-color: var(--primary);
  background: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
  color: #fff;
}

.answer-sheet__legend {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: var(--space-4);
}

.answer-sheet__legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.answer-sheet__legend i {
  width: 10px;
  height: 10px;
  border: 1px solid var(--line-soft);
  border-radius: 3px;
  background: var(--surface-soft);
}

.answer-sheet__legend i.answered,
.answer-sheet__legend i.current {
  border-color: var(--primary);
  background: var(--primary);
}

.answer-sheet__legend i.current {
  box-shadow: 0 0 0 2px var(--primary-glow);
}

@keyframes exam-tick {
  50% { transform: scale(1.08); opacity: .82; }
}

@media (max-width: 340px) {
  .exam-topbar { gap: 4px; padding-inline: 8px; }
  .exam-heading strong { font-size: var(--text-sm); }
  .exam-actions { grid-template-columns: minmax(0, 1fr) 92px; padding-inline: 8px; }
  .question-nav button { font-size: var(--text-xs); }
}
</style>
