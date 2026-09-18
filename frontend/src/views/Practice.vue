<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  Library,
  RefreshCw,
  Sparkles,
} from "@lucide/vue";
import PracticeAnswerSheet from "../components/practice/PracticeAnswerSheet.vue";
import PracticeActionBar from "../components/practice/PracticeActionBar.vue";
import PracticeChoiceOptions from "../components/practice/PracticeChoiceOptions.vue";
import PracticeQuestionStem from "../components/practice/PracticeQuestionStem.vue";
import PracticeResultPanel from "../components/practice/PracticeResultPanel.vue";
import PracticeSummaryModal from "../components/practice/PracticeSummaryModal.vue";
import PracticeTextAnswer from "../components/practice/PracticeTextAnswer.vue";
import PracticeTopBar from "../components/practice/PracticeTopBar.vue";
import { usePracticeSession } from "../composables/usePracticeSession";
import { useSwipeNext } from "../composables/useSwipeNext";
import { typeLabel } from "../utils/question";

const props = defineProps({
  courseId: { type: String, default: "" },
  courseName: { type: String, default: "" },
  totalQuestions: { type: Number, default: 0 },
  mode: { type: String, default: "normal" },
  modeParam: { type: String, default: "" },
  initialQuestions: { type: Array, default: () => [] },
});

const emit = defineEmits(["end-practice"]);
const router = useRouter();
const showSummary = ref(false);
const showAnswerSheet = ref(false);
const practiceSurface = (ref < HTMLElement) | (null > null);

const {
  answerHint,
  answerOptions,
  accuracy,
  canSubmit,
  cancelPendingAdvance,
  correctAnswerDisplay,
  currentAnswer,
  errorMessage,
  fetchRandomQuestion,
  handleTextKeydown,
  hasAnswerSelected,
  isTextQuestion,
  isSeededSession,
  loading,
  phase,
  question,
  sessionQuestions,
  currentSessionQuestionIndex,
  result,
  selectedAnswer,
  selectedAnswers,
  sessionComplete,
  sessionStats,
  setSingleAnswer,
  startSession,
  submitAnswer,
  submitting,
  textAnswer,
  toggleMultipleAnswer,
  toggleCurrentQuestionMark,
  updateTextAnswer,
  validationMessage,
  jumpToSessionQuestion,
} = usePracticeSession(props);

// 全局右滑手势：仅在结果出现后（答错时显示解析，或答对短暂停留期）触发跳下一题。
// 答对时 composable 内 650ms 自动跳仍保留；右滑则让用户主动立即跳。
// fetchRandomQuestion 开头会 clearCorrectAutoNextTimer，不会重复触发。
const canSwipeNext = computed(
  () => !!result.value && !loading.value && !submitting.value && (phase.value === "correct" || phase.value === "wrong"),
);
const requiresManualSubmit = computed(() => isTextQuestion.value || question.value?.type === "multiple_choice");
useSwipeNext({
  onSwipe: () => {
    if (canSwipeNext.value) {
      void fetchRandomQuestion();
    }
  },
  enabled: canSwipeNext,
  target: practiceSurface,
});

const canStartWithoutCourse = computed(() => props.mode === "wrong_review" || props.mode === "due_review");

const modeLabel = computed(() => {
  if (props.mode === "wrong_review") return "错题强化";
  if (props.mode === "due_review") return "到期复习";
  if (props.mode === "type_practice") return `题型 · ${typeLabel(props.modeParam)}`;
  if (props.mode === "chapter_practice") return `章节 · ${props.modeParam}`;
  return "";
});

const isWrongReviewEmpty = computed(
  () =>
    props.mode === "wrong_review" &&
    !loading.value &&
    !errorMessage.value &&
    question.value === null &&
    sessionStats.value.answeredCount === 0,
);

const isDueReviewEmpty = computed(
  () =>
    props.mode === "due_review" &&
    !loading.value &&
    !errorMessage.value &&
    question.value === null &&
    sessionStats.value.answeredCount === 0,
);

const isCourseEmpty = computed(
  () =>
    props.mode === "normal" &&
    !!props.courseId &&
    sessionComplete.value &&
    !loading.value &&
    !errorMessage.value &&
    question.value === null &&
    sessionStats.value.answeredCount === 0,
);

