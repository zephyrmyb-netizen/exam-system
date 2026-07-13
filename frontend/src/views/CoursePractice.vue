<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { BookOpen, Layers, Play, Shuffle, RefreshCw } from "@lucide/vue";
import Practice from "./Practice.vue";

const route = useRoute();
const router = useRouter();
const courseId = computed(() => route.params.courseId);

const course = ref(null);
const loading = ref(false);
const errorMessage = ref("");

const modes = [
  { key: "normal", label: "随机练习", desc: "从当前题库随机抽题", icon: Shuffle, color: "var(--primary)" },
  { key: "wrong_review", label: "错题强化", desc: "复习当前题库做错的题", icon: RefreshCw, color: "var(--rose)" },
];

const selectedMode = ref("normal");
const canStartPractice = computed(() => !!course.value && isPracticeReadyCourse(course.value));
const startButtonText = computed(() => {
  if (loading.value) return "加载中...";
  if (!canStartPractice.value) return "暂无题目";
  return selectedMode.value === "wrong_review" ? "开始错题强化" : "开始练习";
});

const showPractice = ref(false);

function syncPracticeRequest() {
  const requestedMode = String(route.query?.mode || "");
  selectedMode.value = requestedMode === "wrong" ? "wrong_review" : "normal";
  if (route.query?.autostart === "1" && course.value && isPracticeReadyCourse(course.value)) {
    showPractice.value = true;
  }
}

function startPractice() {
  if (!canStartPractice.value) return;
  showPractice.value = true;
}

function endPractice() {
  showPractice.value = false;
}

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await request.get(`/courses/${courseId.value}`);
    course.value = data;
  } catch (error) {
    course.value = null;
    errorMessage.value = getErrorMessage(error, "获取题库信息失败");
  } finally {
    loading.value = false;
    syncPracticeRequest();
  }
}

onMounted(fetchCourse);
watch(() => route.fullPath, () => { showPractice.value = false; fetchCourse(); });
</script>

<template>
  <section class="stack course-practice-page">
    <template v-if="!showPractice">
      <div v-if="course" class="settings-header">
        <div class="settings-header-top">
          <div class="settings-icon"><BookOpen :size="22" :stroke-width="2" /></div>
          <div class="settings-info">
            <h2 :title="getCourseDisplayName(course)">{{ getCourseDisplayName(course) }}</h2>
            <p class="settings-meta">
              <Layers :size="13" :stroke-width="2" />
              <span>{{ course.question_count ?? 0 }} 道题</span>
            </p>
          </div>
        </div>
      </div>

      <p v-if="loading" class="info-message">正在加载题库...</p>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

      <div class="mode-section">
        <p class="settings-section-label">练习模式</p>
        <div class="mode-grid">
          <button
            v-for="m in modes"
            :key="m.key"
            class="mode-card"
            :class="{ 'mode-active': selectedMode === m.key }"
            :aria-pressed="selectedMode === m.key"
            type="button"
            @click="selectedMode = m.key"
          >
            <span class="mode-card-icon" :style="{ color: m.color }">
              <component :is="m.icon" :size="20" :stroke-width="2" />
            </span>
            <span class="mode-card-text">
              <span class="mode-card-title">{{ m.label }}</span>
              <span class="mode-card-desc">{{ m.desc }}</span>
            </span>
          </button>
        </div>
      </div>

      <div class="settings-actions">
        <p v-if="course && !canStartPractice" class="empty-state">
          当前题库还没有题目。先导入题目后再开始练习。
        </p>
        <button class="start-btn" type="button" :disabled="loading || !canStartPractice" @click="startPractice">
          <Play :size="18" :stroke-width="2.5" style="margin-right: 6px" />
          {{ startButtonText }}
        </button>
        <button
          v-if="course && !canStartPractice"
          class="ghost-button full-button"
          type="button"
          @click="router.replace({ name: 'import', query: { course_id: courseId } })"
        >
          去导入题目
        </button>
      </div>
    </template>

    <template v-else>
      <Practice
        :course-id="courseId"
        :course-name="course?.name || ''"
        :total-questions="course?.question_count ?? 0"
        :mode="selectedMode"
        mode-param=""
        @end-practice="endPractice"
      />
    </template>
  </section>
</template>

<style scoped>
.settings-header {
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--surface);
}
.settings-header-top { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: var(--space-3); }
.settings-icon { display: grid; place-items: center; width: 40px; height: 40px; border-radius: var(--radius-sm); background: var(--primary-soft); color: var(--primary-strong); flex-shrink: 0; }
.settings-info { min-width: 0; }
.settings-info h2 { margin: 0; overflow: hidden; font-size: var(--text-lg); font-weight: 800; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; }
.settings-meta { display: inline-flex; align-items: center; gap: 4px; margin: 4px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; }
.mode-section { display: grid; gap: 6px; }
.settings-section-label { margin: 4px 0 0; font-size: var(--text-xs); font-weight: 800; color: var(--text-muted); }
.mode-grid { display: grid; gap: 6px; }
.mode-card {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 60px;
  padding: 10px 12px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--surface);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition: background var(--ease-out), border-color var(--ease-out), color var(--ease-out);
}
.mode-card:hover { border-color: var(--line-accent); }
.mode-active { border-color: var(--primary); background: var(--primary-soft); box-shadow: inset 3px 0 0 var(--primary); }
.mode-active .mode-card-title { color: var(--primary-strong); }
.mode-card-icon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: var(--radius-sm); background: var(--surface-soft); flex-shrink: 0; }
.mode-active .mode-card-icon { background: var(--surface); }
.mode-card-text { display: grid; gap: 1px; min-width: 0; }
.mode-card-title { font-size: var(--text-sm); font-weight: 700; color: var(--text-main); }
.mode-card-desc { font-size: 11px; color: var(--text-muted); font-weight: 500; }
.settings-actions { display: grid; gap: 8px; }
.empty-state { margin: 0; color: var(--text-muted); font-size: var(--text-sm); line-height: 1.5; }
.start-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 48px;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: #fff;
  font-size: var(--text-base);
  font-weight: 800;
  cursor: pointer;
  box-shadow: var(--shadow-xs);
  transition: background var(--ease-out), box-shadow var(--ease-out);
}
.start-btn:hover:not(:disabled) { background: var(--primary-strong); box-shadow: var(--shadow-sm); }
.start-btn:active:not(:disabled) { box-shadow: var(--shadow-xs); }
.start-btn:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
@media (max-width: 420px) {
  .settings-info h2 { font-size: 16px; }
}
</style>
