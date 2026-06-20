<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import { useAuth } from "../stores/auth";
import {
  BookOpen, Layers, Play, Globe, Lock, Upload, Trash2, ArrowLeft,
} from "@lucide/vue";
import QuestionList from "./QuestionList.vue";

const route = useRoute();
const router = useRouter();
const { user } = useAuth();
const courseId = computed(() => route.params.courseId);

const course = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const publishLoading = ref(false);
const deleteLoading = ref(false);

const isOwner = computed(() => {
  if (!course.value || !user.value) return false;
  return course.value.owner_id === user.value.id;
});

const isFromPublicLibrary = computed(() => route.query.from === "public-library");

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await request.get(`/courses/${courseId.value}`);
    course.value = data;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取课程信息失败");
  } finally {
    loading.value = false;
  }
}

async function publishCourse() {
  if (!course.value || course.value.visibility === "public") return;
  const confirmed = window.confirm(
    `确定将课程「${course.value.name}」发布到公共题库吗？\n发布后所有用户都能看到这门课的题目。`
  );
  if (!confirmed) return;

  publishLoading.value = true;
  try {
    const { data } = await request.post(`/courses/${courseId.value}/publish`);
    course.value.visibility = data.visibility || "public";
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "发布失败");
  } finally {
    publishLoading.value = false;
  }
}

async function deleteCourse() {
  if (!course.value) return;
  const confirmed = window.confirm(
    `确定删除课程「${course.value.name}」吗？\n该课程共 ${course.value.question_count ?? 0} 道题，删除后题目将被一并移除，此操作不可撤销。`
  );
  if (!confirmed) return;

  deleteLoading.value = true;
  errorMessage.value = "";
  try {
    await request.delete(`/courses/${courseId.value}`);
    router.push({ name: "courses" });
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "删除课程失败");
  } finally {
    deleteLoading.value = false;
  }
}

function goBackToPublicLibrary() {
  router.push({ name: "public-library" });
}

onMounted(fetchCourse);

watch(
  () => route.params.courseId,
  () => {
    fetchCourse();
  }
);
</script>

<template>
  <section class="stack">
    <div v-if="loading" class="info-message">加载课程信息...</div>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div v-if="course" class="course-header">
      <div class="course-header-top">
        <div class="course-header-icon" :style="{ background: 'var(--primary-soft)' }">
          <BookOpen :size="24" :stroke-width="2" />
        </div>
        <div class="course-header-info">
          <h2>{{ course.name || "课程" }}</h2>
          <p class="course-header-meta">
            <Layers :size="14" :stroke-width="2" />
            <span>{{ course.question_count ?? 0 }} 道题</span>
            <span class="visibility-badge" :class="course.visibility">
              <Lock v-if="course.visibility === 'private'" :size="11" :stroke-width="2.5" />
              <Globe v-else :size="11" :stroke-width="2.5" />
              {{ course.visibility === "public" ? "已公开" : "私有" }}
            </span>
          </p>
        </div>
      </div>
      <p v-if="course.description" class="course-desc">{{ course.description }}</p>

      <div class="course-header-actions">
        <button
          class="primary-button"
          type="button"
          @click="router.push(`/courses/${courseId}/practice`)"
        >
          <Play :size="17" :stroke-width="2.5" style="margin-right:6px" />
          练这门课
        </button>
        <button
          v-if="course.visibility === 'private' && isOwner"
          class="ghost-button"
          type="button"
          :disabled="publishLoading"
          @click="publishCourse"
        >
          <Upload :size="16" :stroke-width="2.5" style="margin-right:4px" />
          发布到公共题库
        </button>
        <button
          v-if="isOwner"
          class="delete-btn-subtle"
          type="button"
          :disabled="deleteLoading"
          @click="deleteCourse"
          title="删除此课程"
        >
          <Trash2 :size="16" :stroke-width="2.5" />
        </button>
      </div>

      <!-- From public library: back link -->
      <button
        v-if="isFromPublicLibrary"
        class="ghost-button back-to-lib"
        type="button"
        @click="goBackToPublicLibrary"
      >
        <ArrowLeft :size="16" :stroke-width="2.5" style="margin-right:4px" />
        返回公共题库
      </button>
    </div>

    <QuestionList :courseId="courseId" />
  </section>
</template>

<style scoped>
.course-header {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.course-header-top {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-3);
}

.course-header-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  color: var(--primary-strong);
}

.course-header-info {
  min-width: 0;
}

.course-header-info h2 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 800;
  line-height: 1.2;
}

.course-header-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  flex-wrap: wrap;
}

.visibility-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.visibility-badge.private {
  background: #f1f5f9;
  color: #64748b;
}

.visibility-badge.public {
  background: #ecfdf3;
  color: #067647;
}

.course-desc {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.55;
}

.course-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.back-to-lib {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
}

.delete-btn-subtle {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--line-strong);
  cursor: pointer;
  transition: all var(--ease-out);
  flex-shrink: 0;
}

.delete-btn-subtle:hover:not(:disabled) {
  color: var(--rose);
  background: var(--rose-soft);
  border-color: var(--rose-border);
}

.primary-button,
.ghost-button,
.danger-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 420px) {
  .course-header-info h2 {
    font-size: var(--text-lg);
  }
}
</style>
