<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import {
  BookOpen,
  GraduationCap,
  ChevronRight,
  Layers,
  Globe,
  Lock,
  Play,
  Sparkles,
  Trash2,
  Plus,
  Pencil,
  Search,
  X,
} from "@lucide/vue";
import { useConfirmDialog } from "../stores/confirmDialog";

const router = useRouter();
const confirmDialog = useConfirmDialog();
const courses = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const deleteLoading = ref(null);
const publishLoading = ref(null);
const searchText = ref("");

const showForm = ref(false);
const editingCourse = ref(null);
const formLoading = ref(false);
const formError = ref("");
const form = reactive({ name: "", description: "", subject: "" });

const cardColors = [
  { bar: "#3b82f6" },
  { bar: "#0d9488" },
  { bar: "#7c3aed" },
  { bar: "#d97706" },
  { bar: "#e11d48" },
];

const isEdit = () => !!editingCourse.value;

const filteredCourses = computed(() => {
  const keyword = searchText.value.trim().toLowerCase();
  if (!keyword) return courses.value;

  return courses.value.filter((course) => {
    const fields = [course.name, course.subject, course.description, course.visibility];
    return fields.some((field) => String(field || "").toLowerCase().includes(keyword));
  });
});

const courseSummary = computed(() => {
  const total = courses.value.length;
  const visible = filteredCourses.value.length;
  if (!total) return "管理课程，然后开始练习。";
  if (searchText.value.trim()) return `已筛选 ${visible} / ${total} 个题库`;
  return `共 ${total} 个题库，选择一门开始练习。`;
});

function getCardColor(index) {
  return cardColors[index % cardColors.length];
}

function openCreate() {
  form.name = "";
  form.description = "";
  form.subject = "";
  editingCourse.value = null;
  formError.value = "";
  showForm.value = true;
}

function openEdit(course) {
  form.name = course.name;
  form.description = course.description || "";
  form.subject = course.subject || "";
  editingCourse.value = course;
  formError.value = "";
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
}

function clearSearch() {
  searchText.value = "";
}

async function handleSave() {
  if (!form.name.trim()) {
    formError.value = "课程名称不能为空";
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

    if (editingCourse.value) {
      const { data } = await request.patch(`/courses/${editingCourse.value.id}`, payload);
      Object.assign(editingCourse.value, data);
    } else {
      const { data } = await request.post("/courses/", { ...payload, visibility: "private" });
      courses.value.unshift(data);
    }

    closeForm();
  } catch (error) {
    formError.value = getErrorMessage(error, "保存失败");
  } finally {
    formLoading.value = false;
  }
}

async function fetchCourses() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const { data } = await request.get("/courses/mine");
    courses.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取课程失败");
  } finally {
    loading.value = false;
  }
}

async function deleteCourse(course) {
  const confirmed = await confirmDialog.confirm({
    title: "删除课程",
    message: `确定删除“${course.name}”吗？\n共 ${course.question_count ?? 0} 道题会一起移除。`,
    confirmText: "删除",
    tone: "danger",
  });

  if (!confirmed) return;

  deleteLoading.value = course.id;
  errorMessage.value = "";

  try {
    await request.delete(`/courses/${course.id}`);
    courses.value = courses.value.filter((item) => item.id !== course.id);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "删除失败");
  } finally {
    deleteLoading.value = null;
  }
}

async function togglePublish(course) {
  publishLoading.value = course.id;
  errorMessage.value = "";

  try {
    if (course.visibility === "public") {
      const { data } = await request.post(`/courses/${course.id}/unpublish`);
      course.visibility = data.visibility || "private";
    } else {
      const { data } = await request.post(`/courses/${course.id}/publish`);
      course.visibility = data.visibility || "public";
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "操作失败");
  } finally {
    publishLoading.value = null;
  }
}

function goToPractice(course) {
  if (!isPracticeReadyCourse(course)) return;
  router.push(`/courses/${course.id}/practice`);
}

onMounted(fetchCourses);
</script>

