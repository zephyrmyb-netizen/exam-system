<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Clock, FileQuestion, Play, Trophy } from "@lucide/vue";

import { useExamStore } from "@/stores/exam";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const examId = computed(() => Number(route.params.examId));

function start() {
  router.push({ name: "exam-take", params: { examId: examId.value } });
}

function openLeaderboard() {
  router.push({ name: "exam-leaderboard", params: { examId: examId.value } });
}

function goBack() {
  router.push({ name: "exams" });
}

function retry() {
  store.loadExam(examId.value);
}

onMounted(() => {
  store.loadExam(examId.value);
});
</script>

<template>
  <section class="exam-detail-page">
    <p v-if="store.loading" class="info-message">正在加载考试...</p>

    <div v-else-if="store.error" class="empty-panel">
      <p class="error-message">{{ store.error }}</p>
      <div class="empty-actions">
        <button type="button" class="action-btn" @click="retry">重试</button>
        <button type="button" class="action-btn ghost" @click="goBack">
          <ArrowLeft :size="16" /> 返回列表
        </button>
      </div>
    </div>

    <article v-if="store.currentExam" class="detail-card">
      <p class="eyebrow">考试说明</p>
      <h1>{{ store.currentExam.title }}</h1>
      <span>{{ store.currentExam.description || "请在规定时间内完成题目，提交后查看成绩。" }}</span>

      <div class="detail-stats">
        <div>
          <FileQuestion :size="22" />
          <strong>{{ store.currentExam.question_count }}</strong>
          <span>题目</span>
        </div>
        <div>
          <Clock :size="22" />
          <strong>{{ store.currentExam.time_limit }}</strong>
          <span>分钟</span>
        </div>
        <div>
          <strong>{{ store.currentExam.total_score }}</strong>
          <span>总分</span>
        </div>
      </div>

      <button class="start-button" type="button" :disabled="!store.currentExam.questions.length" @click="start">
        <Play :size="18" />
        开始考试
      </button>
      <button class="leaderboard-button" type="button" @click="openLeaderboard">
        <Trophy :size="18" />
        查看排行榜
      </button>
    </article>
  </section>
</template>

<style scoped>
.exam-detail-page { display: grid; gap: var(--space-4); }
.empty-panel {
  display: grid;
  gap: var(--space-4);
  place-items: center;
  padding: var(--space-8) var(--space-4);
  text-align: center;
}
.empty-actions { display: flex; gap: var(--space-2); flex-wrap: wrap; justify-content: center; }
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.action-btn.ghost { background: var(--surface); color: var(--text-main); border: 1px solid var(--line-soft); }
.detail-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--line-soft);
  border-radius: 30px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.eyebrow, h1, .detail-card > span { margin: 0; }
.eyebrow { color: var(--primary); font-size: var(--text-xs); font-weight: 900; }
h1 { color: var(--text-main); font-size: clamp(30px, 8vw, 46px); line-height: 1.1; }
.detail-card > span { color: var(--text-muted); font-size: var(--text-sm); line-height: 1.6; }
.detail-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}
.detail-stats div {
  display: grid;
  place-items: center;
  gap: 4px;
  min-height: 92px;
  border-radius: 20px;
  background: var(--surface-soft);
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 800;
}
.detail-stats strong { color: var(--text-main); font-size: 28px; line-height: 1; }
.start-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 56px;
  border: 0;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font: inherit;
  font-size: var(--text-lg);
  font-weight: 900;
  box-shadow: var(--shadow-primary);
}
.leaderboard-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 52px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-size: var(--text-base);
  font-weight: 900;
}
</style>
