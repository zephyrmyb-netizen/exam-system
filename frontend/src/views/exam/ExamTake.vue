<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronLeft, ChevronRight, LayoutGrid, Send, X } from "@lucide/vue";

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
const examId = computed(() => Number(route.params.examId));
const currentAnswer = computed(() => {
  const question = store.currentQuestion;
  return question ? store.answers[String(question.question_id)] || "" : "";
});

function answer(value: string) {
  if (!store.currentQuestion) return;
  store.setAnswer(store.currentQuestion.question_id, value);
}

async function submit() {
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

const shortcuts = useKeyboardShortcuts({
  next: () => store.next(),
  prev: () => store.prev(),
  selectOption,
});

useSwipe(pageRef, {
  onSwipeLeft: () => store.next(),
  onSwipeRight: () => store.prev(),
});

onMounted(() => {
  shortcuts.bind();
  store.startAttempt(examId.value);
});

onUnmounted(() => {
  shortcuts.unbind();
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
      <div class="exam-topbar">
        <div class="exam-topbar-row">
          <button class="exam-exit" type="button" aria-label="退出考试" @click="exitExam">
            <ArrowLeft :size="17" :stroke-width="2.5" />
            <span>退出</span>
          </button>
          <div class="exam-progress-copy">
            <span>{{ store.currentExam.title }}</span>
            <strong>{{ store.answeredCount }} / {{ store.totalQuestions }}</strong>
          </div>
          <button class="exam-answer-card-trigger" type="button" aria-label="打开答题卡" @click="showAnswerSheet = true">
            <LayoutGrid :size="18" :stroke-width="2.4" />
            <span>{{ store.answeredCount }}/{{ store.totalQuestions }}</span>
          </button>
          <span v-if="store.currentExam.time_limit" class="exam-timer">限时 {{ store.currentExam.time_limit }} 分钟</span>
        </div>
        <div class="progress-track"><i :style="{ width: `${store.progress}%` }"></i></div>
      </div>

      <ExamQuestionCard
        :question="store.currentQuestion"
        :answer="currentAnswer"
        :index="store.currentIndex"
        :total="store.totalQuestions"
        @answer="answer"
      />

      <div class="question-nav">
        <button type="button" :disabled="store.currentIndex === 0" @click="store.prev">
          <ChevronLeft :size="17" />
          上一题
        </button>
        <button type="button" :disabled="store.currentIndex >= store.totalQuestions - 1" @click="store.next">
          下一题
          <ChevronRight :size="17" />
        </button>
      </div>

      <button class="submit-button" type="button" :disabled="store.submitting" @click="submit">
        <Send :size="18" />
        {{ store.submitting ? "提交中..." : "交卷并查看成绩" }}
      </button>

      <Transition name="answer-sheet">
        <div v-if="showAnswerSheet" class="answer-sheet" data-exam-answer-sheet>
          <button class="answer-sheet__backdrop" type="button" aria-label="关闭答题卡" @click="showAnswerSheet = false"></button>
          <section class="answer-sheet__panel" role="dialog" aria-modal="true" aria-label="答题卡">
            <div class="answer-sheet__handle" aria-hidden="true"></div>
            <header class="answer-sheet__head">
              <div><strong>答题卡</strong><span>共 {{ store.totalQuestions }} 题 · 已答 {{ store.answeredCount }} 题</span></div>
              <button type="button" aria-label="关闭答题卡" @click="showAnswerSheet = false"><X :size="18" /></button>
            </header>
            <div class="answer-map">
              <button
                v-for="(question, index) in store.currentExam.questions"
                :key="question.question_id"
                type="button"
                :class="{ active: index === store.currentIndex, answered: store.answers[String(question.question_id)] }"
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
.exam-take-page { display: grid; gap: var(--space-4); }
.empty-panel {
  display: grid;
  gap: var(--space-4);
  place-items: center;
  padding: var(--space-8) var(--space-4);
  text-align: center;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 20px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.exam-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: 22px;
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  backdrop-filter: blur(16px);
}
.exam-topbar-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.exam-progress-copy { display: flex; min-width: 0; align-items: center; justify-content: flex-end; gap: var(--space-2); color: var(--text-muted); font-size: var(--text-sm); font-weight: 850; }
.exam-progress-copy span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.exam-exit { display: inline-flex; align-items: center; gap: 4px; min-width: 44px; min-height: 40px; padding: 0 8px; border: 0; border-radius: var(--radius-md); background: transparent; color: var(--text-main); font: inherit; font-size: var(--text-sm); font-weight: 800; }
.exam-exit:active { background: var(--surface-soft); }
.exam-topbar strong { color: var(--primary); }
.exam-timer { display: inline-flex; flex: 0 0 auto; padding: 5px 8px; border-radius: var(--radius-full); background: var(--amber-soft); color: var(--amber-strong); font-size: 11px; font-weight: 850; }
.exam-answer-card-trigger { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 3px; min-height: 36px; padding: 0 8px; border: 1px solid var(--primary-border); border-radius: 12px; background: var(--primary-soft); color: var(--primary-strong); font: inherit; font-size: 10px; font-weight: 850; }
.progress-track { height: 8px; overflow: hidden; border-radius: var(--radius-full); background: var(--surface-soft); }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--primary), var(--teal)); transition: width .2s ease; }
.question-nav {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
}
.question-nav button, .submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 48px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 900;
}
.question-nav button:disabled, .submit-button:disabled { opacity: .55; }
.answer-map {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
  gap: 8px;
}
.answer-map button {
  min-height: 44px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--surface);
  color: var(--text-muted);
  font: inherit;
  font-weight: 900;
}
.answer-map button.answered { color: var(--primary); background: var(--primary-soft); }
.answer-map button.active { border-color: var(--primary); color: #fff; background: var(--primary); }
.answer-sheet { position: fixed; inset: 0; z-index: 100; display: grid; align-items: end; }
.answer-sheet__backdrop { position: absolute; inset: 0; border: 0; background: rgba(15, 23, 42, .36); backdrop-filter: blur(4px); }
.answer-sheet__panel { position: relative; display: grid; gap: 14px; max-height: min(70dvh, 560px); padding: 10px 18px calc(22px + env(safe-area-inset-bottom)); overflow: auto; border: 1px solid var(--glass-border); border-radius: 24px 24px 0 0; background: var(--glass-card); box-shadow: var(--shadow-modal), var(--glass-inner-highlight); backdrop-filter: blur(24px) saturate(160%); }
.answer-sheet__handle { width: 36px; height: 4px; margin: 0 auto; border-radius: 999px; background: var(--line-strong); }
.answer-sheet__head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.answer-sheet__head div { display: grid; gap: 3px; }
.answer-sheet__head strong { font-size: 18px; }
.answer-sheet__head span { color: var(--text-muted); font-size: 12px; font-weight: 650; }
.answer-sheet__head button { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--line-soft); border-radius: 50%; background: var(--surface); color: var(--text-muted); }
.answer-sheet-enter-active, .answer-sheet-leave-active { transition: opacity var(--ease-out); }
.answer-sheet-enter-active .answer-sheet__panel, .answer-sheet-leave-active .answer-sheet__panel { transition: transform var(--ease-smooth); }
.answer-sheet-enter-from, .answer-sheet-leave-to { opacity: 0; }
.answer-sheet-enter-from .answer-sheet__panel, .answer-sheet-leave-to .answer-sheet__panel { transform: translateY(100%); }
.submit-button {
  border: 0;
  min-height: 56px;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
}
</style>
