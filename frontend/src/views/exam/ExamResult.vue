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
const durationLabel = computed(() => {
  const seconds = result.value?.duration_seconds;
  if (typeof seconds !== "number" || seconds < 0) return "--";
  return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
});
const questionDetails = computed(() => store.currentExam?.questions || []);

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
</script>

<template>
  <section class="exam-result-page">
    <template v-if="result">
      <header class="result-header">
        <div class="result-icon"><Trophy :size="40" /></div>
        <h1>考试完成</h1>
        <p>{{ examTitle }}</p>
        <span class="result-badge" :class="{ passed: result.passed === true }">{{ passedLabel }}</span>
      </header>

      <section class="score-card" aria-label="考试成绩">
        <div class="score-ring" :style="{ '--score-angle': `${scorePercent * 3.6}deg` }">
          <div class="score-ring__inner"><strong>{{ result.score ?? "--" }}</strong><span>分</span></div>
        </div>
        <div class="score-copy"><span>满分 {{ result.total_score ?? "--" }} 分</span><strong>正确率 {{ result.accuracy_rate ?? "--" }}%</strong></div>
      </section>

      <section class="summary-card">
        <div><strong class="success-text">{{ result.correct_count ?? "--" }}</strong><span>答对</span></div>
        <div><strong class="error-text">{{ result.wrong_count ?? "--" }}</strong><span>答错</span></div>
        <div><strong>{{ durationLabel }}</strong><span>用时</span></div>
      </section>

      <section class="details-card">
        <h2><ClipboardList :size="17" /> 答题详情</h2>
        <div v-if="questionDetails.length" class="question-details">
          <div v-for="(question, index) in questionDetails" :key="question.question_id" class="question-detail">
            <div class="question-detail__copy"><span>第 {{ index + 1 }} 题 · {{ question.question_type }}</span><strong>{{ question.question }}</strong></div>
            <div class="question-detail__status" :class="{ correct: formatStatus(question) === '正确', incorrect: formatStatus(question) === '错误' }">
              <span>答案 {{ formatAnswer(question) }}</span>
              <strong v-if="formatStatus(question) === '正确'"><CheckCircle2 :size="16" /> 正确</strong>
              <strong v-else-if="formatStatus(question) === '错误'"><XCircle :size="16" /> 错误</strong>
              <strong v-else>--</strong>
            </div>
          </div>
        </div>
        <p v-else class="empty-detail">--</p>
      </section>

      <section class="result-meta"><span><Clock3 :size="15" /> 完成时间</span><strong>{{ result.submitted_at || "--" }}</strong></section>

      <div class="result-actions">
        <button class="primary-button" type="button" data-exam-result-action="back" @click="backToExams"><ArrowLeft :size="18" /> 返回考试</button>
        <button class="ghost-button" type="button" @click="openLeaderboard"><Trophy :size="18" /> 查看排行榜</button>
        <button class="ghost-button" type="button" @click="router.replace({ name: 'exam-take', params: { examId } })"><RotateCcw :size="18" /> 再考一次</button>
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
.exam-result-page { display: grid; gap: 14px; padding: 24px 0 calc(32px + env(safe-area-inset-bottom)); }
.result-header { display: grid; justify-items: center; gap: 8px; padding: 20px 16px 8px; text-align: center; }
.result-header h1, .result-header p { margin: 0; }
.result-header h1 { color: var(--text-main); font-size: 24px; line-height: 1.2; }
.result-header p { color: var(--text-muted); font-size: 14px; }
.result-icon { display: grid; place-items: center; width: 80px; height: 80px; border-radius: 50%; background: var(--primary); color: #fff; box-shadow: var(--shadow-primary); }
.result-badge { padding: 5px 13px; border-radius: var(--radius-full); background: var(--surface-soft); color: var(--text-muted); font-size: 12px; font-weight: 800; }
.result-badge.passed { background: var(--primary-soft); color: var(--primary-strong); }
.score-card, .summary-card, .details-card, .result-meta { border: 1px solid var(--glass-border, var(--line-soft)); background: color-mix(in srgb, var(--surface) 92%, transparent); box-shadow: var(--shadow-card); }
.score-card { display: grid; justify-items: center; gap: 16px; padding: 24px; border-radius: var(--radius-xl); backdrop-filter: blur(20px) saturate(160%); }
.score-ring { display: grid; place-items: center; width: 120px; height: 120px; border-radius: 50%; background: conic-gradient(var(--primary) var(--score-angle), var(--surface-soft) 0); }
.score-ring__inner { display: grid; place-items: center; align-content: center; width: 100px; height: 100px; border-radius: 50%; background: var(--surface); }
.score-ring strong { color: var(--primary-strong); font-size: 36px; line-height: 1; }
.score-ring span { color: var(--text-muted); font-size: 13px; }
.score-copy { display: grid; gap: 5px; justify-items: center; color: var(--text-muted); font-size: 13px; }
.score-copy strong { color: var(--primary-strong); }
.summary-card { display: grid; grid-template-columns: repeat(3, 1fr); padding: 18px 8px; border-radius: var(--radius-xl); }
.summary-card div { display: grid; justify-items: center; gap: 5px; padding: 0 8px; border-right: 1px solid var(--line-soft); }
.summary-card div:last-child { border-right: 0; }
.summary-card strong { color: var(--text-main); font-size: 20px; font-variant-numeric: tabular-nums; }
.summary-card span, .result-meta { color: var(--text-muted); font-size: 12px; }
.success-text { color: var(--primary-strong) !important; }
.error-text { color: var(--state-error, var(--rose)) !important; }
.details-card { padding: 16px; border-radius: var(--radius-lg); }
.details-card h2 { display: flex; align-items: center; gap: 6px; margin: 0 0 4px; color: var(--text-main); font-size: 15px; }
.question-details { display: grid; }
.question-detail { display: flex; justify-content: space-between; gap: 12px; padding: 13px 0; border-bottom: 1px solid var(--line-soft); }
.question-detail:last-child { border-bottom: 0; }
.question-detail__copy { display: grid; min-width: 0; gap: 4px; }
.question-detail__copy span { color: var(--text-muted); font-size: 12px; }
.question-detail__copy strong { overflow: hidden; color: var(--text-main); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.question-detail__status { display: grid; flex: 0 0 auto; justify-items: end; gap: 4px; color: var(--text-muted); font-size: 12px; text-align: right; }
.question-detail__status strong { display: inline-flex; align-items: center; gap: 4px; }
.question-detail__status.correct strong { color: var(--primary-strong); }
.question-detail__status.incorrect strong { color: var(--state-error, var(--rose)); }
.empty-detail { margin: 16px 0 4px; color: var(--text-muted); text-align: center; }
.result-meta { display: flex; justify-content: space-between; gap: 12px; padding: 14px 16px; border-radius: var(--radius-lg); }
.result-meta span { display: inline-flex; align-items: center; gap: 6px; }
.result-meta strong { color: var(--text-secondary); font-size: 12px; font-weight: 700; }
.result-actions { display: grid; gap: 10px; padding-top: 8px; }
.primary-button, .ghost-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; width: 100%; min-height: 48px; border-radius: var(--radius-full); font: inherit; font-weight: 800; }
.primary-button { border: 0; background: var(--primary); color: #fff; box-shadow: var(--shadow-primary); }
.ghost-button { border: 1px solid var(--line-soft); background: var(--surface); color: var(--text-secondary); }
.empty-result { display: grid; justify-items: center; gap: 12px; padding: 48px 20px; color: var(--text-muted); text-align: center; }
.empty-result h1, .empty-result p { margin: 0; }
.empty-result h1 { color: var(--text-main); font-size: 22px; }
@media (min-width: 700px) { .exam-result-page { gap: 16px; padding-top: 32px; } .result-actions { grid-template-columns: 1fr 1fr 1fr; } }
</style>