const isCurrentQuestionMarked = computed(
  () => sessionQuestions.value[currentSessionQuestionIndex.value]?.marked ?? false,
);
const answerCardTotal = computed(() => sessionQuestions.value.length || props.totalQuestions);
const answerCardAnsweredCount = computed(
  () => sessionQuestions.value.filter((item) => item.answer.trim().length > 0).length,
);
const canGoPreviousQuestion = computed(() => currentSessionQuestionIndex.value > 0);
const canGoNextQuestion = computed(() => {
  const nextIndex = currentSessionQuestionIndex.value + 1;
  if (nextIndex < sessionQuestions.value.length) return true;
  return !!result.value && !loading.value && !submitting.value && !sessionComplete.value;
});
const currentSessionOrder = computed(
  () => sessionQuestions.value[currentSessionQuestionIndex.value]?.sessionOrder ?? 0,
);
const nextButtonLabel = computed(() => {
  const isLastSeededQuestion =
    isSeededSession.value && currentSessionQuestionIndex.value === sessionQuestions.value.length - 1;
  return isLastSeededQuestion ? "完成练习" : "下一题";
});

function openAnswerSheet() {
  showAnswerSheet.value = true;
}

function jumpFromAnswerSheet(index) {
  if (jumpToSessionQuestion(index)) showAnswerSheet.value = false;
}

function goPreviousQuestion() {
  if (canGoPreviousQuestion.value) jumpToSessionQuestion(currentSessionQuestionIndex.value - 1);
}

function goNextQuestion() {
  if (!canGoNextQuestion.value) return;
  const nextIndex = currentSessionQuestionIndex.value + 1;
  if (nextIndex < sessionQuestions.value.length) {
    jumpToSessionQuestion(nextIndex);
    return;
  }
  void fetchRandomQuestion();
}

function goBack() {
  cancelPendingAdvance?.();
  showAnswerSheet.value = false;
  if (props.courseId) {
    router.replace(`/courses/${props.courseId}`);
  } else if (props.mode === "wrong_review" || props.mode === "due_review") {
    router.replace({ name: "practice" });
  } else {
    router.replace("/courses");
  }
}

function endPractice() {
  cancelPendingAdvance?.();
  showAnswerSheet.value = false;
  if (sessionStats.value.startedAt && sessionStats.value.durationSeconds === null) {
    sessionStats.value.durationSeconds = Math.max(
      0,
      Math.round((Date.now() - sessionStats.value.startedAt.getTime()) / 1000),
    );
  }
  showSummary.value = true;
}

function handleEndPractice() {
  cancelPendingAdvance?.();
  showSummary.value = false;
  if (props.courseId) {
    emit("end-practice");
    return;
  }
  goBack();
}

function continuePractice() {
  showSummary.value = false;
}

function reviewWrongAnswers() {
  cancelPendingAdvance?.();
  showSummary.value = false;
  router.replace({ name: "wrongbook", query: { from: "practice" } });
}

onMounted(() => {
  if (props.courseId || canStartWithoutCourse.value) {
    startSession();
  }
});

onBeforeUnmount(() => cancelPendingAdvance?.());

watch(sessionComplete, (complete) => {
  showSummary.value = complete && sessionStats.value.answeredCount > 0;
});
</script>

