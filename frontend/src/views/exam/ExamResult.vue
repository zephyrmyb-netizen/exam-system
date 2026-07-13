<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, CheckCircle2, ClipboardList, Clock3, RotateCcw, Trophy, XCircle } from "@lucide/vue";

import type { ExamQuestion, ExamResult as ExamResultData } from "@/types";
import { useExamStore } from "@/stores/exam";

type ExtendedResult = ExamResultData & {
  passed?: boolean;
  duration_seconds?: number;
  question_results?: Record<string, { correct?: boolean; answer?: string }>;
};

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const examId = computed(() => Number(route.params.examId));
const result = computed(() => store.result as ExtendedResult | null);
const examTitle = computed(() => store.currentExam?.title || "--");
const scorePercent = computed(() => {
  if (!result.value?.total_score) return 0;
  return Math.min(100, Math.max(0, (result.value.score / result.value.total_score) * 100));
});
const passedLabel = computed(() => {
  if (typeof result.value?.passed !== "boolean") return "--";
  return result.value.passed ? "通过" : "未通过";
});
const durationSeconds = computed(() => {
  const currentResult = result.value;
  if (!currentResult) return null;

  if (currentResult.duration_seconds !== undefined) {
    return Number.isFinite(currentResult.duration_seconds) && currentResult.duration_seconds >= 0
      ? Math.floor(currentResult.duration_seconds)
      : null;
  }

  const startedAt = store.currentAttempt?.started_at;
  const submittedAt = currentResult.submitted_at;
  if (!startedAt || !submittedAt) return null;
  const startedAtMs = Date.parse(startedAt);
  const submittedAtMs = Date.parse(submittedAt);
  if (!Number.isFinite(startedAtMs) || !Number.isFinite(submittedAtMs) || submittedAtMs < startedAtMs) return null;
  return Math.floor((submittedAtMs - startedAtMs) / 1000);
});
const durationLabel = computed(() => {
  const seconds = durationSeconds.value;
  if (seconds === null) return "--";
  return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
});
const questionDetails = computed(() => store.currentExam?.questions || []);

function questionTypeLabel(question: ExamQuestion) {
  const labels: Record<string, string> = {
    single_choice: "单选题",
    multiple_choice: "多选题",
    true_false: "判断题",
    fill_blank: "填空题",
    short_answer: "简答题",
  };
  return labels[question.question_type] || question.question_type || "题目";
}

function formatAnswer(question: ExamQuestion) {
  const detail = result.value?.question_results?.[String(question.question_id)];
  return detail?.answer || store.answers[String(question.question_id)] || "--";
}

function formatStatus(question: ExamQuestion) {
  const correct = result.value?.question_results?.[String(question.question_id)]?.correct;
  if (typeof correct !== "boolean") return "--";
  return correct ? "正确" : "错误";
}

function backToExams() {
  store.reset();
  router.replace({ name: "exams" });
}

function openLeaderboard() {
  router.replace({ name: "exam-leaderboard", params: { examId: examId.value } });
}

function retakeExam() {
  router.replace({ name: "exam-take", params: { examId: examId.value } });
}
</script>

<template>
  <section class="exam-result-page" data-reference-page="exam-complete">
    <template v-if="result">
      <header class="result-header">
        <div class="result-icon"><Trophy :size="40" :stroke-width="2.2" /></div>
        <h1>考试完成</h1>
        <p>{{ examTitle }}</p>
      </header>

      <section class="score-card" aria-label="考试成绩">
        <div class="score-ring" :style="{ '--score-angle': `${scorePercent * 3.6}deg` }">
          <div class="score-ring__inner"><strong>{{ result.score ?? "--" }}</strong><span>分</span></div>
        </div>
        <span
          class="result-badge"
          :class="{ passed: result.passed === true, failed: result.passed === false }"
          data-exam-result-pass
        >{{ passedLabel }}</span>
        <span class="score-total">满分 {{ result.total_score ?? "--" }} 分</span>
        <strong class="score-accuracy">正确率 {{ result.accuracy_rate ?? "--" }}%</strong>
      </section>

      <section class="summary-card" aria-label="答题统计">
        <div><strong class="success-text">{{ result.correct_count ?? "--" }}</strong><span>答对</span></div>
        <div><strong class="error-text">{{ result.wrong_count ?? "--" }}</strong><span>答错</span></div>
        <div><strong data-exam-result-duration>{{ durationLabel }}</strong><span>用时</span></div>
      </section>

      <section class="details-card">
        <h2><ClipboardList :size="17" /> 答题详情</h2>
        <div v-if="questionDetails.length" class="question-details">
          <article v-for="(question, index) in questionDetails" :key="question.question_id" class="question-detail">
            <div class="question-detail__meta">
              <span>第 {{ index + 1 }} 题</span>
              <span>{{ questionTypeLabel(question) }}</span>
              <span>{{ question.score ?? "--" }} 分</span>
            </div>
            <strong class="question-detail__question">{{ question.question }}</strong>
            <div class="question-detail__status" :class="{ correct: formatStatus(question) === '正确', incorrect: formatStatus(question) === '错误' }">
              <span data-question-answer>你的答案：{{ formatAnswer(question) }}</span>
              <strong v-if="formatStatus(question) === '正确'" data-question-status><CheckCircle2 :size="16" /> 正确</strong>
              <strong v-else-if="formatStatus(question) === '错误'" data-question-status><XCircle :size="16" /> 错误</strong>
              <strong v-else data-question-status>--</strong>
            </div>
          </article>
        </div>
        <p v-else class="empty-detail">暂无逐题数据</p>
      </section>

      <section class="result-meta">
        <span><Clock3 :size="15" /> 完成时间</span>
        <strong>{{ result.submitted_at || "--" }}</strong>
      </section>

      <div class="result-actions">
        <button class="primary-button" type="button" data-exam-result-action="back" @click="backToExams">
          <ArrowLeft :size="18" /> 返回考试
        </button>
        <button class="ghost-button" type="button" data-exam-result-action="leaderboard" @click="openLeaderboard">
          <Trophy :size="18" /> 查看排行榜
        </button>
        <button class="ghost-button" type="button" data-exam-result-action="retake" @click="retakeExam">
          <RotateCcw :size="18" /> 再考一次
        </button>
      </div>
    </template>

    <article v-else class="empty-result">
      <ClipboardList :size="40" />
      <h1>暂无考试结果</h1>
      <p>如果你刚刚刷新了页面，请重新进入考试并提交。</p>
      <button class="primary-button" type="button" @click="backToExams">返回考试列表</button>
    </article>
  </section>