<template>
  <section class="stack">
    <div class="section-heading row-heading">
      <div>
        <h2>我的题库</h2>
        <p>{{ courseSummary }}</p>
      </div>
      <div class="heading-actions">
        <button class="ghost-button" type="button" :disabled="loading" @click="fetchCourses">刷新</button>
        <button class="primary-button" type="button" @click="openCreate">
          <Plus :size="16" :stroke-width="2.5" style="margin-right:4px" />创建课程
        </button>
      </div>
    </div>

    <p v-if="loading" class="status-banner status-banner--info">加载中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <div v-if="courses.length > 0" class="course-search-panel surface-card">
      <Search :size="18" :stroke-width="2.3" color="var(--text-placeholder)" />
      <input
        v-model="searchText"
        class="course-search-input"
        type="search"
        placeholder="搜索题库、科目或描述"
      />
      <button v-if="searchText" class="mini-btn" type="button" title="清空搜索" @click="clearSearch">
        <X :size="14" :stroke-width="2.5" />
      </button>
    </div>

    <div v-if="!loading && courses.length === 0 && !errorMessage" class="status-panel status-panel--empty">
      <GraduationCap :size="44" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p class="status-panel__title">还没有课程</p>
      <p class="status-panel__text">创建一门，或先去导入。</p>
      <div class="status-actions">
        <button class="primary-button" type="button" @click="openCreate">
          <Plus :size="16" :stroke-width="2.5" style="margin-right:4px" />创建课程
        </button>
        <button class="ghost-button" type="button" @click="router.push('/import')">
          <Sparkles :size="16" :stroke-width="2.5" style="margin-right:4px" />去导入
        </button>
      </div>
    </div>

    <div
      v-if="!loading && courses.length > 0 && filteredCourses.length === 0 && !errorMessage"
      class="status-panel status-panel--empty"
    >
      <Search :size="42" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p class="status-panel__title">没有找到匹配题库</p>
      <p class="status-panel__text">换个关键词试试，或者清空搜索查看全部题库。</p>
      <div class="status-actions">
        <button class="ghost-button" type="button" @click="clearSearch">清空搜索</button>
        <button class="primary-button" type="button" @click="router.push('/import')">
          <Sparkles :size="16" :stroke-width="2.5" style="margin-right:4px" />去导入
        </button>
      </div>
    </div>

    <div
      v-for="(course, index) in filteredCourses"
      :key="course.id"
      class="course-card surface-card"
      :style="{ '--card-accent': getCardColor(index).bar }"
    >
      <div class="course-card-body" @click="router.push(`/courses/${course.id}`)">
        <div class="course-icon" :style="{ background: 'var(--primary-soft)', color: 'var(--primary-strong)' }">
          <BookOpen :size="20" :stroke-width="2" />
        </div>
        <div class="course-info">
          <h3>{{ getCourseDisplayName(course) }}</h3>
          <p class="course-meta">
            <Layers :size="13" :stroke-width="2" />
            <span>{{ course.question_count ?? 0 }} 道题</span>
            <span class="visibility-badge" :class="course.visibility">
              <Lock v-if="course.visibility === 'private'" :size="11" :stroke-width="2.5" />
              <Globe v-else :size="11" :stroke-width="2.5" />
              {{ course.visibility === "public" ? "已公开" : "私有" }}
            </span>
          </p>
        </div>
        <ChevronRight class="course-chevron" :size="18" :stroke-width="2.5" color="var(--text-placeholder)" />
      </div>

      <div class="course-actions">
        <button class="ghost-button course-action-btn" type="button" @click="router.push(`/courses/${course.id}`)">
          查看题目
        </button>
        <button
          class="primary-button course-action-btn course-start-btn"
          type="button"
          :disabled="!isPracticeReadyCourse(course)"
          @click="goToPractice(course)"
        >
          <Play :size="14" :stroke-width="2.5" style="margin-right:3px" />
          {{ isPracticeReadyCourse(course) ? "开始练习" : "暂无题目" }}
        </button>
        <button class="mini-btn" type="button" title="编辑" @click.stop="openEdit(course)">
          <Pencil :size="13" :stroke-width="2.5" />
        </button>
        <button
          class="mini-btn"
          type="button"
          :title="course.visibility === 'public' ? '撤回公开' : '发布到公共题库'"
          :disabled="publishLoading === course.id"
          @click.stop="togglePublish(course)"
        >
          <Globe v-if="course.visibility !== 'public'" :size="13" :stroke-width="2.5" />
          <Lock v-else :size="13" :stroke-width="2.5" />
        </button>
        <button
          class="mini-btn mini-btn--danger"
          type="button"
          title="删除"
          :disabled="deleteLoading === course.id"
          @click.stop="deleteCourse(course)"
        >
          <Trash2 :size="13" :stroke-width="2.5" />
        </button>
      </div>
    </div>

    <div v-if="courses.length > 0 && filteredCourses.length > 0" class="public-library-link">
      <button class="ghost-button full-button" type="button" @click="router.push('/public-library')">
        <Globe :size="16" :stroke-width="2.5" style="margin-right:6px" />浏览公共题库
      </button>
    </div>

    <div v-if="showForm" class="form-overlay" @click.self="closeForm">
      <div class="form-modal surface-card">
        <div class="form-head">
          <h3>{{ isEdit() ? "编辑课程" : "创建课程" }}</h3>
          <button class="form-close icon-button" type="button" @click="closeForm">
            <X :size="18" :stroke-width="2.5" />
          </button>
        </div>

        <p v-if="formError" class="status-banner status-banner--error form-error">{{ formError }}</p>

        <label class="field">
          <span class="field-label">课程名称</span>
          <input v-model="form.name" class="field-input" type="text" placeholder="如：高等数学" />
        </label>
        <label class="field">
          <span class="field-label">科目（可选）</span>
          <input v-model="form.subject" class="field-input" type="text" placeholder="如：数学" />
        </label>
        <label class="field">
          <span class="field-label">描述（可选）</span>
          <textarea v-model="form.description" class="field-input field-textarea" placeholder="简单描述课程内容" />
        </label>

        <div class="form-actions">
          <button class="btn-cancel" type="button" @click="closeForm">取消</button>
          <button class="btn-save" type="button" :disabled="formLoading" @click="handleSave">
            {{ formLoading ? "保存中..." : isEdit() ? "保存修改" : "创建" }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.heading-actions { display: flex; gap: var(--space-2); flex-shrink: 0; }

.course-search-panel {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-2);
  min-height: 48px;
  padding: 0 var(--space-3);
  border-color: var(--line-soft);
  box-shadow: none;
}

