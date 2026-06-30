<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Trophy } from "@lucide/vue";

import { useExamStore } from "@/stores/exam";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const examId = computed(() => Number(route.params.examId));

function formatTime(value: string | null): string {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function backToExam() {
  router.replace({ name: "exam-detail", params: { examId: examId.value } });
}

onMounted(() => {
  store.fetchLeaderboard(examId.value);
});
</script>

<template>
  <section class="leaderboard-page">
    <button class="back-button" type="button" @click="backToExam">
      <ArrowLeft :size="18" />
      返回考试
    </button>

    <article class="leaderboard-hero">
      <div class="hero-icon"><Trophy :size="34" /></div>
      <p>考试排行榜</p>
      <h1>看看本场表现</h1>
      <span>仅展示已提交的考试记录，按分数从高到低排序。</span>
    </article>

    <p v-if="store.loading" class="info-message">正在加载排行榜...</p>
    <p v-if="store.error" class="error-message">{{ store.error }}</p>

    <article v-if="!store.loading && store.leaderboard?.entries.length === 0" class="empty-card">
      <Trophy :size="42" />
      <strong>还没有提交记录</strong>
      <span>完成一次考试后，这里会显示排行榜。</span>
    </article>

    <div v-if="store.leaderboard?.entries.length" class="leaderboard-list">
      <article v-for="entry in store.leaderboard.entries" :key="entry.user_id" class="leaderboard-row">
        <span class="rank" :class="{ 'rank--top': entry.rank <= 3 }">{{ entry.rank }}</span>
        <div class="user-block">
          <strong>{{ entry.username }}</strong>
          <small>{{ formatTime(entry.submitted_at) }}</small>
        </div>
        <div class="score-block">
          <strong>{{ entry.score }}</strong>
          <small>/ {{ entry.total_score }}</small>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.leaderboard-page { display: grid; gap: var(--space-4); }
.back-button {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 900;
}
.leaderboard-hero,
.empty-card,
.leaderboard-row {
  border: 1px solid var(--line-soft);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.leaderboard-hero {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-5);
  border-radius: 30px;
}
.hero-icon {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: var(--primary-soft);
  color: var(--primary);
}
.leaderboard-hero p,
.leaderboard-hero h1,
.leaderboard-hero span {
  margin: 0;
}
.leaderboard-hero p {
  color: var(--primary);
  font-size: var(--text-xs);
  font-weight: 900;
}
.leaderboard-hero h1 {
  color: var(--text-main);
  font-size: clamp(30px, 8vw, 46px);
  line-height: 1.1;
}
.leaderboard-hero span {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1.6;
}
.empty-card {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  padding: var(--space-6);
  border-radius: 28px;
  color: var(--text-muted);
  text-align: center;
}
.empty-card strong { color: var(--text-main); font-size: var(--text-lg); }
.leaderboard-list { display: grid; gap: var(--space-3); }
.leaderboard-row {
  display: grid;
  grid-template-columns: 52px 1fr auto;
  align-items: center;
  gap: var(--space-3);
  min-height: 76px;
  padding: var(--space-3);
  border-radius: 24px;
}
.rank {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 16px;
  background: var(--surface-soft);
  color: var(--text-muted);
  font-weight: 900;
}
.rank--top {
  background: linear-gradient(135deg, #facc15, #fb923c);
  color: #fff;
}
.user-block,
.score-block {
  display: grid;
  gap: 3px;
}
.user-block strong,
.score-block strong {
  color: var(--text-main);
  font-weight: 900;
}
.user-block small,
.score-block small {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 800;
}
.score-block { justify-items: end; }
.score-block strong { font-size: var(--text-2xl); line-height: 1; }
</style>
