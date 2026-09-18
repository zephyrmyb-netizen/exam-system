<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { BookOpen, Copy, Layers, Play, Users } from "@lucide/vue";
import { useRoute } from "vue-router";

import request, { getErrorMessage } from "../api/request";
import PracticeModeSheet from "../components/practice/PracticeModeSheet.vue";
import { useAppNavigation } from "../composables/useAppNavigation";
import { useAuthStore } from "../stores/auth";
import { isPracticeReadyCourse } from "../utils/course";

const route = useRoute();
const { replaceWithSource } = useAppNavigation();
const auth = useAuthStore();

const courseId = computed(() => route.params.courseId);
const course = ref<any>(null);
const loading = ref(false);
const errorMessage = ref("");
const showPracticeModes = ref(false);
const shareMessage = ref("");
const groupShareError = ref("");

const navigationSource = computed(() => {
  const source = route.query.from;
  return source === "home" ||
    source === "mine" ||
    source === "public-library" ||
    source === "practice" ||
    source === "study-groups"
    ? source
    : "courses";
});
const canStartPractice = computed(() => !!course.value && isPracticeReadyCourse(course.value));
const canShare = computed(
  () => !!course.value && (course.value.visibility === "public" || course.value.owner_id === auth.user?.id),
);
const isOwner = computed(() => !!course.value && course.value.owner_id === auth.user?.id);
const shareGroupId = computed(() => Number(route.query.share_group));
const canShareToGroup = computed(() => isOwner.value && Number.isInteger(shareGroupId.value) && shareGroupId.value > 0);
const practiceCount = computed(() => course.value?.practice_count ?? 0);
const progress = computed(() => {
  const total = course.value?.question_count ?? 0;
  return total ? Math.min(100, Math.round((practiceCount.value / total) * 100)) : 0;
});

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
  }
}

function openPracticeModes() {
  if (!canStartPractice.value) return;
  showPracticeModes.value = true;
}

/* Superseded malformed legacy helper kept inert for source compatibility.
async function copyShareLink() {
  shareMessage.value = "";
  try {
    let link = `${window.location.origin}/courses/${courseId.value}`;
    if (course.value?.visibility === "private") {
      const { data } = await request.post<{ token: string }>(`/courses/${courseId.value}/share-link`);
      link = `${window.location.origin}/shared-courses/${data.token}`;
    }
    await navigator.clipboard.writeText(link);
    shareMessage.value = "题库链接已复制，登录后的用户可查看并复制到自己的题库。";
  } catch {
    window.prompt("请复制题库链接", link);
  }
}

*/
async function copyShareLinkSafe() {
  shareMessage.value = "";
  let link = `${window.location.origin}/courses/${courseId.value}`;
  try {
    if (course.value?.visibility === "private") {
      let token = course.value.share_token;
      if (!token) {
        const { data } = await request.post<{ token: string }>(`/courses/${courseId.value}/share-link`);
        token = data.token;
        course.value.share_token = token;
      }
      link = `${window.location.origin}/shared-courses/${token}`;
    }
    await navigator.clipboard.writeText(link);
    shareMessage.value =
      "\u9898\u5e93\u94fe\u63a5\u5df2\u590d\u5236\uff0c\u767b\u5f55\u540e\u7684\u7528\u6237\u53ef\u67e5\u770b\u5e76\u590d\u5236\u5230\u81ea\u5df1\u7684\u9898\u5e93\u3002";
  } catch {
    window.prompt("\u8bf7\u590d\u5236\u9898\u5e93\u94fe\u63a5", link);
  }
}

async function shareToGroup() {
  if (!canShareToGroup.value) return;
  shareMessage.value = "";
  groupShareError.value = "";
  try {
    await request.post(`/study-groups/${shareGroupId.value}/courses/${courseId.value}`);
    shareMessage.value = "题库已共享到当前学习小组。";
  } catch (error) {
    groupShareError.value = getErrorMessage(error, "共享题库失败");
  }
}

