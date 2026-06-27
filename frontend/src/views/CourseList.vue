<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import {
  BookOpen,
  ChevronRight,
  Globe,
  GraduationCap,
  Layers,
  Lock,
  Pencil,
  Play,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from "@lucide/vue";

import request, { getErrorMessage } from "../api/request";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import { useConfirmDialog } from "../stores/confirmDialog";
import type { Course } from "../types";
import Button from "../components/ui/button/Button.vue";
import Card from "../components/ui/card/Card.vue";
import CardContent from "../components/ui/card/CardContent.vue";

const router = useRouter();
const confirmDialog = useConfirmDialog();

const courses = ref<Course[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const deleteLoading = ref<number | null>(null);
const publishLoading = ref<number | null>(null);
const searchText = ref("");

const showForm = ref(false);
const editingCourse = ref<Course | null>(null);
const formLoading = ref(false);
const formError = ref("");
const form = reactive({ name: "", description: "", subject: "" });

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
  if (!total) return "创建题库或导入资料后，就可以开始练习。";
  if (searchText.value.trim()) return `已筛选 ${visible} / ${total} 个题库`;
  return `共 ${total} 个题库，选择一个开始练习。`;
});

const isEdit = computed(() => !!editingCourse.value);

function openCreate() {
  form.name = "";
  form.description = "";
  form.subject = "";
  editingCourse.value = null;
  formError.value = "";
  showForm.value = true;
}

function openEdit(course: Course) {
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

    if (editingCourse.value) {
      const { data } = await request.patch<Course>(`/courses/${editingCourse.value.id}`, payload);
      Object.assign(editingCourse.value, data);
    } else {
      const { data } = await request.post<Course>("/courses/", { ...payload, visibility: "private" });
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
    const { data } = await request.get<Course[] | { items: Course[] }>("/courses/mine");
    courses.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取题库失败");
  } finally {
    loading.value = false;
  }
}

