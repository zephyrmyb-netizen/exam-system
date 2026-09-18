<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Clock, Copy, FileQuestion, Play, Trophy, Users } from "@lucide/vue";

import { useExamStore } from "@/stores/exam";
import { useAuthStore } from "@/stores/auth";
import { publishExam } from "@/api/exams";
import request, { getErrorMessage } from "@/api/request";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const auth = useAuthStore();
const examId = computed(() => Number(route.params.examId));
const publishing = ref(false);
const publishMessage = ref("");
const shareMessage = ref("");
const groupShareError = ref("");
const canPublish = computed(
  () => store.currentExam?.status === "draft" && store.currentExam.creator_id === auth.user?.id,
);
const canStart = computed(
  () => store.currentExam?.availability !== "scheduled" && store.currentExam?.availability !== "closed",
);
const shareGroupId = computed(() => Number(route.query?.share_group));
const isCreator = computed(() => store.currentExam?.creator_id === auth.user?.id);
const canShareToGroup = computed(
  () =>
    isCreator.value &&
    store.currentExam?.status === "published" &&
    Number.isInteger(shareGroupId.value) &&
    shareGroupId.value > 0,
);

function start() {
  router.replace({ name: "exam-take", params: { examId: examId.value } });
}

function openLeaderboard() {
  router.replace({ name: "exam-leaderboard", params: { examId: examId.value } });
}

function openAnalytics() {
  router.replace({ name: "exam-analytics", params: { examId: examId.value } });
}

function goBack() {
  if (route.query?.from === "study-groups") {
    router.replace({ name: "study-groups" });
    return;
  }
  router.replace({ name: "exams" });
}

function retry() {
  store.loadExam(examId.value);
}

async function copyShareLink() {
  const code = store.currentExam?.share_code;
  const link = code
    ? `${window.location.origin}/exams/share/${code}`
    : `${window.location.origin}/exams/${examId.value}`;
  shareMessage.value = "";
  try {
    await navigator.clipboard.writeText(link);
    shareMessage.value = "考试链接已复制，登录后的用户可直接打开并参加。";
  } catch {
    window.prompt("请复制考试链接", link);
  }
}

async function shareToGroup() {
  if (!canShareToGroup.value) return;
  shareMessage.value = "";
  groupShareError.value = "";
  try {
    await request.post(`/study-groups/${shareGroupId.value}/exams/${examId.value}`);
    shareMessage.value = "考试已共享到当前学习小组。";
  } catch (error) {
    groupShareError.value = getErrorMessage(error, "共享考试失败");
  }
}

async function publish() {
  if (!canPublish.value || publishing.value) return;
  publishing.value = true;
  publishMessage.value = "";
  store.error = "";
  try {
    await publishExam(examId.value);
    await store.loadExam(examId.value);
    publishMessage.value = "考试已发布，其他登录用户现在可以参加。";
  } catch (error) {
    store.error = getErrorMessage(error, "发布考试失败");
  } finally {
    publishing.value = false;
  }
}

onMounted(() => {
  store.loadExam(examId.value);
});
</script>

<template>
  <section class="exam-detail-page">
    <p v-if="store.loading" class="info-message">正在加载考试...</p>
    <p v-if="publishMessage" class="success-message" role="status">{{ publishMessage }}</p>
    <p v-if="shareMessage" class="success-message" role="status">{{ shareMessage }}</p>
    <p v-if="groupShareError" class="error-message" role="alert">{{ groupShareError }}</p>

    <div v-else-if="store.error" class="empty-panel">
      <p class="error-message">{{ store.error }}</p>
      <div class="empty-actions">
        <button type="button" class="action-btn" @click="retry">重试</button>
        <button type="button" class="action-btn ghost" @click="goBack"><ArrowLeft :size="16" /> 返回列表</button>
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

      <p v-if="store.currentExam.availability === 'scheduled'" class="info-message" data-testid="exam-detail-schedule">
        考试尚未开始，请在开始时间后进入。
      </p>
      <p v-else-if="store.currentExam.availability === 'closed'" class="error-message" data-testid="exam-detail-closed">
        考试已截止，不能再开始答题。
      </p>
      <p v-if="store.currentExam.start_at || store.currentExam.end_at" class="schedule-summary">
        {{ store.currentExam.start_at ? `开始：${store.currentExam.start_at}` : "发布后立即开始"
        }}{{ store.currentExam.end_at ? ` · 截止：${store.currentExam.end_at}` : "" }}
      </p>
      <button
        data-testid="exam-detail-start"
        class="start-button"
        type="button"
        :disabled="!store.currentExam.questions.length || !canStart"
        @click="start"
      >
        <Play :size="18" />
        开始考试
      </button>
      <button data-testid="exam-detail-leaderboard" class="leaderboard-button" type="button" @click="openLeaderboard">
        <Trophy :size="18" />
        查看排行榜
      </button>
      <button
        v-if="store.currentExam.creator_id === auth.user?.id"
        data-testid="exam-detail-analytics"
        class="leaderboard-button"
        type="button"
        @click="openAnalytics"
      >
        <Trophy :size="18" />考试数据分析
      </button>
      <button
        v-if="store.currentExam.status === 'published'"
        data-testid="exam-detail-share"
        class="leaderboard-button"
        type="button"
        @click="copyShareLink"
      >
        <Copy :size="18" />
        复制考试链接
      </button>
      <button
        v-if="canShareToGroup"
        data-testid="exam-detail-share-group"
        class="leaderboard-button"
        type="button"
        @click="shareToGroup"
      >
        <Users :size="18" />
        共享到当前小组
      </button>
      <p
        v-if="store.currentExam.status === 'published' && store.currentExam.share_code"
        class="share-code"
        data-testid="exam-detail-share-code"
      >
        邀请码：{{ store.currentExam.share_code }}
      </p>
      <button
        v-if="canPublish"
        data-testid="exam-detail-publish"
        class="publish-button"
        type="button"
        :disabled="publishing"
        @click="publish"
      >
        <Trophy :size="18" />
        {{ publishing ? "正在发布..." : "发布考试" }}
      </button>
    </article>
  </section>
</template>

<style scoped>
.exam-detail-page {
  display: grid;
  gap: var(--space-4);
}
.empty-panel {
  display: grid;
  gap: var(--space-4);
  place-items: center;
  padding: var(--space-8) var(--space-4);
  text-align: center;
}
.empty-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  justify-content: center;
}
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
.action-btn.ghost {
  background: var(--surface);
  color: var(--text-main);
  border: 1px solid var(--line-soft);
}
.detail-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--line-soft);
  border-radius: 30px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.eyebrow,
h1,
.detail-card > span {
  margin: 0;
}
.eyebrow {
  color: var(--primary);
  font-size: var(--text-xs);
  font-weight: 900;
}
h1 {
  color: var(--text-main);
  font-size: clamp(30px, 8vw, 46px);
  line-height: 1.1;
}
.detail-card > span {
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}
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
.detail-stats strong {
  color: var(--text-main);
  font-size: 28px;
  line-height: 1;
}
.schedule-summary {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--surface-soft);
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.share-code {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 800;
  text-align: center;
}
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
.publish-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 52px;
  border: 0;
  border-radius: 18px;
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-size: var(--text-base);
  font-weight: 900;
}
.publish-button:disabled {
  opacity: 0.6;
}
</style>
