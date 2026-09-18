<script setup lang="ts">
import { BookCopy, CheckCircle2, Layers } from "@lucide/vue";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { copySharedCourse, getSharedCourse } from "../api/courses";
import { getErrorMessage } from "../api/request";
import type { SharedCourse } from "../types";

const route = useRoute();
const router = useRouter();
const token = computed(() => String(route.params.token || ""));
const course = ref<SharedCourse | null>(null);
const loading = ref(false);
const copying = ref(false);
const errorMessage = ref("");

async function loadSharedCourse() {
  if (!token.value) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    course.value = await getSharedCourse(token.value);
  } catch (error) {
    course.value = null;
    errorMessage.value = getErrorMessage(error, "分享链接无效或已失效");
  } finally {
    loading.value = false;
  }
}

async function copyCourse() {
  if (!course.value || copying.value) return;
  copying.value = true;
  errorMessage.value = "";
  try {
    const { id } = await copySharedCourse(token.value);
    await router.replace({ name: "course-detail", params: { courseId: id }, query: { from: "courses" } });
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "复制题库失败，请稍后重试");
  } finally {
    copying.value = false;
  }
}

onMounted(loadSharedCourse);
</script>

<template>
  <section class="shared-course-page">
    <p v-if="loading" class="info-message">正在读取分享题库…</p>
    <div v-else-if="errorMessage && !course" class="empty-panel">
      <p class="error-message">{{ errorMessage }}</p>
      <button class="ghost-button" type="button" @click="loadSharedCourse">重新加载</button>
    </div>
    <article v-else-if="course" class="shared-course-card">
      <span class="shared-course-icon"><BookCopy :size="28" /></span>
      <p class="shared-course-eyebrow">他人分享的私有题库</p>
      <h1>{{ course.name }}</h1>
      <p v-if="course.description" class="shared-course-description">{{ course.description }}</p>
      <p class="shared-course-meta">
        <span v-if="course.subject">{{ course.subject }}</span>
        <span><Layers :size="15" /> {{ course.question_count }} 题</span>
      </p>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <button class="primary-button shared-course-copy" type="button" :disabled="copying" @click="copyCourse">
        <CheckCircle2 :size="18" />
        {{ copying ? "正在复制…" : "复制到我的题库" }}
      </button>
      <p class="shared-course-hint">复制后会生成一份独立的私有题库，双方后续修改互不影响。</p>
    </article>
  </section>
</template>

<style scoped>
.shared-course-page {
  display: grid;
  min-height: 100%;
  place-items: start stretch;
  padding: 24px 0;
}
.shared-course-card {
  display: grid;
  gap: 14px;
  padding: 26px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}
.shared-course-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: var(--primary-soft);
  color: var(--primary-strong);
}
.shared-course-eyebrow,
.shared-course-description,
.shared-course-hint {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.55;
}
.shared-course-eyebrow {
  font-size: var(--text-sm);
  font-weight: 800;
  color: var(--primary-strong);
}
h1 {
  margin: -5px 0 0;
  color: var(--text-main);
  font-size: clamp(24px, 7vw, 32px);
  line-height: 1.2;
}
.shared-course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 700;
}
.shared-course-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.shared-course-copy {
  min-height: 52px;
  margin-top: 4px;
}
.shared-course-hint {
  font-size: var(--text-sm);
}
</style>