async function deleteCourse(course: Course) {
  const confirmed = await confirmDialog.confirm({
    title: "删除题库",
    message: `确定删除「${getCourseDisplayName(course)}」吗？\n其中 ${course.question_count ?? 0} 道题会一起移除。`,
    confirmText: "删除",
    cancelText: "取消",
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

async function togglePublish(course: Course) {
  publishLoading.value = course.id;
  errorMessage.value = "";

  try {
    if (course.visibility === "public") {
      const { data } = await request.post<Course>(`/courses/${course.id}/unpublish`);
      course.visibility = data.visibility || "private";
    } else {
      const { data } = await request.post<Course>(`/courses/${course.id}/publish`);
      course.visibility = data.visibility || "public";
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "操作失败");
  } finally {
    publishLoading.value = null;
  }
}

function goToPractice(course: Course) {
  if (!isPracticeReadyCourse(course)) return;
  router.push(`/courses/${course.id}/practice`);
}

onMounted(fetchCourses);
</script>

<template>
  <section class="space-y-4 pb-24">
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-sm font-bold text-slate-400">选择课程开始练习</p>
        <h1 class="mt-1 text-4xl font-black text-slate-950">我的题库</h1>
        <p class="mt-2 text-sm font-semibold text-slate-500">{{ courseSummary }}</p>
      </div>
      <div class="flex shrink-0 gap-2">
        <Button variant="outline" :disabled="loading" @click="fetchCourses">刷新</Button>
        <Button @click="openCreate">
          <Plus :size="16" :stroke-width="2.5" />
          创建题库
        </Button>
      </div>
    </div>

    <p v-if="loading" class="status-banner status-banner--info">题库加载中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <Card v-if="courses.length > 0" class="border-slate-200 bg-white">
      <CardContent class="flex items-center gap-3 p-3">
        <Search :size="19" :stroke-width="2.4" class="text-slate-400" />
        <input
          v-model="searchText"
          class="min-h-10 min-w-0 flex-1 border-0 bg-transparent text-base font-bold text-slate-800 outline-none placeholder:text-slate-400"
          type="search"
          placeholder="搜索题库、科目或描述"
        />
        <button v-if="searchText" class="grid h-8 w-8 place-items-center rounded-full bg-slate-100 text-slate-500" type="button" @click="clearSearch">
          <X :size="15" :stroke-width="2.6" />
        </button>
      </CardContent>
    </Card>

    <Card v-if="!loading && courses.length === 0 && !errorMessage" class="border-dashed border-slate-200 bg-white">
      <CardContent class="grid place-items-center gap-4 py-12 text-center">
        <GraduationCap :size="48" :stroke-width="1.5" class="text-slate-300" />
        <div>
          <strong class="text-lg font-black text-slate-900">还没有题库</strong>
          <p class="mt-1 text-sm font-semibold text-slate-500">创建一门课程，或先去导入题目。</p>
        </div>
        <div class="flex gap-2">
          <Button @click="openCreate">
            <Plus :size="16" :stroke-width="2.5" />
            创建题库
          </Button>
          <Button variant="outline" @click="router.push('/import')">
            <Sparkles :size="16" :stroke-width="2.5" />
            去导入
          </Button>
        </div>
      </CardContent>
    </Card>

    <Card v-if="!loading && courses.length > 0 && filteredCourses.length === 0 && !errorMessage" class="border-dashed border-slate-200 bg-white">
      <CardContent class="grid place-items-center gap-4 py-10 text-center">
        <Search :size="44" :stroke-width="1.5" class="text-slate-300" />
        <div>
          <strong class="text-lg font-black text-slate-900">没有找到匹配题库</strong>
          <p class="mt-1 text-sm font-semibold text-slate-500">换个关键词，或者清空搜索查看全部。</p>
        </div>
        <Button variant="outline" @click="clearSearch">清空搜索</Button>
      </CardContent>
    </Card>

    <div class="space-y-3">
      <Card v-for="course in filteredCourses" :key="course.id" class="overflow-hidden border-slate-200 bg-white">
        <CardContent class="p-4">
          <button class="flex w-full items-center gap-3 text-left" type="button" @click="router.push(`/courses/${course.id}`)">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-50 text-blue-600">
              <BookOpen :size="22" :stroke-width="2.2" />
            </span>
            <span class="min-w-0 flex-1">
              <strong class="block truncate text-lg font-black text-slate-950">{{ getCourseDisplayName(course) }}</strong>
              <small class="mt-1 flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-500">
                <span class="inline-flex items-center gap-1"><Layers :size="13" />{{ course.question_count ?? 0 }} 道题</span>
                <span class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                  <Lock v-if="course.visibility === 'private'" :size="12" />
                  <Globe v-else :size="12" />
                  {{ course.visibility === "public" ? "已公开" : "私有" }}
                </span>
              </small>
            </span>
            <ChevronRight :size="20" :stroke-width="2.5" class="text-slate-300" />
          </button>

          <div class="mt-4 grid grid-cols-[1fr_1.4fr_auto_auto_auto] gap-2 border-t border-slate-100 pt-3">
            <Button variant="outline" size="sm" @click="router.push(`/courses/${course.id}`)">查看题目</Button>
            <Button size="sm" :disabled="!isPracticeReadyCourse(course)" @click="goToPractice(course)">
              <Play :size="14" :stroke-width="2.6" />
              {{ isPracticeReadyCourse(course) ? "开始练习" : "暂无题目" }}
            </Button>
            <button class="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700" type="button" title="编辑" @click.stop="openEdit(course)">
              <Pencil :size="15" :stroke-width="2.5" />
            </button>
            <button
              class="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              type="button"
              :title="course.visibility === 'public' ? '撤回公开' : '发布到公共题库'"
              :disabled="publishLoading === course.id"
              @click.stop="togglePublish(course)"
            >
              <Globe v-if="course.visibility !== 'public'" :size="15" :stroke-width="2.5" />
              <Lock v-else :size="15" :stroke-width="2.5" />
            </button>
            <button
              class="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"
              type="button"
              title="删除"
              :disabled="deleteLoading === course.id"
              @click.stop="deleteCourse(course)"
            >
              <Trash2 :size="15" :stroke-width="2.5" />
            </button>
          </div>
        </CardContent>
      </Card>
    </div>

    <Button v-if="courses.length > 0 && filteredCourses.length > 0" variant="outline" class="w-full" @click="router.push('/public-library')">
      <Globe :size="17" :stroke-width="2.5" />
      浏览公共题库
    </Button>

    <div v-if="showForm" class="fixed inset-0 z-[100] grid place-items-center bg-slate-950/40 p-4 backdrop-blur-sm" @click.self="closeForm">
      <Card class="w-full max-w-[430px] border-slate-200 bg-white shadow-2xl">
        <CardContent class="space-y-4 p-5">
          <div class="flex items-center justify-between">
            <h3 class="text-xl font-black text-slate-950">{{ isEdit ? "编辑题库" : "创建题库" }}</h3>
            <button class="grid h-9 w-9 place-items-center rounded-full bg-slate-100 text-slate-500" type="button" @click="closeForm">
              <X :size="18" :stroke-width="2.5" />
            </button>
          </div>

          <p v-if="formError" class="status-banner status-banner--error">{{ formError }}</p>

          <label class="grid gap-1">
            <span class="text-sm font-black text-slate-600">题库名称</span>
            <input v-model="form.name" class="min-h-12 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-base font-bold outline-none focus:border-blue-400" type="text" placeholder="如：Java 期末复习" />
          </label>
          <label class="grid gap-1">
            <span class="text-sm font-black text-slate-600">科目（可选）</span>
            <input v-model="form.subject" class="min-h-12 rounded-2xl border border-slate-200 bg-slate-50 px-4 text-base font-bold outline-none focus:border-blue-400" type="text" placeholder="如：Java" />
          </label>
          <label class="grid gap-1">
            <span class="text-sm font-black text-slate-600">描述（可选）</span>
            <textarea v-model="form.description" class="min-h-20 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-base font-bold outline-none focus:border-blue-400" placeholder="简单描述题库内容" />
          </label>

          <div class="grid grid-cols-2 gap-2">
            <Button variant="outline" @click="closeForm">取消</Button>
            <Button :disabled="formLoading" @click="handleSave">
              {{ formLoading ? "保存中..." : isEdit ? "保存修改" : "创建" }}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </section>
</template>
