<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronLeft, ChevronRight, Clock3, LayoutGrid, Send, X } from "@lucide/vue";

import ExamQuestionCard from "@/components/exam/ExamQuestionCard.vue";
import { useKeyboardShortcuts } from "@/composables/useKeyboardShortcuts";
import { useSwipe } from "@/composables/useSwipe";
import { useConfirmDialog } from "@/stores/confirmDialog";
import { useExamStore } from "@/stores/exam";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const confirmDialog = useConfirmDialog();
const pageRef = ref<HTMLElement | null>(null);
const showAnswerSheet = ref(false);
const timerExpiredSubmitting = ref(false);
const examId = computed(() => Number(route.params.examId));
const currentAnswer = computed(() => {
  const question = store.currentQuestion;
  return question ? store.answers[String(question.question_id)] || "" : "";
});

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

async function submit() {
  if (store.submitting) return;
  try {
    const result = await store.submitCurrentExam();
    router.replace({ name: "exam-result", params: { examId: result.exam_id } });
  } catch {
    // store.error 已由 store 设置，留在当前页让用户重试
  }
}

async function exitExam() {
  const confirmed = await confirmDialog.confirm({
    title: "退出考试",
    message: "退出后本次未交卷的答案不会保存。",
    confirmText: "退出",
    tone: "warning",
  });
  if (!confirmed) return;

  store.reset();
  router.replace({ name: "exam-detail", params: { examId: examId.value } });
}

function selectOption(index: number) {
  const question = store.currentQuestion;
  if (!question?.options) return;
  const key = Object.keys(question.options)[index];
  if (key) answer(key);
}

function jumpFromAnswerSheet(index: number) {
  store.jumpTo(index);
  showAnswerSheet.value = false;
}

async function syncTimer() {
  store.syncRemainingSeconds();
  if (store.remainingSeconds === 0 && !timerExpiredSubmitting.value) {
    timerExpiredSubmitting.value = true;
    await submit();
  }
}

const shortcuts = useKeyboardShortcuts({
  next: () => store.next(),
  prev: () => store.prev(),
  selectOption,
});

useSwipe(pageRef, {
  onSwipeLeft: () => store.next(),
  onSwipeRight: () => store.prev(),
});

let timerHandle: number | undefined;

onMounted(async () => {
  shortcuts.bind();
  await store.startAttempt(examId.value);
  await syncTimer();
  timerHandle = window.setInterval(syncTimer, 1000);
});

onUnmounted(() => {
  shortcuts.unbind();
  if (timerHandle) window.clearInterval(timerHandle);
  if (!store.result) store.reset();
});
</script>

<template>
  <section ref="pageRef" class="exam-take-page">
    <p v-if="store.loading" class="info-message">正在进入考试...</p>

    <div v-else-if="store.error" class="empty-panel">
      <p class="error-message">{{ store.error }}</p>
      <button type="button" class="back-btn" @click="router.replace({ name: 'exams' })">
        <ArrowLeft :size="16" /> 返回考试列表
      </button>
    </div>

    <template v-else-if="store.currentExam && store.currentQuestion">
      <header class="exam-topbar">
        <div class="exam-topbar__row">
          <button class="exam-exit" type="button" aria-label="退出考试" @click="exitExam">
            <ArrowLeft :size="18" :stroke-width="2.5" />
            <span>返回</span>
          </button>
          <div class="exam-heading">
            <strong>{{ store.currentExam.title }}</strong>
            <span>第 {{ store.currentIndex + 1 }} / {{ store.totalQuestions }} 题</span>
          </div>
          <button class="exam-answer-card-trigger" type="button" aria-label="打开答题卡" @click="showAnswerSheet = true">
            <LayoutGrid :size="18" :stroke-width="2.4" />
            <span>答题卡</span>
          </button>
        </div>
        <div class="exam-topbar__meta">
          <span>{{ store.answeredCount }} / {{ store.totalQuestions }} 已答</span>
          <span class="exam-timer" :class="{ urgent: store.remainingSeconds !== null && store.remainingSeconds <= 60 }" data-exam-countdown>
            <Clock3 :size="15" /> {{ formatRemaining(store.remainingSeconds) }}
          </span>
        </div>
        <div class="progress-track" aria-label="答题进度"><i :style="{ width: `${store.progress}%` }"></i></div>
      </header>

      <ExamQuestionCard
        :question="store.currentQuestion"
        :answer="currentAnswer"
        :index="store.currentIndex"
        :total="store.totalQuestions"
        @answer="answer"
      />

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

      <Transition name="answer-sheet">
        <div v-if="showAnswerSheet" class="answer-sheet" data-exam-answer-sheet>
          <button class="answer-sheet__backdrop" type="button" aria-label="关闭答题卡" @click="showAnswerSheet = false"></button>
          <section class="answer-sheet__panel" role="dialog" aria-modal="true" aria-label="答题卡">
            <div class="answer-sheet__handle" aria-hidden="true"></div>
            <header class="answer-sheet__head">
              <div><strong>答题卡</strong><span>已答 {{ store.answeredCount }} / {{ store.totalQuestions }} 题</span></div>
              <button type="button" aria-label="关闭答题卡" @click="showAnswerSheet = false"><X :size="18" /></button>
            </header>
            <div class="answer-map">
              <button
                v-for="(question, index) in store.currentExam.questions"
                :key="question.question_id"
                type="button"
                :class="{ active: index === store.currentIndex, answered: Boolean(store.answers[String(question.question_id)]?.trim()) }"
                @click="jumpFromAnswerSheet(index)"
              >
                {{ index + 1 }}
              </button>
            </div>
          </section>
        </div>
      </Transition>
    </template>
  </section>
