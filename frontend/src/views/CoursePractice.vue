<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ChevronLeft, LoaderCircle } from "@lucide/vue";

import { getCourse, getCoursePracticeQuestions } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { getCourseWrongPracticeQuestions } from "../api/wrongbook";
import { useAppNavigation } from "../composables/useAppNavigation";
import type { Question } from "../types";
import { isPracticeReadyCourse } from "../utils/course";
import Practice from "./Practice.vue";

type CoursePracticeMode = "normal" | "random" | "wrong_review";

const route = useRoute();
const { replaceWithSource } = useAppNavigation();
const courseId = computed(() => route.params.courseId);
const source = computed(() => {
  const value = route.query.from;
  return value === "home" || value === "mine" || value === "public-library" || value === "practice" ? value : "courses";
});

const course = ref<{ id: number; name: string; question_count: number } | null>(null);
const loading = ref(false);
const practiceStarting = ref(false);
const practiceQuestions = ref<Question[]>([]);
const errorMessage = ref("");
const showPractice = ref(false);
const selectedMode = ref<CoursePracticeMode>("normal");

const canStartPractice = computed(() => !!course.value && isPracticeReadyCourse(course.value));

function resolveMode(): CoursePracticeMode {
  const requested = String(route.query.mode || "");
  if (requested === "random") return "random";
  if (requested === "wrong" || requested === "wrong_review") return "wrong_review";
  return "normal";
}

function shuffleQuestions(questions: Question[]) {
  const shuffled = [...questions];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const target = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[target]] = [shuffled[target], shuffled[index]];
  }
  return shuffled;
}

function returnToCourseDetail() {
  replaceWithSource({ name: "course-detail", params: { courseId: courseId.value } }, source.value);
}

async function startPractice() {
  if (!canStartPractice.value || practiceStarting.value) return;

  errorMessage.value = "";
  practiceStarting.value = true;
  try {
    const questions =
      selectedMode.value === "wrong_review"
        ? await getCourseWrongPracticeQuestions(Number(courseId.value))
        : await getCoursePracticeQuestions(Number(courseId.value));
    if (!questions.length) {
      errorMessage.value = "当前题库没有可练习的题目。";
      return;
    }
    practiceQuestions.value = selectedMode.value === "random" ? shuffleQuestions(questions) : questions;
    showPractice.value = true;
  } catch (error) {
    practiceQuestions.value = [];
    errorMessage.value = getErrorMessage(error, "获取练习题目失败");
  } finally {
    practiceStarting.value = false;
  }
}

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true;
  errorMessage.value = "";
  showPractice.value = false;
  practiceQuestions.value = [];
  selectedMode.value = resolveMode();

  try {
    const data = await getCourse(Number(courseId.value));
    course.value = data;
    if (route.query.autostart === "1" && isPracticeReadyCourse(data)) {
      await startPractice();
    } else {
      returnToCourseDetail();
    }
  } catch (error) {
    course.value = null;
    errorMessage.value = getErrorMessage(error, "获取题库信息失败");
  } finally {
    loading.value = false;
  }
}

function endPractice() {
  returnToCourseDetail();
}

onMounted(fetchCourse);
watch(
  () => route.fullPath,
  () => void fetchCourse(),
);
</script>

<template>
  <Practice
    v-if="showPractice"
    :course-id="courseId"
    :course-name="course?.name || ''"
    :total-questions="practiceQuestions.length"
    :initial-questions="practiceQuestions"
    :mode="selectedMode"
    mode-param=""
    @end-practice="endPractice"
  />

  <section v-else class="course-practice-loading" aria-live="polite">
    <LoaderCircle v-if="loading || practiceStarting" class="course-practice-loading__spinner" :size="28" />
    <p v-if="loading || practiceStarting">正在准备练习…</p>
    <p v-else-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <button v-if="errorMessage" class="ghost-button" type="button" @click="returnToCourseDetail">
      <ChevronLeft :size="18" :stroke-width="2.5" />
      返回题库详情
    </button>
  </section>
</template>

<style scoped>
.course-practice-loading {
  display: grid;
  justify-items: center;
  gap: var(--space-3);
  min-height: 45dvh;
  padding: var(--space-8) var(--space-4);
  color: var(--text-secondary);
  text-align: center;
}

.course-practice-loading p {
  margin: 0;
  font-weight: 700;
}

.course-practice-loading__spinner {
  color: var(--primary);
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
