<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ShieldCheck, Users } from "@lucide/vue";

import { getAdminStats, type AdminStats } from "@/api/admin";
import { getErrorMessage } from "@/api/request";

const stats = ref<AdminStats | null>(null);
const loading = ref(false);
const errorMessage = ref("");

async function fetchStats() {
  loading.value = true;
  errorMessage.value = "";
  try {
    stats.value = await getAdminStats();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "管理统计加载失败");
  } finally {
    loading.value = false;
  }
}

onMounted(fetchStats);
</script>

<template>
  <section class="admin-page">
    <div class="admin-hero">
      <ShieldCheck :size="34" />
      <div>
        <p>管理后台</p>
        <h1>系统总览</h1>
      </div>
    </div>

    <p v-if="loading" class="info-message">正在加载统计...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div class="admin-grid">
      <article>
        <strong>{{ stats?.user_count ?? "--" }}</strong>
        <span>用户</span>
      </article>
      <article>
        <strong>{{ stats?.course_count ?? "--" }}</strong>
        <span>题库</span>
      </article>
      <article>
        <strong>{{ stats?.question_count ?? "--" }}</strong>
        <span>题目</span>
      </article>
      <article>
        <strong>{{ stats?.exam_count ?? "--" }}</strong>
        <span>考试</span>
      </article>
      <article>
        <strong>{{ stats?.submission_count ?? "--" }}</strong>
        <span>交卷记录</span>
      </article>
    </div>

    <RouterLink class="admin-link" :to="{ name: 'admin-users' }">
      <Users :size="18" />
      用户角色管理
    </RouterLink>
  </section>
</template>

<style scoped>
.admin-page { display: grid; gap: var(--space-4); }
.admin-hero {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  border-radius: 28px;
  background: linear-gradient(135deg, #111827, #1d4ed8);
  color: #fff;
}
.admin-hero p, .admin-hero h1 { margin: 0; }
.admin-hero p { font-size: var(--text-xs); font-weight: 900; opacity: .75; }
.admin-hero h1 { font-size: clamp(28px, 7vw, 42px); line-height: 1.1; }
.admin-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}
.admin-grid article {
  display: grid;
  gap: 4px;
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.admin-grid strong { color: var(--text-main); font-size: 30px; line-height: 1; }
.admin-grid span { color: var(--text-muted); font-size: var(--text-xs); font-weight: 900; }
.admin-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 52px;
  border-radius: 18px;
  background: var(--primary);
  color: #fff;
  font-weight: 900;
  text-decoration: none;
}
</style>
