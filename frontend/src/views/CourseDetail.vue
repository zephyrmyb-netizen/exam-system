<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import { useAuth } from "../stores/auth";
import {
  BookOpen, Layers, Play, Globe, Lock, Upload, Trash2, Pencil, X,
} from "@lucide/vue";
import QuestionList from "./QuestionList.vue";
import { useConfirmDialog } from "../stores/confirmDialog";

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

// ── Edit form state ──
const showForm = ref(false);
const formLoading = ref(false);
const formError = ref("");
const form = reactive({ name: "", description: "", subject: "" });

function openEdit() {
  if (!course.value) return;
  form.name = course.value.name || "";
  form.description = course.value.description || "";
  form.subject = course.value.subject || "";
  formError.value = "";
  showForm.value = true;
}
function closeForm() { showForm.value = false; }

async function handleSave() {
  if (!form.name.trim()) { formError.value = "课程名称不能为空"; return; }
  formLoading.value = true; formError.value = "";
  try {
    const payload = { name: form.name.trim(), description: form.description.trim(), subject: form.subject.trim() };
    const { data } = await request.patch(`/courses/${courseId.value}`, payload);
    Object.assign(course.value, data);
    closeForm();
  } catch (error) { formError.value = getErrorMessage(error, "保存失败"); }
  finally { formLoading.value = false; }
}

const isOwner = computed(() => course.value?.owner_id === user.value?.id);

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true; errorMessage.value = "";
  try { const { data } = await request.get(`/courses/${courseId.value}`); course.value = data; }
  catch (error) { errorMessage.value = getErrorMessage(error, "获取课程信息失败"); }
  finally { loading.value = false; }
}

async function publishCourse() {
  if (!course.value || course.value.visibility === "public") return;
  const confirmed = await confirmDialog.confirm({
    title: "发布到公共题库",
    message: `确定将「${course.value.name}」发布到公共题库吗？其他用户将可以看到这门课程。`,
    confirmText: "发布",
  });
  if (!confirmed) return;
  publishLoading.value = true;
  try { const { data } = await request.post(`/courses/${courseId.value}/publish`); course.value.visibility = data.visibility || "public"; }
  catch (error) { errorMessage.value = getErrorMessage(error, "发布失败"); }
  finally { publishLoading.value = false; }
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
  try { const { data } = await request.post(`/courses/${courseId.value}/unpublish`); course.value.visibility = data.visibility || "private"; }
  catch (error) { errorMessage.value = getErrorMessage(error, "操作失败"); }
  finally { publishLoading.value = false; }
}

async function deleteCourse() {
  if (!course.value) return;
  const confirmed = await confirmDialog.confirm({
    title: "删除课程",
    message: `确定删除「${course.value.name}」吗？\n该课程共 ${course.value.question_count ?? 0} 道题，删除后题目将被一并移除，此操作不可撤销。`,
    confirmText: "删除",
    tone: "danger",
  });
  if (!confirmed) return;
  deleteLoading.value = true; errorMessage.value = "";
  try { await request.delete(`/courses/${courseId.value}`); router.push({ name: "courses" }); }
  catch (error) { errorMessage.value = getErrorMessage(error, "删除课程失败"); }
  finally { deleteLoading.value = false; }
}

onMounted(fetchCourse);
watch(() => route.params.courseId, fetchCourse);
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
            <span v-if="course.subject" class="meta-subject">{{ course.subject }}</span>
            <span class="visibility-badge" :class="course.visibility">
              <Lock v-if="course.visibility === 'private'" :size="11" :stroke-width="2.5" />
              <Globe v-else :size="11" :stroke-width="2.5" />
              {{ course.visibility === "public" ? "已公开" : "私有" }}
            </span>
          </p>
        </div>
      </div>
      <p v-if="course.description" class="course-desc">{{ course.description }}</p>

      <p v-if="course.visibility === 'public' && isOwner" class="public-hint">
        <Globe :size="14" :stroke-width="2.5" style="margin-right:4px;flex-shrink:0" />已公开，其他用户可在公共题库中看到
      </p>

      <div class="course-header-actions">
        <button class="primary-button" type="button" @click="router.push(`/courses/${courseId}/practice`)">
          <Play :size="17" :stroke-width="2.5" style="margin-right:6px" />练这门课
        </button>
        <button v-if="isOwner" class="ghost-button" type="button" @click="openEdit">
          <Pencil :size="15" :stroke-width="2.5" style="margin-right:4px" />编辑
        </button>
        <button v-if="isOwner && course.visibility === 'private'" class="ghost-button" type="button" :disabled="publishLoading" @click="publishCourse">
          <Upload :size="15" :stroke-width="2.5" style="margin-right:4px" />发布到公共题库
        </button>
        <button v-if="isOwner && course.visibility === 'public'" class="ghost-button" type="button" :disabled="publishLoading" @click="unpublishCourse">
          <Lock :size="15" :stroke-width="2.5" style="margin-right:4px" />撤回公开
        </button>
        <button v-if="isOwner" class="delete-btn-subtle" type="button" :disabled="deleteLoading" @click="deleteCourse" title="删除此课程">
          <Trash2 :size="16" :stroke-width="2.5" />
        </button>
      </div>
    </div>

    <QuestionList :courseId="courseId" />

    <!-- ── Edit Form Modal ── -->
    <div v-if="showForm" class="form-overlay" @click.self="closeForm">
      <div class="form-modal">
        <div class="form-head"><h3>编辑课程</h3><button class="form-close" type="button" @click="closeForm"><X :size="18" :stroke-width="2.5" /></button></div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <label class="field"><span class="field-label">课程名称</span><input v-model="form.name" class="field-input" type="text" /></label>
        <label class="field"><span class="field-label">科目</span><input v-model="form.subject" class="field-input" type="text" placeholder="可选" /></label>
        <label class="field"><span class="field-label">描述</span><textarea v-model="form.description" class="field-input field-textarea" placeholder="可选" /></label>
        <div class="form-actions">
          <button class="btn-cancel" type="button" @click="closeForm">取消</button>
          <button class="btn-save" type="button" :disabled="formLoading" @click="handleSave">{{ formLoading ? "保存中..." : "保存" }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.course-header { display: grid; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--line-soft); border-radius: var(--radius-lg); background: var(--surface); box-shadow: var(--shadow-xs); }