</template>

<style scoped>
.exam-take-page { display: grid; gap: 16px; min-height: 100%; padding: 8px 0 calc(24px + env(safe-area-inset-bottom)); }
.empty-panel { display: grid; gap: 16px; place-items: center; padding: 48px 16px; text-align: center; }
.back-btn, .exam-exit, .exam-answer-card-trigger, .question-nav button, .submit-button, .answer-sheet__head button, .answer-map button { cursor: pointer; }
.back-btn { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 20px; border: 1px solid var(--line-soft); border-radius: var(--radius-full); background: var(--surface); color: var(--text-main); font: inherit; font-weight: 700; }
.exam-topbar { position: sticky; top: 0; z-index: 10; display: grid; gap: 12px; padding: 14px 16px; border: 1px solid var(--glass-border, var(--line-soft)); border-radius: 20px; background: color-mix(in srgb, var(--surface) 88%, transparent); box-shadow: var(--shadow-sm); backdrop-filter: blur(20px) saturate(160%); }
.exam-topbar__row, .exam-topbar__meta, .exam-heading, .exam-actions, .question-nav { display: flex; align-items: center; }
.exam-topbar__row, .exam-topbar__meta { justify-content: space-between; gap: 12px; }
.exam-heading { min-width: 0; flex: 1; flex-direction: column; align-items: flex-start; gap: 2px; }
.exam-heading strong { max-width: 100%; overflow: hidden; color: var(--text-main); font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.exam-heading span, .exam-topbar__meta { color: var(--text-muted); font-size: 12px; font-weight: 700; }
.exam-exit { display: inline-flex; align-items: center; gap: 4px; min-height: 40px; padding: 0 8px 0 0; border: 0; background: transparent; color: var(--text-main); font: inherit; font-weight: 800; }
.exam-answer-card-trigger { display: inline-flex; align-items: center; gap: 5px; min-height: 40px; padding: 0 10px; border: 1px solid var(--primary-border); border-radius: var(--radius-full); background: var(--primary-soft); color: var(--primary-strong); font: inherit; font-size: 12px; font-weight: 800; }
.exam-timer { display: inline-flex; align-items: center; gap: 5px; color: var(--primary-strong); font-variant-numeric: tabular-nums; }
.exam-timer.urgent { color: var(--state-error, var(--rose)); }
.progress-track { height: 7px; overflow: hidden; border-radius: var(--radius-full); background: var(--surface-soft); }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: var(--primary); transition: width var(--ease-out); }
.exam-actions { position: sticky; bottom: 0; z-index: 5; display: grid; gap: 10px; padding: 12px 0 calc(4px + env(safe-area-inset-bottom)); background: linear-gradient(180deg, transparent, var(--page-bg) 22%); }
.question-nav { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.question-nav button, .submit-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 48px; border-radius: var(--radius-full); font: inherit; font-weight: 800; }
.question-nav button { border: 1px solid var(--line-soft); background: var(--surface); color: var(--text-main); }
.question-nav button:disabled, .submit-button:disabled { cursor: not-allowed; opacity: .55; }
.submit-button { min-height: 52px; border: 0; background: var(--primary); color: #fff; box-shadow: var(--shadow-primary); }
.answer-sheet { position: fixed; inset: 0; z-index: 100; display: grid; align-items: end; }
.answer-sheet__backdrop { position: absolute; inset: 0; border: 0; background: rgba(15, 23, 42, .4); backdrop-filter: blur(4px); }
.answer-sheet__panel { position: relative; display: grid; gap: 16px; max-height: min(70dvh, 560px); padding: 10px 18px calc(22px + env(safe-area-inset-bottom)); overflow: auto; border: 1px solid var(--glass-border, var(--line-soft)); border-radius: 24px 24px 0 0; background: color-mix(in srgb, var(--surface) 86%, transparent); box-shadow: var(--shadow-modal); backdrop-filter: blur(24px) saturate(160%); }
.answer-sheet__handle { width: 36px; height: 4px; margin: 0 auto; border-radius: 999px; background: var(--line-strong); }
.answer-sheet__head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.answer-sheet__head div { display: grid; gap: 3px; }
.answer-sheet__head strong { font-size: 18px; }
.answer-sheet__head span { color: var(--text-muted); font-size: 12px; font-weight: 650; }
.answer-sheet__head button { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--line-soft); border-radius: 50%; background: var(--surface); color: var(--text-muted); }
.answer-map { display: grid; grid-template-columns: repeat(auto-fill, minmax(44px, 1fr)); gap: 8px; }
.answer-map button { min-height: 44px; border: 1px solid var(--line-soft); border-radius: 14px; background: var(--surface); color: var(--text-muted); font: inherit; font-weight: 900; }
.answer-map button.answered { border-color: var(--primary-border); color: var(--primary-strong); background: var(--primary-soft); }
.answer-map button.active { border-color: var(--primary); color: #fff; background: var(--primary); }
.answer-sheet-enter-active, .answer-sheet-leave-active { transition: opacity var(--ease-out); }
.answer-sheet-enter-active .answer-sheet__panel, .answer-sheet-leave-active .answer-sheet__panel { transition: transform var(--ease-smooth); }
.answer-sheet-enter-from, .answer-sheet-leave-to { opacity: 0; }
.answer-sheet-enter-from .answer-sheet__panel, .answer-sheet-leave-to .answer-sheet__panel { transform: translateY(100%); }
@media (min-width: 700px) {
  .exam-take-page { gap: 20px; padding-top: 16px; }
  .exam-actions { grid-template-columns: minmax(0, 1fr) 180px; align-items: center; }
}
</style>