function startPractice(mode: string) {
  if (!course.value) return;
  showPracticeModes.value = false;
  if (mode === "bookmark") {
    replaceWithSource({ name: "bookmarks", query: { course_id: courseId.value } }, navigationSource.value);
    return;
  }
  replaceWithSource(
    {
      name: "course-practice",
      params: { courseId: courseId.value },
      query: { mode: mode === "sequential" ? "normal" : mode, autostart: "1" },
    },
    navigationSource.value,
  );
}

onMounted(fetchCourse);
watch(() => route.params.courseId, fetchCourse);
</script>

<template>
  <section class="course-entry-page" data-reference-page="course-entry">
    <p v-if="loading" class="info-message">正在加载题库…</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="shareMessage" class="success-message" role="status">{{ shareMessage }}</p>
    <p v-if="groupShareError" class="error-message" role="alert">{{ groupShareError }}</p>

    <template v-if="course">
      <article class="course-overview-card">
        <span class="course-overview-card__icon" aria-hidden="true"><BookOpen :size="29" :stroke-width="2" /></span>
        <div class="course-overview-card__content">
          <h1>{{ course.name || "未命名题库" }}</h1>
          <p class="course-overview-card__count">
            <Layers :size="16" :stroke-width="2.2" /> {{ course.question_count ?? 0 }} 题
          </p>
        </div>

        <div class="course-overview-card__progress">
          <p>
            已练 <strong>{{ practiceCount }}</strong> 次 · 共 {{ course.question_count ?? 0 }} 题
          </p>
          <div class="course-overview-card__track" aria-hidden="true">
            <span :style="{ width: `${progress}%` }"></span>
          </div>
        </div>
      </article>

      <button class="course-entry-page__start" type="button" :disabled="!canStartPractice" @click="openPracticeModes">
        <Play :size="20" :stroke-width="2.5" />
        {{ canStartPractice ? "开始练习" : "暂无题目" }}
      </button>

      <p v-if="!canStartPractice" class="course-entry-page__hint">该题库还没有可练习的题目。</p>
    </template>

    <button
      v-if="canShare"
      class="course-entry-page__share"
      data-testid="course-detail-share"
      type="button"
      @click="copyShareLinkSafe"
    >
      <Copy :size="17" :stroke-width="2.5" />
      复制题库链接
    </button>
    <button
      v-if="canShareToGroup"
      class="course-entry-page__share"
      data-testid="course-detail-share-group"
      type="button"
      @click="shareToGroup"
    >
      <Users :size="17" :stroke-width="2.5" />
      共享到当前小组
    </button>

    <PracticeModeSheet
      :model-value="showPracticeModes"
      :course="course"
      @update:model-value="showPracticeModes = $event"
      @select="startPractice"
    />
  </section>
</template>

<style scoped>
.course-entry-page {
  display: grid;
  align-content: start;
  gap: 20px;
  min-height: 100%;
  padding: 12px 0 calc(var(--nav-bottom-clearance) + 24px);
}

.course-overview-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
  padding: 22px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.course-overview-card__icon {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  border-radius: 18px;
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.course-overview-card__content {
  min-width: 0;
}

.course-overview-card h1 {
  margin: 2px 0 4px;
  overflow: hidden;
  color: var(--text-main);
  font-size: clamp(22px, 6vw, 28px);
  font-weight: 850;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-overview-card__count,
.course-overview-card__progress p {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 650;
}

.course-overview-card__progress {
  grid-column: 1 / -1;
  display: grid;
  gap: 10px;
  padding-top: 3px;
}

.course-overview-card__progress strong {
  color: var(--primary-strong);
  font-size: var(--text-base);
}

.course-overview-card__track {
  height: 8px;
  overflow: hidden;
  border-radius: var(--radius-full);
  background: var(--surface-strong);
}

.course-overview-card__track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
  transition: width var(--ease-out);
}

.course-entry-page__start {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 56px;
  border: 0;
  border-radius: var(--radius-lg);
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-size: var(--text-lg);
  font-weight: 850;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.course-entry-page__start:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.course-entry-page__share {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 48px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.course-entry-page__hint {
  margin: -8px 0 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-align: center;
}
</style>
