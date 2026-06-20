<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getErrorMessage } from "../api/request";
import { getRandomPracticeQuestion, submitPracticeAnswer, getReviewWrongQuestion, getReviewDueQuestion } from "../api/practice";
import { typeLabel, formatOptions } from "../utils/question";
import {
  Send, ArrowRight, CheckCircle, XCircle, BookMarked,
  Library, Shuffle, RefreshCw, AlertTriangle,
  ChevronLeft, Sparkles, X, Play,
} from "@lucide/vue";

const props = defineProps({
  courseId: { type: String, default: "" },
  courseName: { type: String, default: "" },
  mode: { type: String, default: "normal" },
  modeParam: { type: String, default: "" },
});

const emit = defineEmits(["end-practice"]);
const router = useRouter();

const showSummary = ref(false);

// ── Question state ──
const question = ref(null);
const selectedAnswer = ref("");
const selectedAnswers = ref([]);
const textAnswer = ref("");
const result = ref(null);
const loading = ref(false);
const submitting = ref(false);
const errorMessage = ref("");
const validationMessage = ref("");

// ── Session state (in-memory) ──
const sessionStats = ref({
  answeredCount: 0,
  correctCount: 0,
  wrongCount: 0,
  streak: 0,
  startedAt: null,
});

const accuracy = computed(() => {
  const answered = sessionStats.value.answeredCount;
  if (answered === 0) return null;
  return Math.round((sessionStats.value.correctCount / answered) * 100);
});

const streakText = computed(() => {
  const s = sessionStats.value.streak;
  if (s === 0) return "0";
  if (s >= 5) return `🔥 ${s}`;
  if (s >= 3) return `⭐ ${s}`;
  return `✅ ${s}`;
});

const modeLabel = computed(() => {
  if (props.mode === "wrong_review") return "错题强化";
  if (props.mode === "due_review") return "到期复习";
  if (props.mode === "type_practice") return `题型·${typeLabel(props.modeParam)}`;
  if (props.mode === "chapter_practice") return `章节·${props.modeParam}`;
  return "";
});

const isTextQuestion = computed(() =>
  ["fill_blank", "short_answer"].includes(question.value?.type)
);

const currentAnswer = computed(() => {
  if (!question.value) return "";
  if (question.value.type === "multiple_choice") {
    return [...selectedAnswers.value].sort().join(",");
  }
  if (isTextQuestion.value) return textAnswer.value.trim();
  return selectedAnswer.value;
});

const answerOptions = computed(() => {
  if (!question.value) return [];
  if (question.value.type === "true_false") {
    return [
      { key: "正确", value: "正确" },
      { key: "错误", value: "错误" },
    ];
  }
  const options = formatOptions(question.value.options);
  return options.length > 0 ? options : ["A", "B", "C", "D"].map(k => ({ key: k, value: k }));
});

const canStartWithoutCourse = computed(() => props.mode === "wrong_review" || props.mode === "due_review");

const isWrongReviewEmpty = computed(() =>
  props.mode === "wrong_review" && !loading.value && !errorMessage.value && question.value === null && sessionStats.value.answeredCount === 0
);

const isDueReviewEmpty = computed(() =>
  props.mode === "due_review" && !loading.value && !errorMessage.value && question.value === null && sessionStats.value.answeredCount === 0
);

const isCourseEmpty = computed(() =>
  props.mode === "normal" && !props.courseId && !loading.value && !errorMessage.value && question.value === null && sessionStats.value.answeredCount === 0
);

// ── State helpers ──

const hasAnswerSelected = computed(() => {
  if (!question.value) return false;
  if (question.value.type === "multiple_choice") return selectedAnswers.value.length > 0;
  if (isTextQuestion.value) return textAnswer.value.trim().length > 0;
  return selectedAnswer.value.length > 0;
});

const canSubmit = computed(() => hasAnswerSelected.value && !submitting.value);