.course-header-top { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: var(--space-3); }
.course-header-icon { display: grid; place-items: center; width: 44px; height: 44px; border-radius: var(--radius-sm); color: var(--primary-strong); }
.course-header-info { min-width: 0; }
.course-header-info h2 { margin: 0; font-size: var(--text-xl); font-weight: 800; line-height: 1.2; }
.course-header-meta { display: inline-flex; align-items: center; gap: 6px; margin: 4px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; flex-wrap: wrap; }
.meta-subject { color: var(--text-secondary); font-weight: 700; }
.visibility-badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.visibility-badge.private { background: #f1f5f9; color: #64748b; }
.visibility-badge.public { background: #ecfdf3; color: #067647; }
.course-desc { margin: 0; font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.55; }
.public-hint { margin: 0; display: inline-flex; align-items: center; gap: 2px; padding: 6px 12px; border-radius: var(--radius-md); background: var(--emerald-soft); color: var(--emerald); font-size: var(--text-xs); font-weight: 700; justify-self: start; }
.course-header-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.delete-btn-subtle { display: grid; place-items: center; width: 38px; height: 38px; border: 1px solid transparent; border-radius: var(--radius-sm); background: transparent; color: var(--line-strong); cursor: pointer; flex-shrink: 0; transition: all var(--ease-out); }
.delete-btn-subtle:hover:not(:disabled) { color: var(--rose); background: var(--rose-soft); border-color: var(--rose-border); }

.primary-button, .ghost-button { display: inline-flex; align-items: center; justify-content: center; }

/* ── Form Modal ── */
.form-overlay { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; padding: var(--space-4); background: rgba(15,23,42,0.4); backdrop-filter: blur(4px); }
.form-modal { position: relative; display: grid; gap: var(--space-3); width: 100%; max-width: 420px; padding: var(--space-5); border-radius: var(--radius-xl); background: var(--surface); box-shadow: var(--shadow-modal); }
.form-head { display: flex; align-items: center; justify-content: space-between; }
.form-head h3 { margin: 0; font-size: var(--text-lg); font-weight: 800; }
.form-close { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid var(--line-soft); border-radius: 50%; background: transparent; color: var(--text-muted); cursor: pointer; }
.form-error { margin: 0; padding: 8px 12px; border-radius: var(--radius-sm); background: var(--rose-soft); color: var(--rose); font-size: var(--text-sm); font-weight: 600; }
.field { display: grid; gap: 4px; }
.field-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-secondary); }
.field-input { min-height: 42px; padding: 10px 12px; border: 1.5px solid var(--line-strong); border-radius: var(--radius-sm); background: var(--surface-soft); font-size: var(--text-sm); color: var(--text-main); outline: none; }
.field-input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); background: var(--surface); }
.field-textarea { min-height: 70px; resize: vertical; }
.form-actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.btn-cancel, .btn-save { min-height: 44px; border-radius: var(--radius-md); font-weight: 700; font-size: var(--text-sm); cursor: pointer; }
.btn-cancel { border: 1.5px solid var(--line-strong); background: var(--surface); color: var(--text-muted); }
.btn-cancel:hover { background: var(--surface-soft); }
.btn-save { border: none; background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color: #fff; box-shadow: var(--shadow-primary); }
.btn-save:disabled { opacity: 0.55; }

@media (max-width: 420px) { .course-header-info h2 { font-size: var(--text-lg); } }
</style>