<template>
  <section
    class="practice-page"
    data-reference-page="course-practice"
    :class="{ 'practice-page--with-action': requiresManualSubmit && question && !result }"
  >
    <PracticeTopBar
      :course-name="props.courseName"
      :mode-label="modeLabel"
      :answered-count="sessionStats.answeredCount"
      :accuracy="accuracy"
      :total-questions="props.totalQuestions"
      :session-order="isSeededSession ? currentSessionOrder : 0"
      :session-total="isSeededSession ? sessionQuestions.length : 0"
      :marked="isCurrentQuestionMarked"
      @back="goBack"
      @end="endPractice"
      @toggle-mark="toggleCurrentQuestionMark"
    />

    <div v-if="!props.courseId && !canStartWithoutCourse && !question && !loading" class="state-block">
      <div class="state-icon"><Library :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">请先选择题库</p>
      <p class="state-hint">从你的题库中选择一个，进入专注练习模式。</p>
      <button class="primary-button" type="button" @click="goBack">去选择题库</button>
    </div>

    <div v-else-if="isWrongReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color: var(--emerald)" /></div>
      <p class="state-title">暂无错题</p>
      <p class="state-hint">继续练习积累后再来强化。</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" />
        <span>去练习</span>
      </button>
    </div>

    <div v-else-if="isDueReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color: var(--emerald)" /></div>
      <p class="state-title">暂无到期题目</p>
      <p class="state-hint">你已清空今日到期复习，继续保持。</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" />
        <span>去练习</span>
      </button>
    </div>

    <div v-else-if="isCourseEmpty" class="state-block">
      <div class="state-icon"><AlertTriangle :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">当前题库暂无题目</p>
      <p class="state-hint">先去导入或添加题目到当前题库。</p>
      <div class="state-actions">
        <button class="ghost-button" type="button" @click="goBack">
          <Library :size="16" :stroke-width="2.5" />
          <span>返回题库</span>
        </button>
        <button
          class="primary-button"
          type="button"
          @click="router.replace({ name: 'import', query: { from: 'practice' } })"
        >
          <Sparkles :size="16" :stroke-width="2.5" />
          <span>去导入题目</span>
        </button>
      </div>
    </div>

    <div v-else-if="errorMessage && !question" class="state-block">
      <p class="error-msg">{{ errorMessage }}</p>
      <button class="ghost-button retry-btn" type="button" @click="fetchRandomQuestion">
        <RefreshCw :size="15" :stroke-width="2.5" />
        <span>重试</span>
      </button>
    </div>

    <div v-else-if="loading && !question" class="practice-skeleton">
      <div class="practice-skeleton__line practice-skeleton__line--short"></div>
      <div class="practice-skeleton__line practice-skeleton__line--long"></div>
      <div class="practice-skeleton__line practice-skeleton__line--medium"></div>
      <div class="practice-skeleton__grid">
        <div class="practice-skeleton__block"></div>
        <div class="practice-skeleton__block"></div>
      </div>
    </div>

    <div v-else-if="question" ref="practiceSurface" class="practice-content">
      <Transition name="question-fade">
        <div :key="question.id" class="practice-card-shell">
          <PracticeQuestionStem :question="question" />

          <div class="practice-answer-section">
            <PracticeChoiceOptions
              v-if="!isTextQuestion"
              :question-type="question.type"
              :options="answerOptions"
              :selected-answer="selectedAnswer"
              :selected-answers="selectedAnswers"
              :result="result"
              :correct-answer-display="correctAnswerDisplay"
              @pick-single="setSingleAnswer"
              @toggle-multiple="toggleMultipleAnswer"
            />

            <PracticeTextAnswer
              v-else
              :model-value="textAnswer"
              :disabled="!!result"
              @update:model-value="updateTextAnswer"
              @keydown="handleTextKeydown"
            />
          </div>

          <div v-if="validationMessage || errorMessage" class="practice-message-stack">
            <p v-if="validationMessage" class="msg msg-warn">{{ validationMessage }}</p>
            <p v-if="errorMessage" class="msg msg-err">{{ errorMessage }}</p>
          </div>

          <Transition name="result-fade">
            <PracticeResultPanel
              v-if="result"
              :result="result"
              :current-answer="currentAnswer"
              :correct-answer-display="correctAnswerDisplay"
              :loading="loading"
            />
          </Transition>
        </div>
      </Transition>

      <PracticeActionBar
        :result="result"
        :can-submit="canSubmit"
        :submitting="submitting"
        :has-answer-selected="hasAnswerSelected"
        :answer-hint="answerHint"
        :show-submit-button="requiresManualSubmit"
        @submit="submitAnswer"
      />
    </div>

    <nav v-if="question" class="practice-bottom-toolbar" aria-label="练习题目导航">
      <button
        class="practice-bottom-toolbar__button"
        type="button"
        :disabled="!canGoPreviousQuestion"
        @click="goPreviousQuestion"
      >
        <ChevronLeft :size="18" :stroke-width="2.5" />
        <span>上一题</span>
      </button>
      <button class="practice-bottom-toolbar__card" type="button" aria-label="答题卡" @click="openAnswerSheet">
        <LayoutGrid :size="18" :stroke-width="2.4" />
        <span>答题卡 {{ answerCardAnsweredCount }}/{{ answerCardTotal }}</span>
      </button>
      <button
        class="practice-bottom-toolbar__button practice-bottom-toolbar__button--next"
        type="button"
        :disabled="!canGoNextQuestion"
        @click="goNextQuestion"
      >
        <span>{{ nextButtonLabel }}</span>
        <ChevronRight :size="18" :stroke-width="2.5" />
      </button>
    </nav>

    <PracticeAnswerSheet
      v-model="showAnswerSheet"
      :items="sessionQuestions"
      :current-index="currentSessionQuestionIndex"
      :total-questions="answerCardTotal"
      @jump="jumpFromAnswerSheet"
    />

    <PracticeSummaryModal
      :show="showSummary"
      :answered-count="sessionStats.answeredCount"
      :correct-count="sessionStats.correctCount"
      :wrong-count="sessionStats.wrongCount"
      :accuracy="accuracy"
      :duration-seconds="sessionStats.durationSeconds"
      :course-name="props.courseName"
      :mode-label="modeLabel"
      :completed="sessionComplete"
      :can-continue="!sessionComplete"
      @end="handleEndPractice"
      @continue="continuePractice"
      @review="reviewWrongAnswers"
    />
  </section>