const answerHint = computed(() => {
  if (!question.value) return "";
  const t = question.value.type;
  if (t === "multiple_choice") return "请选择所有正确选项";
  if (t === "single_choice") return "请选择一个答案";
  if (t === "true_false") return "请选择正确或错误";
  if (isTextQuestion.value) return "请输入答案";
  return "";
});

function resetAnswerState() {
  selectedAnswer.value = "";
  selectedAnswers.value = [];
  textAnswer.value = "";
  result.value = null;
  validationMessage.value = "";
}

async function fetchRandomQuestion() {
  loading.value = true;
  errorMessage.value = "";
  validationMessage.value = "";
  resetAnswerState();
  try {
    const params = {};
    if (props.courseId) params.course_id = props.courseId;
    let data;
    if (props.mode === "wrong_review") {
      data = await getReviewWrongQuestion(params);
    } else if (props.mode === "due_review") {
      data = await getReviewDueQuestion(params);
    } else {
      if (props.mode === "type_practice") params.type = props.modeParam;
      if (props.mode === "chapter_practice") params.chapter = props.modeParam;
      data = await getRandomPracticeQuestion(params);
    }
    question.value = data;
  } catch (error) {
    question.value = null;
    errorMessage.value = getErrorMessage(error, "获取题目失败");
  } finally {
    loading.value = false;
  }
}

function toggleMultipleAnswer(key) {
  if (result.value) return;
  if (selectedAnswers.value.includes(key)) {
    selectedAnswers.value = selectedAnswers.value.filter(i => i !== key);
  } else {
    selectedAnswers.value = [...selectedAnswers.value, key];
  }
  validationMessage.value = "";
}

async function submitAnswer() {
  if (!question.value) return;
  if (question.value.type === "multiple_choice" && selectedAnswers.value.length === 0) {
    validationMessage.value = "请至少选择一个选项。";
    return;
  }
  if (!currentAnswer.value) {
    validationMessage.value = isTextQuestion.value ? "请先填写你的答案。" : "请先选择一个选项。";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  validationMessage.value = "";
  try {
    const data = await submitPracticeAnswer({
      question_id: question.value.id,
      user_answer: currentAnswer.value,
    });
    result.value = data;
    sessionStats.value.answeredCount++;
    if (data.is_correct) {
      sessionStats.value.correctCount++;
      sessionStats.value.streak++;
    } else {
      sessionStats.value.wrongCount++;
      sessionStats.value.streak = 0;
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "提交答案失败");
  } finally {
    submitting.value = false;
  }
}

function getBtnClass(optionKey) {
  if (!result.value) return "";
  const isSelected = question.value.type === "multiple_choice"
    ? selectedAnswers.value.includes(optionKey)
    : selectedAnswer.value === optionKey;
  const correctKey = question.value.type === "true_false"
    ? (result.value.correct_answer === "True" ? "正确" : result.value.correct_answer === "False" ? "错误" : result.value.correct_answer)
    : result.value.correct_answer;
  if (optionKey === correctKey) return "btn-correct";
  if (isSelected && optionKey !== correctKey) return "btn-wrong";
  if (isSelected) return "btn-selected";
  return "";
}

function handleTextKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!result.value && !submitting.value) submitAnswer();
  }
}

