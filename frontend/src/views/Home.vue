<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  BookOpen,
  ChevronRight,
  ClipboardList,
  FileUp,
  Megaphone,
  Search,
  Target,
  TrendingUp,
} from "@lucide/vue";

import { getMyCourses } from "../api/courses";
import { getErrorMessage } from "../api/request";
import { useStudyOverview } from "../composables/useStudyOverview";
import { releaseNotes } from "../data/releaseNotes";
import { useAuth } from "../stores/auth";
import type { Course } from "../types";
import { getCourseDisplayName, isPracticeReadyCourse } from "../utils/course";
import Button from "../components/ui/button/Button.vue";
import Card from "../components/ui/card/Card.vue";
import CardContent from "../components/ui/card/CardContent.vue";
import CardHeader from "../components/ui/card/CardHeader.vue";
import CardTitle from "../components/ui/card/CardTitle.vue";

const router = useRouter();
const { user } = useAuth();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();

const courses = ref<Course[]>([]);
const coursesLoading = ref(false);
const coursesError = ref("");

const usernameText = computed(() => user.value?.username || "同学");

const dateText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(new Date()),
);

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null || rate === undefined) return "--";
  return `${(rate * 100).toFixed(0)}%`;
});

const statCards = computed(() => [
  { label: "今日已刷", value: stats.value.todayCount, suffix: "题" },
  { label: "总刷题", value: stats.value.totalCount, suffix: "题" },
  { label: "正确率", value: accuracyDisplay.value, suffix: "" },
  { label: "近 7 日", value: stats.value.recentCount7d, suffix: "题" },
]);

const latestNote = computed(() => releaseNotes[0] || null);

const recentCourses = computed(() => {
  const seen = new Set<number | string>();
  return [...courses.value]
    .filter((course) => {
      if (!isPracticeReadyCourse(course) || seen.has(course.id)) return false;
      seen.add(course.id);
      return true;
    })
    .sort((a, b) => {
      const aTime = new Date(a.last_practiced_at || a.created_at || 0).getTime();
      const bTime = new Date(b.last_practiced_at || b.created_at || 0).getTime();
      return bTime - aTime;
    })
    .slice(0, 3);
});

const heroActions = [
  {
    label: "AI 导入",
    desc: "上传 Word/PPT，自动整理题库",
    icon: FileUp,
    to: "/import",
    badge: "推荐",
  },
  {
    label: "开始练习",
    desc: "先选题库，再进入专业练习",
    icon: ClipboardList,
    to: "/practice",
  },
  {
    label: "正式考试",
    desc: "选择考试并提交成绩",
    icon: Target,
    to: "/exams",
  },
  {
    label: "学习概览",
    desc: "查看今日进度和正确率",
    icon: TrendingUp,
    to: { name: "study-overview", query: { from: "home" } },
  },
];

function goTo(target: string | Record<string, unknown>) {
  router.push(target);
}

function formatCourseDate(course: Course) {
  const raw = course.last_practiced_at || course.created_at;
  if (!raw) return "暂无记录";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return "暂无记录";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" }).format(date);
}

async function fetchRecentCourses() {
  coursesLoading.value = true;
  coursesError.value = "";

  try {
    courses.value = await getMyCourses();
  } catch (error) {
    coursesError.value = getErrorMessage(error, "题库加载失败，请稍后重试。");
  } finally {
    coursesLoading.value = false;
  }
}

onMounted(() => {
  fetchAll();
  fetchRecentCourses();
});
</script>