.course-search-input {
  width: 100%;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-main);
  font-size: var(--text-sm);
  font-weight: 650;
}

.course-search-input::placeholder {
  color: var(--text-placeholder);
  font-weight: 600;
}

.course-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  position: relative;
  overflow: hidden;
}

.course-card::before {
  content: "";
  position: absolute;
  top: 12px;
  left: 0;
  width: 4px;
  height: calc(100% - 24px);
  border-radius: 0 4px 4px 0;
  background: var(--card-accent);
  opacity: 0.6;
}

.course-card-body {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  padding-left: var(--space-1);
}

.course-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.course-info { min-width: 0; }
.course-info h3 { margin: 0; font-size: var(--text-sm); font-weight: 700; line-height: 1.3; color: var(--text-main); }
.course-meta { display: inline-flex; align-items: center; gap: 6px; margin: 4px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; flex-wrap: wrap; }
.visibility-badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 7px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.visibility-badge.private { background: #f1f5f9; color: #64748b; }
.visibility-badge.public { background: var(--emerald-soft); color: var(--emerald); }
.course-chevron { flex-shrink: 0; }

.course-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: var(--space-2);
  border-top: 1px solid var(--line-soft);
}

.course-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  flex: 1;
}

.course-start-btn { flex: 1.5; }

.mini-btn {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-placeholder);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ease-out);
}

.mini-btn:hover { background: var(--surface-soft); color: var(--text-main); border-color: var(--line-soft); }
.mini-btn--danger:hover { color: var(--rose); background: var(--rose-soft); border-color: var(--rose-border); }
.mini-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.public-library-link { padding-top: var(--space-1); }
.public-library-link button { display: inline-flex; align-items: center; justify-content: center; }

.form-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
}

.form-modal {
  position: relative;
  display: grid;
  gap: var(--space-3);
  width: 100%;
  max-width: 420px;
  padding: var(--space-5);
  box-shadow: var(--shadow-modal);
}

.form-head { display: flex; align-items: center; justify-content: space-between; }
.form-head h3 { margin: 0; font-size: var(--text-lg); font-weight: 800; }
.form-close { background: transparent; }
.form-error { margin: 0; }

.field { display: grid; gap: 4px; }
.field-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-secondary); }
.field-input { min-height: 42px; padding: 10px 12px; border: 1.5px solid var(--line-strong); border-radius: var(--radius-sm); background: var(--surface-soft); font-size: var(--text-sm); color: var(--text-main); outline: none; }
.field-input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); background: var(--surface); }
.field-textarea { min-height: 70px; resize: vertical; }

.form-actions { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.btn-cancel { min-height: 44px; border: 1.5px solid var(--line-strong); border-radius: var(--radius-md); background: var(--surface); color: var(--text-muted); font-weight: 700; font-size: var(--text-sm); cursor: pointer; }
.btn-cancel:hover { background: var(--surface-soft); }
.btn-save { min-height: 44px; border: none; border-radius: var(--radius-md); background: linear-gradient(135deg, var(--primary), var(--primary-strong)); color: #fff; font-weight: 800; font-size: var(--text-sm); cursor: pointer; box-shadow: var(--shadow-primary); }
.btn-save:hover:not(:disabled) { transform: translateY(-1px); }
.btn-save:disabled { opacity: 0.55; }

.ghost-button, .primary-button { display: inline-flex; align-items: center; justify-content: center; }

@media (max-width: 420px) {
  .course-card { padding: var(--space-3); }
  .course-action-btn { min-height: 32px; padding: 6px 8px; font-size: 10px; }
  .mini-btn { width: 28px; height: 28px; }
}
</style>
