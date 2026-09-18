<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, BarChart3 } from "@lucide/vue";
import { getOwnerExamAnalytics } from "@/api/analytics";
import { getErrorMessage } from "@/api/request";
import type { ExamAnalytics as ExamAnalyticsData } from "@/types";

const route = useRoute();
const router = useRouter();
const examId = computed(() => Number(route.params.examId));
const data = ref<ExamAnalyticsData | null>(null);
const loading = ref(false);
const errorMessage = ref("");

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try {
    data.value = await getOwnerExamAnalytics(examId.value);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "加载考试分析失败");
  } finally {
    loading.value = false;
  }
}
function back() {
  router.replace({ name: "exam-detail", params: { examId: examId.value } });
}
onMounted(load);
</script>

<template>
  <section class="exam-analytics-page">
    <button class="back-button" type="button" @click="back"><ArrowLeft :size="18" />返回考试</button>
    <header>
      <BarChart3 :size="32" />
      <p>发布者数据</p>
      <h1>考试数据分析</h1>
    </header>
    <p v-if="loading" class="info-message">正在计算分析…</p>
    <div v-else-if="errorMessage" class="empty-panel">
      <p class="error-message">{{ errorMessage }}</p>
      <button class="action-btn" type="button" @click="load">重试</button>
    </div>
    <template v-else-if="data">
      <section class="summary-grid">
        <div>
          <strong>{{ data.participant_count }}</strong
          ><span>参与人数</span>
        </div>
        <div>
          <strong>{{ data.average_score }}</strong
          ><span>平均分</span>
        </div>
        <div>
          <strong>{{ data.average_accuracy_rate }}%</strong><span>平均正确率</span>
        </div>
      </section>
      <section class="question-card">
        <h2>题目正确率（从易错到易）</h2>
        <p v-if="!data.question_stats.length" class="info-message">还没有题目数据。</p>
        <div v-for="item in data.question_stats" :key="item.question_id" class="question-row">
          <span>第 {{ item.order_index + 1 }} 题</span><strong>{{ item.accuracy_rate }}%</strong
          ><small>{{ item.correct_count }} / {{ item.attempt_count }} 人答对</small>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.exam-analytics-page {
  display: grid;
  gap: var(--space-4);
}
.back-button {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-weight: 800;
}
header,
.question-card,
.summary-grid div {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
header {
  display: grid;
  gap: 8px;
  padding: var(--space-5);
  color: var(--primary);
}
header p,
header h1 {
  margin: 0;
}
header h1 {
  color: var(--text-main);
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}
.summary-grid div {
  display: grid;
  gap: 5px;
  padding: var(--space-3);
  text-align: center;
}
.summary-grid strong {
  color: var(--primary-strong);
  font-size: var(--text-xl);
}
.summary-grid span,
.question-row small {
  color: var(--text-muted);
  font-size: var(--text-xs);
}
.question-card {
  display: grid;
  gap: 8px;
  padding: var(--space-4);
}
.question-card h2 {
  margin: 0;
  color: var(--text-main);
  font-size: var(--text-base);
}
.question-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line-soft);
}
.question-row strong {
  color: var(--state-error);
}
.question-row small {
  grid-column: 1 / -1;
}
.action-btn {
  min-height: 44px;
  border: 0;
  border-radius: var(--radius-md);
  padding: 0 18px;
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 800;
}
</style>