<template>
  <section class="space-y-5 pb-24">
    <section class="rounded-[28px] bg-gradient-to-br from-blue-500 via-blue-600 to-blue-800 p-5 text-white shadow-xl shadow-blue-500/20">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-sm font-semibold text-white/75">{{ dateText }}</p>
          <h1 class="mt-2 text-4xl font-black leading-tight tracking-normal">
            {{ usernameText }}，开始复习吧
          </h1>
        </div>
        <button
          class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white/15 text-white backdrop-blur"
          type="button"
          aria-label="更新公告"
          @click="router.push('/announcements?from=home')"
        >
          <Megaphone :size="20" :stroke-width="2.4" />
        </button>
      </div>

      <button
        class="mt-5 flex min-h-14 w-full items-center gap-3 rounded-full bg-white px-5 text-left text-base font-bold text-slate-500 shadow-sm"
        type="button"
        @click="router.push('/courses')"
      >
        <Search :size="21" :stroke-width="2.4" />
        <span>搜索题库、课程、题目</span>
      </button>

      <div class="mt-5 grid grid-cols-4 gap-3">
        <button
          v-for="item in heroActions"
          :key="item.label"
          class="relative grid min-h-24 place-items-center gap-1 rounded-2xl border border-white/20 bg-white/12 px-2 py-3 text-center backdrop-blur transition active:scale-[0.98]"
          type="button"
          @click="goTo(item.to)"
        >
          <span v-if="item.badge" class="absolute -top-2 right-2 rounded-full bg-amber-300 px-2 py-0.5 text-[10px] font-black text-blue-900">
            {{ item.badge }}
          </span>
          <component :is="item.icon" :size="24" :stroke-width="2.25" />
          <strong class="text-sm font-black leading-tight">{{ item.label }}</strong>
          <small class="hidden text-[10px] leading-tight text-white/70 sm:block">{{ item.desc }}</small>
        </button>
      </div>
    </section>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <Card class="overflow-hidden border-slate-200 bg-white">
      <button class="block w-full text-left" type="button" @click="goTo({ name: 'study-overview', query: { from: 'home' } })">
        <CardHeader class="flex flex-row items-center justify-between gap-4">
          <div>
            <p class="text-sm font-bold text-slate-400">我的学习空间</p>
            <CardTitle class="mt-1 text-3xl text-slate-950">学习概览</CardTitle>
          </div>
          <ChevronRight :size="22" :stroke-width="2.5" class="text-slate-400" />
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-4 gap-2">
            <div v-for="item in statCards" :key="item.label" class="rounded-2xl bg-slate-50 px-2 py-3 text-center">
              <strong class="block text-lg font-black text-slate-950">
                {{ item.value !== null && item.value !== undefined && item.value !== "" ? item.value : "--" }}
                <small v-if="item.suffix" class="text-xs font-bold text-slate-500">{{ item.suffix }}</small>
              </strong>
              <span class="mt-1 block text-xs font-bold text-slate-500">{{ item.label }}</span>
            </div>
          </div>
        </CardContent>
      </button>
    </Card>

    <section class="space-y-3">
      <div class="flex items-end justify-between gap-3">
        <div>
          <p class="text-sm font-bold text-slate-400">我的学习空间</p>
          <h2 class="text-3xl font-black text-slate-950">最近题库</h2>
        </div>
        <Button variant="ghost" size="sm" @click="router.push('/courses')">
          查看全部
          <ChevronRight :size="15" :stroke-width="2.5" />
        </Button>
      </div>

      <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
      <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

      <Card v-if="!coursesLoading && !coursesError && recentCourses.length === 0" class="border-dashed border-slate-200 bg-white">
        <CardContent class="grid place-items-center gap-3 py-10 text-center">
          <BookOpen :size="42" :stroke-width="1.7" class="text-slate-300" />
          <div>
            <strong class="text-lg font-black text-slate-900">还没有可练习题库</strong>
            <p class="mt-1 text-sm font-semibold text-slate-500">导入资料后，这里会显示最近学习的题库。</p>
          </div>
          <div class="flex gap-2">
            <Button size="sm" @click="goTo('/import')">去导入</Button>
            <Button variant="outline" size="sm" @click="goTo('/courses')">浏览题库</Button>
          </div>
        </CardContent>
      </Card>

      <div v-if="recentCourses.length > 0" class="space-y-3">
        <Card v-for="course in recentCourses" :key="course.id" class="overflow-hidden border-slate-200 bg-white">
          <CardContent class="p-4">
            <div class="flex items-center gap-3">
              <button class="flex min-w-0 flex-1 items-center gap-3 text-left" type="button" @click="goTo(`/courses/${course.id}`)">
                <span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-blue-50 text-blue-600">
                  <BookOpen :size="22" :stroke-width="2.2" />
                </span>
                <span class="min-w-0">
                  <strong class="block truncate text-base font-black text-slate-950">{{ getCourseDisplayName(course) }}</strong>
                  <small class="mt-1 block text-sm font-semibold text-slate-500">
                    {{ course.question_count ?? 0 }} 题 · {{ course.visibility === "public" ? "公开" : "私有" }} · {{ formatCourseDate(course) }}
                  </small>
                </span>
              </button>
              <Button size="sm" @click="goTo(`/courses/${course.id}/practice`)">练习</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>

    <Card v-if="latestNote" class="border-blue-100 bg-blue-50/70">
      <CardContent class="flex items-center justify-between gap-3 p-4">
        <div class="min-w-0">
          <p class="text-xs font-black text-blue-600">最新公告 {{ latestNote.version }}</p>
          <h3 class="mt-1 truncate text-base font-black text-slate-950">{{ latestNote.title }}</h3>
        </div>
        <Button variant="outline" size="sm" @click="router.push('/announcements?from=home')">查看</Button>
      </CardContent>
    </Card>
  </section>
</template>
