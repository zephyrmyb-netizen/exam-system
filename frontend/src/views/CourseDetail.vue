<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import request, { getErrorMessage } from "../api/request";
import CourseEditModal from "../components/course/CourseEditModal.vue";
import CourseHeader from "../components/course/CourseHeader.vue";
import { useAuth } from "../stores/auth";
import { useConfirmDialog } from "../stores/confirmDialog";
import { isPracticeReadyCourse } from "../utils/course";
import QuestionList from "./QuestionList.vue";

const route = useRoute();
const router = useRouter();
const { user } = useAuth();
const confirmDialog = useConfirmDialog();

const courseId = computed(() => route.params.courseId);
const course = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const publishLoading = ref(false);
const deleteLoading = ref(false);
const exportLoading = ref(false);

const showForm = ref(false);
const formLoading = ref(false);
const formError = ref("");

const isOwner = computed(() => course.value?.owner_id === user.value?.id);
const canStartPractice = computed(() => !!course.value && isPracticeReadyCourse(course.value));

function openEdit() {
  if (!course.value) return;
  formError.value = "";
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
}

async function handleSave(form) {
  if (!form.name.trim()) {
    formError.value = "题库名称不能为空";
    return;
  }

  formLoading.value = true;
  formError.value = "";
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      subject: form.subject.trim(),
    };
    const { data } = await request.patch(`/courses/${courseId.value}`, payload);
    Object.assign(course.value, data);
    closeForm();
  } catch (error) {
    formError.value = getErrorMessage(error, "保存失败");
  } finally {
    formLoading.value = false;
  }
}

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await request.get(`/courses/${courseId.value}`);
    course.value = data;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取题库信息失败");
  } finally {
    loading.value = false;
  }
}

async function publishCourse() {
  if (!course.value || course.value.visibility === "public") return;

  const confirmed = await confirmDialog.confirm({
    title: "发布到公共题库",
    message: `确定将「${course.value.name}」发布到公共题库吗？其他用户将可以看到这个题库。`,
    confirmText: "发布",
  });
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

async function unpublishCourse() {
  if (!course.value || course.value.visibility !== "public") return;

  const confirmed = await confirmDialog.confirm({
    title: "撤回公开",
    message: `确定撤回「${course.value.name}」的公开状态吗？撤回后其他用户将无法继续看到。`,
    confirmText: "撤回",
  });
  if (!confirmed) return;

  publishLoading.value = true;
  try {
    const { data } = await request.post(`/courses/${courseId.value}/unpublish`);
    course.value.visibility = data.visibility || "private";
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "操作失败");
  } finally {
    publishLoading.value = false;
  }
}

async function deleteCourse() {
  if (!course.value) return;

  const confirmed = await confirmDialog.confirm({
    title: "删除题库",
    message: `确定删除「${course.value.name}」吗？\n该题库共 ${course.value.question_count ?? 0} 道题，删除后题目将一并移除，此操作不可撤销。`,
    confirmText: "删除",
    tone: "danger",
  });
  if (!confirmed) return;

  deleteLoading.value = true;
  errorMessage.value = "";
  try {
    await request.delete(`/courses/${courseId.value}`);
    router.push({ name: "courses" });
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "删除题库失败");
  } finally {
    deleteLoading.value = false;
  }
}

function goToPractice() {
  if (!canStartPractice.value) return;
  router.push(`/courses/${courseId.value}/practice`);
}

function goToImport() {
  router.push({ name: "import", query: { course_id: courseId.value } });
}

async function exportCourse() {
  if (!course.value || exportLoading.value) return;
  exportLoading.value = true;
  errorMessage.value = "";
  try {
    const response = await request.get(`/exports/courses/${courseId.value}.json`, { responseType: "blob" });
    const blobUrl = window.URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = `${course.value.name || "course"}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "导出题库失败");
  } finally {
    exportLoading.value = false;
  }
}

onMounted(fetchCourse);
watch(() => route.params.courseId, fetchCourse);
</script>

<template>
  <section class="stack">
    <div v-if="loading" class="info-message">加载题库信息...</div>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <CourseHeader
      v-if="course"
      :course="course"
      :is-owner="isOwner"
      :can-start-practice="canStartPractice"
      :publish-loading="publishLoading"
      :delete-loading="deleteLoading"
      @practice="goToPractice"
      @import="goToImport"
      @edit="openEdit"
      @publish="publishCourse"
      @unpublish="unpublishCourse"
      @export="exportCourse"
      @delete="deleteCourse"
    />

    <QuestionList :course-id="courseId" />

    <CourseEditModal
      v-if="showForm && course"
      :course="course"
      :loading="formLoading"
      :error="formError"
      @close="closeForm"
      @save="handleSave"
    />
  </section>
</template>
