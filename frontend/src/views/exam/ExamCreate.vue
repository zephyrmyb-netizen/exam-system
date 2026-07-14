<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Check, Send } from "@lucide/vue";

import { createExam, publishExam } from "@/api/exams";
import { getQuestions } from "@/api/questions";
import { getMyCourses } from "@/api/courses";
import { getErrorMessage } from "@/api/request";
import type { Course, Question } from "@/types";

const router = useRouter();

const courses = ref<Course[]>([]);
const questions = ref<Question[]>([]);
const selectedCourseId = ref<number | null>(null);
const selectedIds = ref<Set<number>>(new Set());
const title = ref("");
const description = ref("");
const timeLimit = ref(60);
const totalScore = ref(100);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");

const selectedCount = computed(() => selectedIds.value.size);
const canSubmit = computed(() => title.value.trim() && selectedCourseId.value && selectedCount.value > 0);

async function loadCourses() {
  loading.value = true;
  errorMessage.value = "";
  try {
    courses.value = await getMyCourses();
    if (!selectedCourseId.value && courses.value.length) {
      selectedCourseId.value = courses.value[0].id;
      title.value = `${courses.value[0].name} 考试`;
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "题库加载失败");
  } finally {
    loading.value = false;
  }
}

async function loadQuestions() {
  if (!selectedCourseId.value) return;
  loading.value = true;
  errorMessage.value = "";
  selectedIds.value = new Set();
  try {
    const data = await getQuestions({ course_id: selectedCourseId.value, page: 1, page_size: 200 });
    questions.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    questions.value = [];
    errorMessage.value = getErrorMessage(error, "题目加载失败");
  } finally {
    loading.value = false;
  }
}

function toggleQuestion(id: number) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

async function save(publish = false) {
  if (!canSubmit.value || !selectedCourseId.value) return;
  saving.value = true;
  errorMessage.value = "";
  try {
    const exam = await createExam({
      title: title.value.trim(),
      description: description.value.trim(),
      course_id: selectedCourseId.value,
      time_limit: timeLimit.value,
      total_score: totalScore.value,
      question_ids: Array.from(selectedIds.value),
    });
    if (publish) await publishExam(exam.id);
    router.replace({ name: "exam-detail", params: { examId: exam.id } });
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "考试创建失败");
  } finally {
    saving.value = false;
  }
}

onMounted(loadCourses);
watch(selectedCourseId, loadQuestions);
</script>

<template>
  <section class="exam-create-page">
    <div class="create-hero">
      <p>创建考试</p>
      <h1>从题库选择题目组卷</h1>
      <span>适合老师把已有题库整理成一次正式考试。</span>
    </div>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="loading" class="info-message">加载中...</p>

    <form class="create-form" @submit.prevent="save(false)">
      <label>
        <span>考试标题</span>
        <input v-model="title" type="text" placeholder="例如：Java 期末模拟考试" />
      </label>
      <label>
        <span>考试说明</span>
        <textarea v-model="description" rows="3" placeholder="可选，填写考试范围或注意事项" />
      </label>
      <div class="form-grid">
        <label>
          <span>题库</span>
          <select v-model.number="selectedCourseId">
            <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
          </select>
        </label>
        <label>
          <span>时长</span>
          <input v-model.number="timeLimit" type="number" min="1" />
        </label>
        <label>
          <span>总分</span>
          <input v-model.number="totalScore" type="number" min="1" />
        </label>
      </div>
    </form>

    <div class="question-picker">
      <div class="picker-head">
        <strong>选择题目</strong>
        <span>已选 {{ selectedCount }} / {{ questions.length }}</span>
      </div>
      <button
        v-for="question in questions"
        :key="question.id"
        type="button"
        class="question-row"
        :class="{ selected: selectedIds.has(question.id) }"
        @click="toggleQuestion(question.id)"
      >
        <span><Check v-if="selectedIds.has(question.id)" :size="16" /></span>
        <strong>{{ question.question }}</strong>
      </button>
      <div v-if="!loading && !questions.length" class="empty-panel">这门题库还没有题目，先去导入或新增题目。</div>
    </div>

    <div class="sticky-actions">
      <button type="button" :disabled="!canSubmit || saving" @click="save(false)">保存草稿</button>
      <button class="primary" type="button" :disabled="!canSubmit || saving" @click="save(true)">
        <Send :size="17" />
        创建并发布
      </button>
    </div>
  </section>
</template>

<style scoped>
.exam-create-page { display: grid; gap: var(--space-4); }
.create-hero {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-5);
  border-radius: 28px;
  background: linear-gradient(135deg, #eaf3ff, #f6fbff);
  border: 1px solid var(--line-soft);
}
.create-hero p, .create-hero h1, .create-hero span { margin: 0; }
.create-hero p { color: var(--primary); font-size: var(--text-xs); font-weight: 900; }
.create-hero h1 { color: var(--text-main); font-size: clamp(28px, 7vw, 42px); line-height: 1.1; }
.create-hero span { color: var(--text-muted); font-size: var(--text-sm); }
.create-form { display: grid; gap: var(--space-3); }
.create-form label { display: grid; gap: 7px; color: var(--text-muted); font-size: var(--text-xs); font-weight: 900; }
.create-form input, .create-form textarea, .create-form select {
  width: 100%;
  min-height: 48px;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  padding: 0 13px;
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
}
.create-form textarea { min-height: 92px; padding-top: 12px; }
.form-grid { display: grid; grid-template-columns: 1fr 96px 96px; gap: var(--space-2); }
.question-picker { display: grid; gap: var(--space-2); }
.picker-head { display: flex; justify-content: space-between; align-items: center; color: var(--text-muted); font-size: var(--text-sm); font-weight: 850; }
.picker-head strong { color: var(--text-main); font-size: var(--text-lg); }
.question-row {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-2);
  min-height: 58px;
  padding: 10px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
  color: var(--text-main);
  text-align: left;
  font: inherit;
}
.question-row > span {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--primary);
}
.question-row strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.question-row.selected { border-color: var(--primary); background: var(--primary-soft); }
.empty-panel { padding: var(--space-5); border: 1px dashed var(--line-strong); border-radius: 20px; background: var(--surface); color: var(--text-muted); text-align: center; font-weight: 800; }
.sticky-actions {
  position: sticky;
  bottom: calc(110px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: var(--space-2);
  padding: var(--space-2);
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  backdrop-filter: blur(16px);
}
.sticky-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 50px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 900;
}
.sticky-actions button.primary { border: 0; background: var(--primary); color: #fff; box-shadow: var(--shadow-primary); }
.sticky-actions button:disabled { opacity: .55; }
@media (max-width: 520px) { .form-grid { grid-template-columns: 1fr; } }
</style>