</template>

<style scoped>
.practice-page {
  position: relative;
  display: grid;
  align-content: start;
  gap: 12px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  padding-bottom: calc(88px + env(safe-area-inset-bottom));
  background: radial-gradient(circle at 88% 14%, rgba(16, 185, 129, 0.09), transparent 34%), var(--page-bg);
}

.practice-page--with-action {
  padding-bottom: calc(88px + env(safe-area-inset-bottom));
}

.practice-content {
  position: relative;
  display: grid;
  gap: 10px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.practice-card-shell {
  display: grid;
  gap: 16px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  margin: 0;
  padding: 18px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
  -webkit-backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
}

/* 高频答题只保留一次轻量交接，不再使用 out-in 留出空白帧。 */
.question-fade-enter-active {
  transition:
    opacity 0.18s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}

.question-fade-leave-active {
  position: absolute;
  inset: 0;
  width: 100%;
  pointer-events: none;
  transition:
    opacity 0.12s ease-out,
    transform 0.12s ease-out;
}

.question-fade-enter-from {
  opacity: 0;
  transform: translateX(8px);
}

.question-fade-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

/* ── 结果面板出现：短暂淡入轻移 ── */
.result-fade-enter-active,
.result-fade-leave-active {
  transition:
    opacity 0.16s ease-out,
    transform 0.16s ease-out;
}

.result-fade-enter-from,
.result-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.practice-answer-section,
.practice-message-stack {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.practice-bottom-toolbar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 45;
  display: grid;
  grid-template-columns: minmax(70px, 1fr) minmax(136px, 1.45fr) minmax(70px, 1fr);
  gap: 8px;
  width: min(100%, var(--shell-max));
  min-height: 68px;
  margin: 0 auto;
  padding: 8px 16px max(8px, env(safe-area-inset-bottom));
  border-top: 1px solid var(--glass-border);
  background: var(--glass-header);
  box-shadow:
    0 -8px 24px rgba(31, 41, 55, 0.08),
    var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
  -webkit-backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
}

.practice-bottom-toolbar__button,
.practice-bottom-toolbar__card {
  display: inline-flex;
  min-width: 0;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 8px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--surface-card);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.practice-bottom-toolbar__button:disabled {
  opacity: 0.42;
}

.practice-bottom-toolbar__card {
  border-color: var(--line-accent);
  background: var(--primary-soft);
  color: var(--primary-strong);
  box-shadow: var(--shadow-xs);
}

.state-block {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: var(--space-8) var(--space-4);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
  text-align: center;
}

.state-icon {
  color: var(--text-placeholder);
  margin-bottom: var(--space-1);
}

.state-title {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 800;
  color: var(--text-secondary);
}

.state-hint {
  margin: 0;
  max-width: 300px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-muted);
}

.error-msg {
  margin: 0;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: var(--rose-soft);
  color: var(--rose);
  font-size: 13px;
  font-weight: 700;
}

.state-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
}

.retry-btn,
.ghost-button,
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.practice-skeleton {
  width: 100%;
  margin: 0;
  padding: var(--space-4);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  background: var(--glass-card);
}

.practice-skeleton__line {
  height: 14px;
  margin-bottom: 12px;
  border-radius: 4px;
  background: var(--surface-soft);
}

.practice-skeleton__line--short {
  width: 30%;
}

.practice-skeleton__line--long {
  width: 90%;
}

.practice-skeleton__line--medium {
  width: 65%;
}

.practice-skeleton__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.practice-skeleton__block {
  height: 52px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.msg {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.msg-warn {
  background: var(--primary-soft);
  color: var(--text-secondary);
}

.msg-err {
  background: var(--rose-soft);
  color: var(--rose);
}

@media (max-width: 420px) {
  .practice-page {
    gap: 10px;
    padding-bottom: calc(84px + env(safe-area-inset-bottom));
  }

  .practice-page--with-action {
    padding-bottom: calc(84px + env(safe-area-inset-bottom));
  }

  .practice-card-shell {
    gap: 14px;
    padding: 16px;
  }

  .practice-answer-section,
  .practice-message-stack {
    gap: 6px;
  }

  .practice-bottom-toolbar {
    grid-template-columns: minmax(66px, 1fr) minmax(128px, 1.42fr) minmax(66px, 1fr);
    gap: 6px;
    padding-inline: 10px;
  }

  .practice-bottom-toolbar__button,
  .practice-bottom-toolbar__card {
    padding-inline: 6px;
    font-size: 12px;
  }
}
</style>