</template>

<style scoped>
.exam-result-page {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
  padding: 36px var(--space-4) calc(40px + var(--safe-area-bottom));
}

.result-header {
  display: grid;
  justify-items: center;
  gap: var(--space-3);
  padding: 20px var(--space-4) 0;
  text-align: center;
}

.result-header h1,
.result-header p {
  margin: 0;
}

.result-header h1 {
  color: var(--text-main);
  font-family: var(--font-display);
  font-size: 24px;
  line-height: 1.2;
}

.result-header p {
  max-width: 100%;
  overflow-wrap: anywhere;
  color: var(--text-muted);
  font-size: var(--text-md);
}

.result-icon {
  display: grid;
  place-items: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: var(--shadow-primary);
  color: #fff;
}

.score-card,
.summary-card,
.details-card,
.result-meta {
  min-width: 0;
  border: 1px solid var(--glass-border);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
  -webkit-backdrop-filter: blur(var(--glass-card-blur)) saturate(160%);
}

.score-card {
  display: grid;
  justify-items: center;
  gap: 8px;
  margin-top: var(--space-3);
  padding: 28px 24px;
  border-radius: var(--radius-xl);
}

.score-ring {
  display: grid;
  place-items: center;
  width: 120px;
  height: 120px;
  margin-bottom: 8px;
  border-radius: 50%;
  background: conic-gradient(var(--primary) var(--score-angle), var(--line-soft) 0);
}

.score-ring__inner {
  display: grid;
  width: 102px;
  height: 102px;
  align-content: center;
  justify-items: center;
  border-radius: 50%;
  background: var(--surface);
  box-shadow: inset 0 0 0 1px var(--glass-border);
}

.score-ring strong {
  color: var(--primary-strong);
  font-size: 36px;
  line-height: 1;
}

.score-ring span,
.score-total {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.result-badge {
  padding: 4px 12px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 800;
}

.result-badge.passed {
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.result-badge.failed {
  background: var(--state-error-soft);
  color: var(--state-error);
}

.score-accuracy {
  color: var(--primary-strong);
  font-size: var(--text-sm);
}

.summary-card {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 20px 8px;
  border-radius: var(--radius-xl);
}

.summary-card div {
  display: grid;
  min-width: 0;
  justify-items: center;
  gap: 5px;
  padding: 0 6px;
  border-right: 1px solid var(--line-soft);
}

.summary-card div:last-child {
  border-right: 0;
}

.summary-card strong {
  max-width: 100%;
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-size: clamp(15px, 5vw, 22px);
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.summary-card span,
.result-meta {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.success-text { color: var(--primary-strong) !important; }
.error-text { color: var(--state-error) !important; }

.details-card {
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}

.details-card h2 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 4px;
  color: var(--text-main);
  font-size: var(--text-base);
}

.question-details {
  display: grid;
}

.question-detail {
  display: grid;
  min-width: 0;
  gap: 8px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line-soft);
}

.question-detail:last-child {
  border-bottom: 0;
}

.question-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.question-detail__meta span {
  padding: 3px 7px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 750;
}

.question-detail__meta span:nth-child(2) {
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.question-detail__question {
  overflow-wrap: anywhere;
  color: var(--text-main);
  font-size: var(--text-md);
  line-height: 1.55;
}

.question-detail__status {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.question-detail__status > span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.question-detail__status strong {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 4px;
}

.question-detail__status.correct strong { color: var(--primary-strong); }
.question-detail__status.incorrect strong { color: var(--state-error); }

.empty-detail {
  margin: var(--space-4) 0 4px;
  color: var(--text-muted);
  text-align: center;
}

.result-meta {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: 14px var(--space-4);
  border-radius: var(--radius-lg);
}

.result-meta span {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 6px;
}

.result-meta strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  text-align: right;
}

.result-actions {
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-3);
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 48px;
  border-radius: var(--radius-full);
  font: inherit;
  font-weight: 800;
  transition: transform var(--ease-spring);
}

.primary-button:active,
.ghost-button:active {
  transform: scale(.98);
}

.primary-button {
  border: 0;
  background: var(--primary);
  box-shadow: var(--shadow-primary);
  color: #fff;
}

.ghost-button {
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-secondary);
}

.empty-result {
  display: grid;
  justify-items: center;
  gap: var(--space-3);
  padding: 64px 20px;
  color: var(--text-muted);
  text-align: center;
}

.empty-result h1,
.empty-result p {
  margin: 0;
}

.empty-result h1 {
  color: var(--text-main);
  font-size: var(--text-xl);
}
</style>