function confirmAndSkip() {
  if (hasAnswerSelected.value) {
    if (!window.confirm("当前答案还没提交，确定换一题吗？")) return;
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

function startSession() {
  sessionStats.value = { answeredCount: 0, correctCount: 0, wrongCount: 0, streak: 0, startedAt: new Date() };
  fetchRandomQuestion();
}

onMounted(() => {
  if (props.courseId || canStartWithoutCourse.value) startSession();
});
</script>

<template>
  <section class="practice-page">
    <!-- ── Top Bar ── -->
    <div class="topbar">
      <button class="topbar-back" type="button" @click="goBack" aria-label="返回">
        <ChevronLeft :size="18" :stroke-width="2.5" />
      </button>
      <div class="topbar-center">
        <span class="topbar-course">{{ props.courseName || modeLabel || "练习" }}</span>
        <span v-if="modeLabel && props.mode !== 'normal'" class="topbar-mode">{{ modeLabel }}</span>
      </div>
      <button class="topbar-end" type="button" @click="endPractice" aria-label="结束练习">
        <X :size="16" :stroke-width="2.5" />
        <span class="end-label">结束</span>
      </button>
    </div>

    <!-- Stats chips (second row, only when question is loaded) -->
    <div v-if="question" class="stats-chips">
      <span class="chip">已答 {{ sessionStats.answeredCount }}</span>
      <span class="chip-sep">·</span>
      <span class="chip" :class="accuracy !== null && accuracy >= 70 ? 'chip-green' : accuracy !== null && accuracy < 40 ? 'chip-rose' : ''">
        正确率 {{ accuracy !== null ? accuracy + '%' : '--' }}
      </span>
      <span class="chip-sep">·</span>
      <span class="chip chip-streak">{{ streakText }}</span>
    </div>

    <!-- ── Loading / Empty / Error states ── -->

    <!-- No course selected (only for normal mode) -->
    <div v-if="!props.courseId && !canStartWithoutCourse && !question && !loading" class="state-block">
      <div class="state-icon"><Library :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">请先选择课程</p>
      <p class="state-hint">从你的课程中选择一门，进入专注练习模式。</p>
      <button class="primary-button" type="button" @click="goBack">去选择课程</button>
    </div>

    <!-- Wrong review empty -->
    <div v-else-if="isWrongReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color:var(--emerald)" /></div>
      <p class="state-title">暂无错题</p>
      <p class="state-hint">继续练习积累后再来强化。</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" style="margin-right:4px" />
        去练习
      </button>
    </div>

    <!-- Due review empty -->
    <div v-else-if="isDueReviewEmpty" class="state-block">
      <div class="state-icon"><CheckCircle :size="44" :stroke-width="1.5" style="color:var(--emerald)" /></div>
      <p class="state-title">暂无到期题目</p>
      <p class="state-hint">你已清空今日到期复习，继续保持！</p>
      <button class="primary-button" type="button" @click="goBack">
        <ArrowRight :size="16" :stroke-width="2.5" style="margin-right:4px" />
        去练习
      </button>
    </div>

    <!-- Course empty -->
    <div v-else-if="isCourseEmpty" class="state-block">
      <div class="state-icon"><AlertTriangle :size="44" :stroke-width="1.5" /></div>
      <p class="state-title">该课程暂无题目</p>
      <p class="state-hint">先去导入或添加题目到当前课程。</p>
      <button class="primary-button" type="button" @click="router.push('/import')">
        <Sparkles :size="16" :stroke-width="2.5" style="margin-right:4px" />
        去导入题目
      </button>
    </div>

    <!-- Error + retry -->
    <div v-else-if="errorMessage && !question" class="state-block">
      <p class="error-msg">{{ errorMessage }}</p>
      <button class="ghost-button retry-btn" type="button" @click="fetchRandomQuestion">
        <RefreshCw :size="15" :stroke-width="2.5" style="margin-right:4px" />
        重试
      </button>
    </div>

    <!-- Skeleton -->
    <div v-else-if="loading && !question" class="skeleton-wrap">
      <div class="sk-line sk-line--short"></div>
      <div class="sk-line sk-line--long"></div>
      <div class="sk-line sk-line--medium"></div>
      <div class="sk-grid">
        <div class="sk-block"></div>
        <div class="sk-block"></div>
      </div>
    </div>

    <!-- ── Question ── -->
    <div v-else-if="question" class="question-area">
      <!-- Main stem -->
      <div class="stem">
        <div class="stem-meta">
          <span class="stem-tag">{{ typeLabel(question.type) }}</span>
          <span class="stem-tag">{{ question.subject }}</span>
          <span class="stem-tag">{{ question.chapter }}</span>
          <span v-if="question.type === 'multiple_choice'" class="stem-hint">多选题，请选择所有正确选项</span>
        </div>
        <h2 class="stem-text">{{ question.question }}</h2>
      </div>

      <!-- ── Multi-choice ── -->
      <div v-if="question.type === 'multiple_choice'" class="opts">
        <button
          v-for="opt in answerOptions" :key="opt.key"
          class="opt-card"
          :class="[getBtnClass(opt.key), { selected: selectedAnswers.includes(opt.key) && !result }]"
          type="button" :disabled="!!result"
          @click="toggleMultipleAnswer(opt.key)"
        >
          <span class="opt-chk">{{ selectedAnswers.includes(opt.key) ? '✓' : '' }}</span>
          <span class="opt-key" :class="{ 'opt-key--active': selectedAnswers.includes(opt.key) && !result }">{{ opt.key }}</span>
          <span class="opt-val">{{ opt.value }}</span>
        </button>
      </div>

      <!-- ── Single choice ── -->
      <div v-else-if="question.type === 'single_choice'" class="opts">
        <button
          v-for="opt in answerOptions" :key="opt.key"
          class="opt-card"
          :class="[getBtnClass(opt.key), { selected: selectedAnswer === opt.key && !result }]"
          type="button" :disabled="!!result"
          @click="selectedAnswer = opt.key"
        >
          <span class="opt-key" :class="{ 'opt-key--active': selectedAnswer === opt.key && !result }">{{ opt.key }}</span>
          <span class="opt-val">{{ opt.value }}</span>
        </button>
      </div>

      <!-- ── True / False ── -->
      <div v-else-if="question.type === 'true_false'" class="tf">
        <button
          class="tf-btn tf-true"
          :class="[getBtnClass('正确'), { selected: selectedAnswer === '正确' && !result }]"
          type="button" :disabled="!!result"
          @click="selectedAnswer = '正确'"
        >
          <CheckCircle :size="22" :stroke-width="2.5" />
          <span>正确</span>
        </button>
        <button
          class="tf-btn tf-false"
          :class="[getBtnClass('错误'), { selected: selectedAnswer === '错误' && !result }]"
          type="button" :disabled="!!result"
          @click="selectedAnswer = '错误'"
        >
          <XCircle :size="22" :stroke-width="2.5" />
          <span>错误</span>
        </button>
      </div>

      <!-- ── Text input ── -->
      <div v-else class="text-area">
        <textarea
          v-model="textAnswer" class="q-input"
          :disabled="!!result"
          placeholder="在这里输入你的答案"
          @keydown="handleTextKeydown"
        />
        <p class="text-hint">Enter 提交 · Shift+Enter 换行</p>
      </div>

      <!-- Validation -->
      <p v-if="validationMessage" class="msg msg-warn">{{ validationMessage }}</p>
      <p v-if="errorMessage" class="msg msg-err">{{ errorMessage }}</p>

      <!-- Submit hint (when disabled) -->
      <p v-if="!result && !hasAnswerSelected && !submitting" class="submit-hint">{{ answerHint }}</p>

      <!-- ── Submit button ── -->
      <button
        v-if="!result"
        class="btn-action"
        type="button" :disabled="!canSubmit"
        @click="submitAnswer"
      >
        <Send :size="17" :stroke-width="2.5" style="margin-right:6px" />
        {{ submitting ? "提交中..." : "提交答案" }}
      </button>

      <!-- ── "不会，换一题" — always visible before submission ── -->
      <button
        v-if="!result"
        class="skip-link"
        type="button"
        @click="confirmAndSkip"
      >
        不会，换一题
        <Shuffle :size="13" :stroke-width="2.5" style="margin-left:4px" />
      </button>

      <!-- ── Result feedback ── -->
      <transition name="fade">
        <div v-if="result" class="result" :class="result.is_correct ? 'r-correct' : 'r-wrong'">
          <div class="r-head">
            <CheckCircle v-if="result.is_correct" :size="22" class="r-icon" />
            <XCircle v-else :size="22" class="r-icon" />
            <span class="r-title">{{ result.is_correct ? "回答正确" : "回答错误" }}</span>
          </div>
          <div class="r-detail">
            <div class="r-line"><span class="r-lbl">你的答案</span><span :class="result.is_correct ? 'r-ok' : 'r-fail'">{{ currentAnswer || "（未作答）" }}</span></div>
            <div v-if="!result.is_correct" class="r-line"><span class="r-lbl">正确答案</span><span class="r-ok">{{ result.correct_answer }}</span></div>
            <div v-if="result.analysis" class="r-line r-analysis"><span class="r-lbl">解析</span><span>{{ result.analysis }}</span></div>
          </div>
          <div v-if="!result.is_correct" class="r-wb" :class="{ recorded: result.wrongbook_recorded }">
            <BookMarked :size="14" :stroke-width="2.5" style="margin-right:4px" />
            {{ result.wrongbook_recorded ? "已记录到错题本" : "已加入错题本" }}
          </div>
          <button class="btn-action" type="button" :disabled="loading" @click="fetchRandomQuestion" style="margin-top:4px">
            <ArrowRight :size="17" :stroke-width="2.5" style="margin-right:4px" />
            {{ loading ? "加载中..." : "下一题" }}
          </button>
        </div>
      </transition>
    </div>

    <!-- ── Session Summary Modal Overlay ── -->
    <transition name="fade">
      <div v-if="showSummary" class="summary-overlay">
        <div class="summary-backdrop"></div>
        <div class="summary-modal">
          <div class="summary-icon" :class="sessionStats.answeredCount > 0 && accuracy !== null && accuracy >= 60 ? 'sum-good' : 'sum-keep'">
            <CheckCircle v-if="sessionStats.answeredCount > 0 && accuracy !== null && accuracy >= 60" :size="36" />
            <RefreshCw v-else :size="36" />
          </div>
          <p class="summary-title">结束练习</p>
          <p class="summary-desc" v-if="sessionStats.answeredCount > 0">本次练习已完成 {{ sessionStats.answeredCount }} 题，是否返回练习设置？</p>
          <p class="summary-desc" v-else>还没有完成题目，确定要退出本次练习吗？</p>
          <div class="summary-stats">
            <div class="sum-stat"><span class="sum-val">{{ sessionStats.answeredCount }}</span><span class="sum-lbl">答题</span></div>
            <div class="sum-stat"><span class="sum-val sum-correct">{{ sessionStats.correctCount }}</span><span class="sum-lbl">正确</span></div>
            <div class="sum-stat"><span class="sum-val sum-wrong">{{ sessionStats.wrongCount }}</span><span class="sum-lbl">错误</span></div>
            <div class="sum-stat"><span class="sum-val" :class="accuracy !== null && accuracy >= 70 ? 'sum-correct' : accuracy !== null && accuracy < 40 ? 'sum-wrong' : ''">{{ accuracy !== null ? accuracy + '%' : '--' }}</span><span class="sum-lbl">正确率</span></div>
          </div>
          <div class="summary-actions">
            <button class="btn-action" type="button" @click="handleEndPractice">
              <ArrowRight :size="17" :stroke-width="2.5" style="margin-right:4px" />
              结束并返回
            </button>
            <button class="btn-action btn-secondary" type="button" @click="continuePractice">
              <Play :size="17" :stroke-width="2.5" style="margin-right:4px" />
              继续练习
            </button>
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<style scoped>
/* ── Layout ── */
.practice-page { display: grid; gap: var(--space-3); }

/* ── Compact Top Bar ── */
.topbar {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 2px;
}

.topbar-back {
  display: grid; place-items: center;
  width: 34px; height: 34px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ease-out);
}
.topbar-back:hover { background: var(--surface-soft); border-color: var(--line-accent); }

.topbar-center {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  flex: 1;
}
.topbar-course {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topbar-mode {
  flex-shrink: 0;
  padding: 1px 7px;
  border-radius: 5px;
  background: #fef3c7;
  color: #92400e;
  font-size: 10px;
  font-weight: 700;
}

/* ── Stats Chips (second row) ── */
.stats-chips {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  min-height: 24px;
}
.chip { color: var(--text-secondary); }
.chip-green { color: var(--emerald); }
.chip-rose { color: var(--rose); }
.chip-streak { color: var(--amber); }
.chip-sep { color: var(--line-strong); font-weight: 400; }

.topbar-end {
  display: grid; place-items: center;
  width: 34px; height: 34px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ease-out);
}
.topbar-end:hover { background: var(--rose-soft); color: var(--rose); border-color: var(--rose-border); }
.end-label { display: none; }
@media (min-width: 640px) {
  .topbar-end { width: auto; padding: 0 10px; gap: 4px; border-radius: 999px; }
  .end-label { display: inline; font-size: 12px; font-weight: 700; }
}

/* ── State Blocks ── */
.state-block {
  display: grid; place-items: center; gap: var(--space-2);
  padding: var(--space-10) var(--space-4); text-align: center;
}
.state-icon { color: var(--text-placeholder); margin-bottom: var(--space-1); }
.state-title { margin: 0; font-size: var(--text-base); font-weight: 700; color: var(--text-secondary); }
.state-hint { margin: 0; font-size: var(--text-sm); color: var(--text-muted); max-width: 280px; }
.error-msg { margin: 0; padding: 10px 14px; border-radius: var(--radius-sm); background: var(--rose-soft); color: var(--rose); font-size: 13px; font-weight: 600; }
.retry-btn { min-height: 38px; }

/* ── Skeleton ── */
.skeleton-wrap { width: 100%; padding: var(--space-4); }
.sk-line { height: 14px; border-radius: 8px; background: linear-gradient(90deg,#e2e8f0 25%,#f1f5f9 50%,#e2e8f0 75%); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; margin-bottom: 12px; }
.sk-line--short { width: 30%; }
.sk-line--long { width: 90%; }
.sk-line--medium { width: 65%; }
.sk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
.sk-block { height: 52px; border-radius: var(--radius-md); background: linear-gradient(90deg,#e2e8f0 25%,#f1f5f9 50%,#e2e8f0 75%); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── Question Area ── */
.question-area {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4);
  border: none;
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

/* Stem */
.stem { display: grid; gap: var(--space-2); }
.stem-meta { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.stem-tag { padding: 2px 8px; border-radius: 999px; background: #f1f5f9; color: #475467; font-size: 10px; font-weight: 700; }
.stem-hint { padding: 2px 7px; border-radius: 5px; background: #fef3c7; color: #92400e; font-size: 10px; font-weight: 700; }
.stem-text { margin: 0; font-size: 18px; font-weight: 700; line-height: 1.55; color: var(--text-main); word-break: break-word; }

/* Options grid */
.opts { display: grid; gap: 8px; }
.opt-card {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface);
  text-align: left;
  font: inherit;
  color: var(--text-main);
  cursor: pointer;
  transition: all var(--ease-out);
  min-height: 48px;
}
.opt-card:hover:not(:disabled) { border-color: var(--line-accent); background: var(--primary-soft); }
.opt-card:active:not(:disabled) { transform: scale(0.985); }
.opt-card.selected { border-color: var(--primary); background: var(--primary-soft); box-shadow: 0 0 0 2px var(--primary-glow); }

.opt-chk {
  display: grid; place-items: center;
  width: 20px; height: 20px;
  border-radius: 4px;
  border: 1.5px solid var(--line-strong);
  font-size: 12px; font-weight: 800;
  color: var(--primary);
}
.opt-card.selected .opt-chk { background: var(--primary); color: #fff; border-color: var(--primary); }

.opt-key {
  display: grid; place-items: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--primary-strong);
  font-size: 12px; font-weight: 800;
  flex-shrink: 0;
}
.opt-key--active { background: var(--primary); color: #fff; }

.opt-val { font-size: 15px; font-weight: 600; line-height: 1.5; word-break: break-word; }

/* Feedback overrides */
.opt-card.btn-correct { border-color: var(--emerald); background: var(--emerald-soft); }
.opt-card.btn-correct .opt-key { background: var(--emerald); color: #fff; }
.opt-card.btn-correct .opt-chk { background: var(--emerald); color: #fff; border-color: var(--emerald); }
.opt-card.btn-wrong { border-color: var(--rose); background: var(--rose-soft); }
.opt-card.btn-wrong .opt-key { background: var(--rose); color: #fff; }
.opt-card:disabled { opacity: 1; }

/* ── True / False ── */
.tf { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.tf-btn {
  display: grid; place-items: center; gap: 8px;
  padding: 22px 14px;
  border: 2px solid var(--line-strong);
  border-radius: var(--radius-xl);
  background: var(--surface);
  font: inherit;
  color: var(--text-main);
  cursor: pointer;
  font-size: 17px; font-weight: 800;
  transition: all var(--ease-out);
}
.tf-btn:hover:not(:disabled) { transform: translateY(-2px); }
.tf-btn:active:not(:disabled) { transform: scale(0.96); }
.tf-true:hover:not(:disabled) { border-color: var(--emerald); background: var(--emerald-soft); color: var(--emerald); }
.tf-false:hover:not(:disabled) { border-color: var(--rose); background: var(--rose-soft); color: var(--rose); }
.tf-btn.selected { border-color: var(--primary); background: var(--primary-soft); box-shadow: 0 0 0 2px var(--primary-glow); color: var(--primary-strong); }
.tf-btn.btn-correct { border-color: var(--emerald); background: var(--emerald-soft); color: var(--emerald); }
.tf-btn.btn-wrong { border-color: var(--rose); background: var(--rose-soft); color: var(--rose); }
.tf-btn:disabled { opacity: 1; }

/* ── Text Input ── */
.text-area { display: grid; gap: 4px; }
.q-input {
  width: 100%; min-height: 120px; padding: 14px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  color: var(--text-main);
  font-size: 15px; line-height: 1.7;
  resize: vertical;
  transition: border-color var(--ease-out);
}
.q-input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); }
.q-input:disabled { opacity: 0.7; }
.text-hint { margin: 0; font-size: 11px; color: var(--text-placeholder); font-weight: 500; }

/* ── Messages ── */
.msg { margin: 0; padding: 8px 12px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600; text-align: center; }
.msg-warn { background: #fef3c7; color: #92400e; }
.msg-err { background: var(--rose-soft); color: var(--rose); }

/* ── Submit hint ── */
.submit-hint {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  color: var(--text-placeholder);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

/* ── Action button ── */
.btn-action {
  display: inline-flex; align-items: center; justify-content: center;
  width: 100%;
  padding: 13px 18px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font-size: var(--text-base); font-weight: 800;
  cursor: pointer;
  box-shadow: var(--shadow-primary);
  transition: transform var(--ease-out), box-shadow var(--ease-out);
  min-height: 48px;
}
.btn-action:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(37,99,235,0.3); }
.btn-action:active:not(:disabled) { transform: translateY(0); }
.btn-action:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Skip / Reset link ── */
.skip-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 12px;
  margin: -4px auto 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-placeholder);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: color var(--ease-out), background var(--ease-out);
  justify-self: center;
}
.skip-link:hover { color: var(--text-muted); background: var(--surface-soft); }

/* ── Result ── */
.result {
  display: grid; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  animation: fadeIn 0.25s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.r-correct { background: var(--emerald-soft); border: 1px solid var(--emerald-border); }
.r-wrong { background: var(--rose-soft); border: 1px solid var(--rose-border); }
.r-head { display: flex; align-items: center; gap: 8px; }
.r-icon { flex-shrink: 0; }
.r-correct .r-icon { color: var(--emerald); }
.r-wrong .r-icon { color: var(--rose); }
.r-title { font-size: 16px; font-weight: 800; }
.r-correct .r-title { color: #065f46; }
.r-wrong .r-title { color: #991b1b; }
.r-detail { display: grid; gap: 8px; }
.r-line { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2); align-items: baseline; font-size: 14px; line-height: 1.55; }
.r-lbl { font-weight: 700; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap; }
.r-ok { color: #065f46; font-weight: 700; word-break: break-word; }
.r-fail { color: #991b1b; font-weight: 700; word-break: break-word; }
.r-analysis { display: grid; gap: 4px; padding-top: 4px; border-top: 1px solid rgba(0,0,0,0.06); }
.r-analysis span:last-child { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }
.r-wb { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: var(--radius-md); font-size: 13px; font-weight: 700; justify-self: start; }
.r-wb.recorded { background: var(--emerald-soft); color: var(--emerald); }
.r-wb:not(.recorded) { background: var(--surface-soft); color: var(--text-muted); }

.fade-enter-active { animation: fadeIn 0.25s ease; }
.fade-leave-active { animation: fadeIn 0.2s ease reverse; }

/* ── Session Summary Overlay ── */
.summary-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
}

.summary-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  pointer-events: none;
}

.summary-modal {
  position: relative;
  display: grid;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-5);
  border-radius: var(--radius-xl);
  background: var(--surface);
  text-align: center;
  justify-items: center;
  box-shadow: var(--shadow-modal);
  max-width: 340px;
  width: 100%;
  animation: fadeIn 0.25s ease;
}

.summary-icon {
  display: grid; place-items: center;
  width: 60px; height: 60px;
  border-radius: 50%;
}
.sum-good { background: var(--emerald-soft); color: var(--emerald); }
.sum-keep { background: #fef3c7; color: #d97706; }

.summary-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
  color: var(--text-main);
}

.summary-desc {
  margin: -4px 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
  line-height: 1.55;
}

.summary-stats {
  display: flex;
  gap: var(--space-5);
  justify-content: center;
}

.sum-stat { display: grid; gap: 2px; text-align: center; }
.sum-val { font-size: 20px; font-weight: 800; color: var(--text-main); }
.sum-correct { color: var(--emerald); }
.sum-wrong { color: var(--rose); }
.sum-lbl { font-size: 11px; color: var(--text-muted); font-weight: 600; }

.summary-actions {
  display: grid;
  gap: 6px;
  width: 100%;
  margin-top: var(--space-1);
}

.btn-secondary {
  background: var(--surface);
  border: 1.5px solid var(--line-strong);
  color: var(--text-main);
  box-shadow: none;
}
.btn-secondary:hover:not(:disabled) {
  border-color: var(--line-accent);
  background: var(--primary-soft);
  box-shadow: none;
  transform: translateY(-1px);
}

/* ── Responsive ── */
@media (min-width: 640px) {
  .opts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stem-text { font-size: 20px; }
}

@media (max-width: 420px) {
  .stem-text { font-size: 16px; }
  .opt-card { padding: 12px 12px; min-height: 46px; }
  .tf-btn { padding: 18px 10px; font-size: 15px; }
  .tf-btn svg { width: 20px; height: 20px; }
  .q-input { min-height: 110px; }
  .summary-modal { padding: var(--space-5) var(--space-4); max-width: 300px; }
  .sum-val { font-size: 17px; }
}
</style>
