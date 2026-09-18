<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getExamDetailByShareCode } from "@/api/exams";
import { getErrorMessage } from "@/api/request";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const errorMessage = ref("");

async function resolve() {
  const shareCode = String(route.params.shareCode || "").trim();
  loading.value = true;
  errorMessage.value = "";
  try {
    const exam = await getExamDetailByShareCode(shareCode);
    await router.replace({ name: "exam-detail", params: { examId: exam.id }, query: { from: "share" } });
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "Unable to open this shared exam");
  } finally {
    loading.value = false;
  }
}

onMounted(resolve);
</script>

<template>
  <section class="share-resolve-page">
    <p v-if="loading" class="info-message">正在打开分享的考试…</p>
    <div v-else-if="errorMessage" class="empty-panel">
      <p class="error-message">{{ errorMessage }}</p>
      <button type="button" class="action-btn" data-testid="exam-share-retry" @click="resolve">重试</button>
    </div>
  </section>
</template>

<style scoped>
.share-resolve-page,
.empty-panel {
  display: grid;
  gap: var(--space-3);
  place-items: center;
  padding: var(--space-7) var(--space-4);
  text-align: center;
}
.action-btn {
  min-height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 800;
}
</style>
