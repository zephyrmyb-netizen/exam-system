<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ClipboardList, RotateCcw, Trophy } from "@lucide/vue";

import { useExamStore } from "@/stores/exam";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const examId = computed(() => Number(route.params.examId));

function backToExams() {
  store.reset();
  router.replace({ name: "exams" });
}

function openLeaderboard() {
  router.push({ name: "exam-leaderboard", params: { examId: examId.value } });
}
</script>

<template>
  <section class="exam-result-page">
    <article v-if="store.result" class="result-card">
      <div class="result-icon"><ClipboardList :size="46" /></div>
      <p>本次考试完成</p>
      <h1>{{ store.result.score }} / {{ store.result.total_score }}</h1>
      <span>正确率 {{ store.result.accuracy_rate }}%</span>

      <div class="result-stats">
        <div><strong>{{ store.result.correct_count }}</strong><span>正确</span></div>
        <div><strong>{{ store.result.wrong_count }}</strong><span>错误</span></div>
        <div><strong>{{ store.result.accuracy_rate }}%</strong><span>正确率</span></div>
      </div>

      <button class="primary-button" type="button" @click="backToExams">
        <ArrowLeft :size="18" />
        返回考试
      </button>
      <button class="ghost-button" type="button" @click="openLeaderboard">
        <Trophy :size="18" />
        查看排行榜
      </button>
      <button class="ghost-button" type="button" @click="router.replace({ name: 'exam-take', params: { examId } })">
        <RotateCcw :size="18" />
        再考一次
      </button>
    </article>

    <article v-else class="result-card muted">
      <p>暂无考试结果</p>
      <span>如果你刚刚刷新了页面，请重新进入考试并提交。</span>
      <button class="primary-button" type="button" @click="backToExams">返回考试列表</button>
    </article>
  </section>
</template>

<style scoped>
.exam-result-page { display: grid; gap: var(--space-4); }
.result-card {
  display: grid;
  place-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: 30px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
  text-align: center;
}
.result-icon {
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary);
}
.result-card p, .result-card h1, .result-card span { margin: 0; }
.result-card p { color: var(--text-main); font-size: var(--text-xl); font-weight: 900; }
.result-card h1 { color: var(--text-main); font-size: 54px; line-height: 1; }
.result-card > span { color: var(--text-muted); font-size: var(--text-sm); font-weight: 800; }
.result-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
  width: 100%;
}
.result-stats div {
  display: grid;
  gap: 4px;
  padding: var(--space-3);
  border-radius: 18px;
  background: var(--surface-soft);
}
.result-stats strong { color: var(--text-main); font-size: var(--text-xl); }
.result-stats span { color: var(--text-muted); font-size: var(--text-xs); font-weight: 800; }
.primary-button, .ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 52px;
  border-radius: 18px;
  font: inherit;
  font-weight: 900;
}
.primary-button { border: 0; background: var(--primary); color: #fff; box-shadow: var(--shadow-primary); }
.ghost-button { border: 1px solid var(--line-soft); background: var(--surface); color: var(--text-main); }
.muted { color: var(--text-muted); }
</style>
