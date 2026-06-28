<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ClipboardCheck, Plus, RefreshCw } from "@lucide/vue";

import { useAuthStore } from "@/stores/auth";
import { useExamStore } from "@/stores/exam";

const router = useRouter();
const auth = useAuthStore();
const store = useExamStore();

const canCreateExam = computed(() => auth.can("exam:create"));

function openExam(id: number) {
  router.push({ name: "exam-detail", params: { examId: id } });
}

onMounted(() => {
  store.fetchExams();
  if (canCreateExam.value) store.fetchMyExams();
});
</script>

<template>
  <section class="exam-list-page">
    <div class="exam-hero">
      <p>正式考试</p>
      <h1>选择考试开始作答</h1>
      <span>发布后的考试会显示在这里，提交后可查看成绩。</span>
      <div class="hero-actions">
        <button type="button" @click="store.fetchExams">
          <RefreshCw :size="16" />
          刷新
        </button>
        <button v-if="canCreateExam" class="primary" type="button" @click="router.push({ name: 'exam-create' })">
          <Plus :size="17" />
          创建考试
        </button>
      </div>
    </div>

    <p v-if="store.error" class="error-message">{{ store.error }}</p>
    <p v-if="store.loading && !store.exams.length" class="info-message">正在加载考试...</p>

    <div v-if="!store.loading && !store.exams.length" class="empty-panel">
      <ClipboardCheck :size="42" color="var(--text-placeholder)" />
      <strong>暂无可参加考试</strong>
      <span>老师发布考试后，会出现在这里。</span>
    </div>

    <div class="exam-card-list">
      <article v-for="exam in store.exams" :key="exam.id" class="exam-card" @click="openExam(exam.id)">
        <div>
          <p>{{ exam.question_count }} 题 · {{ exam.total_score }} 分 · {{ exam.time_limit }} 分钟</p>
          <h2>{{ exam.title }}</h2>
          <span>{{ exam.description || "暂无考试说明" }}</span>
        </div>
        <button type="button">开始</button>
      </article>
    </div>

    <div v-if="canCreateExam && store.myExams.length" class="mine-exams">
      <div class="section-title">
        <span>我创建的考试</span>
        <button type="button" @click="store.fetchMyExams">刷新</button>
      </div>
      <article v-for="exam in store.myExams" :key="exam.id" class="mine-row">
        <div>
          <strong>{{ exam.title }}</strong>
          <span>{{ exam.status }} · {{ exam.question_count }} 题</span>
        </div>
        <button type="button" @click="openExam(exam.id)">查看</button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.exam-list-page { display: grid; gap: var(--space-4); }
.exam-hero {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-5);
  border-radius: 30px;
  color: #fff;
  background: linear-gradient(135deg, #1687ff, #2850df);
  box-shadow: 0 20px 44px rgba(37, 99, 235, 0.22);
}
.exam-hero p, .exam-hero h1, .exam-hero span { margin: 0; }
.exam-hero p { font-size: var(--text-xs); font-weight: 900; opacity: 0.78; }
.exam-hero h1 { font-size: clamp(28px, 7vw, 44px); line-height: 1.08; }
.exam-hero span { max-width: 28em; font-size: var(--text-sm); opacity: 0.84; }
.hero-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-2); }
.hero-actions button, .exam-card button, .mine-row button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid rgba(255,255,255,.42);
  border-radius: var(--radius-full);
  background: rgba(255,255,255,.16);
  color: inherit;
  font: inherit;
  font-weight: 900;
}
.hero-actions .primary { background: #fff; color: var(--primary); }
.empty-panel {
  display: grid;
  place-items: center;
  gap: var(--space-2);
  min-height: 220px;
  border: 1px dashed var(--line-strong);
  border-radius: 24px;
  background: var(--surface);
  color: var(--text-muted);
  text-align: center;
}
.empty-panel strong { color: var(--text-main); font-size: var(--text-lg); }
.exam-card-list { display: grid; gap: var(--space-3); }
.exam-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
  cursor: pointer;
}
.exam-card p, .exam-card h2, .exam-card span { margin: 0; }
.exam-card p { color: var(--primary); font-size: var(--text-xs); font-weight: 900; }
.exam-card h2 { color: var(--text-main); font-size: var(--text-xl); line-height: 1.25; }
.exam-card span { color: var(--text-muted); font-size: var(--text-sm); }
.exam-card button, .mine-row button {
  border-color: var(--line-soft);
  background: var(--primary-soft);
  color: var(--primary);
}
.mine-exams { display: grid; gap: var(--space-2); }
.section-title { display: flex; align-items: center; justify-content: space-between; color: var(--text-main); font-weight: 900; }
.section-title button { border: 0; background: transparent; color: var(--primary); font-weight: 900; }
.mine-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
}
.mine-row div { display: grid; gap: 2px; min-width: 0; }
.mine-row strong { color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mine-row span { color: var(--text-muted); font-size: var(--text-xs); font-weight: 700; }
</style>
