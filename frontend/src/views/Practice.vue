<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, AlertTriangle, CheckCircle, Library, RefreshCw, Sparkles } from "@lucide/vue";
import PracticeActionBar from "../components/practice/PracticeActionBar.vue";
import PracticeChoiceOptions from "../components/practice/PracticeChoiceOptions.vue";
import PracticeQuestionStem from "../components/practice/PracticeQuestionStem.vue";
import PracticeResultPanel from "../components/practice/PracticeResultPanel.vue";
import PracticeStatsBar from "../components/practice/PracticeStatsBar.vue";
import PracticeSummaryModal from "../components/practice/PracticeSummaryModal.vue";
import PracticeTextAnswer from "../components/practice/PracticeTextAnswer.vue";
import PracticeTopBar from "../components/practice/PracticeTopBar.vue";
import { usePracticeSession } from "../composables/usePracticeSession";
import { typeLabel } from "../utils/question";
import { useConfirmDialog } from "../stores/confirmDialog";

const props = defineProps({
  courseId: { type: String, default: "" },
  courseName: { type: String, default: "" },
  mode: { type: String, default: "normal" },
  modeParam: { type: String, default: "" },
});

const emit = defineEmits(["end-practice"]);
const router = useRouter();
const confirmDialog = useConfirmDialog();
const showSummary = ref(false);

const {
  answerHint,
  answerOptions,
  accuracy,
  canSubmit,
  correctAnswerDisplay,
  currentAnswer,
  errorMessage,
  fetchRandomQuestion,
  handleTextKeydown,
  hasAnswerSelected,
  isTextQuestion,
  loading,
  question,
  result,
  selectedAnswer,
  selectedAnswers,
  sessionStats,
  setSingleAnswer,
  startSession,
  streakText,
  submitAnswer,
  submitting,
  textAnswer,
  toggleMultipleAnswer,
  updateTextAnswer,
  validationMessage,
} = usePracticeSession(props);

const canStartWithoutCourse = computed(() => props.mode === "wrong_review" || props.mode === "due_review");

const modeLabel = computed(() => {
  if (props.mode === "wrong_review") return "错题强化";
  if (props.mode === "due_review") return "到期复习";
  if (props.mode === "type_practice") return `题型 · ${typeLabel(props.modeParam)}`;
  if (props.mode === "chapter_practice") return `章节 · ${props.modeParam}`;
  return "";
});

const isWrongReviewEmpty = computed(() =>
  props.mode === "wrong_review"
    && !loading.value
    && !errorMessage.value
    && question.value === null
    && sessionStats.value.answeredCount === 0,
);

const isDueReviewEmpty = computed(() =>
  props.mode === "due_review"
    && !loading.value
    && !errorMessage.value
    && question.value === null
    && sessionStats.value.answeredCount === 0,
);

const isCourseEmpty = computed(() =>
  props.mode === "normal"
    && !props.courseId
    && !loading.value
    && !errorMessage.value
    && question.value === null
    && sessionStats.value.answeredCount === 0,
);

async function confirmAndSkip() {
  if (hasAnswerSelected.value) {
    const confirmed = await confirmDialog.confirm({
      title: "换下一题",
      message: "当前答案还没提交，确定换一题吗？",
      confirmText: "换题",
    });
    if (!confirmed) return;
  }
  fetchRandomQuestion();
}

function goBack() {
  if (props.courseId) {
    router.push(`/courses/${props.courseId}`);
  } else if (props.mode === "wrong_review" || props.mode === "due_review") {
    router.push({ name: "practice" });
  } else {
    router.push("/courses");
  }
}

function endPractice() {
  showSummary.value = true;
}

function handleEndPractice() {
  emit("end-practice");
}

function continuePractice() {
  showSummary.value = false;
}

onMounted(() => {
  if (props.courseId || canStartWithoutCourse.value) {
    startSession();
  }
});
</script>

<template>
  <section class="practice-page">
    <PracticeTopBar
      :course-name="props.courseName"
      :mode-label="modeLabel"
      @back="goBack"
      @end="endPractice"
    />

    <PracticeStatsBar
      v-if="question"
      :answered-count="sessionStats.answeredCount"
      :accuracy="accuracy"
      :streak-text="streakText"
    />

    <div v-if="!props.courseId && !canStartWithoutCourse && !question && !loading" class="state-block">
      <div class="state-icon"><Library :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">请先选择题库</p>
      <p class="state-hint">从你的题库中选择一个，进入专注练习模式。</p>
      <button class="primary-button" type="button" @click="goBack">去选择题库</button>
    </div>

    <div v-else-if="isWrongReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color:var(--emerald)" /></div>
      <p class="state-title">暂无错题</p>
      <p class="state-hint">继续练习积累后再来强化。</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" />
        <span>去练习</span>
      </button>
    </div>

    <div v-else-if="isDueReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color:var(--emerald)" /></div>
      <p class="state-title">暂无到期题目</p>
      <p class="state-hint">你已清空今日到期复习，继续保持。</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" />
        <span>去练习</span>
      </button>
    </div>

    <div v-else-if="isCourseEmpty" class="state-block">
      <div class="state-icon"><AlertTriangle :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">该题库暂时无题目</p>
      <p class="state-hint">先去导入或添加题目到当前题库。</p>
      <button class="primary-button" type="button" @click="router.push('/import')">
        <Sparkles :size="16" :stroke-width="2.5" />
        <span>去导入题目</span>
      </button>
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

    <div v-else-if="question" class="practice-content">
      <div class="practice-card-shell">
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

        <PracticeResultPanel
          v-if="result"
          :result="result"
          :current-answer="currentAnswer"
          :correct-answer-display="correctAnswerDisplay"
          :loading="loading"
          @next="fetchRandomQuestion"
        />
      </div>

      <PracticeActionBar
        :result="result"
        :can-submit="canSubmit"
        :submitting="submitting"
        :has-answer-selected="hasAnswerSelected"
        :answer-hint="answerHint"
        @submit="submitAnswer"
        @skip="confirmAndSkip"
      />
    </div>

    <PracticeSummaryModal
      :show="showSummary"
      :answered-count="sessionStats.answeredCount"
      :correct-count="sessionStats.correctCount"
      :wrong-count="sessionStats.wrongCount"
      :accuracy="accuracy"
      @end="handleEndPractice"
      @continue="continuePractice"
    />
  </section>
</template>

<style scoped>
.practice-page {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
}

.practice-content {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.practice-card-shell {
  display: grid;
  gap: 16px;
  min-width: 0;
  padding: 16px;
  border-radius: var(--radius-2xl);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 253, 0.96));
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(226, 232, 240, 0.88);
}

.practice-answer-section,
.practice-message-stack {
  display: grid;
  gap: 12px;
}

.state-block {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  padding: var(--space-10) var(--space-4);
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

.retry-btn,
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.practice-skeleton {
  width: 100%;
  padding: var(--space-4);
}

.practice-skeleton__line {
  height: 14px;
  margin-bottom: 12px;
  border-radius: 8px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
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
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
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
  background: #fef3c7;
  color: #92400e;
}

.msg-err {
  background: var(--rose-soft);
  color: var(--rose);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 420px) {
  .practice-card-shell {
    padding: 14px;
    border-radius: var(--radius-xl);
  }
}
</style>
