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

const heatmapData = computed(() => {
  const today = Number(stats.value.todayCount || 0);
  const recent = Number(stats.value.recentCount7d || 0);
  const base = Math.max(Math.floor(Math.max(recent - today, 0) / 6), 0);
  const remainder = Math.max(recent - today - base * 5, 0);
  return [base, base, base, base, base, remainder, today];
});

function heatmapClass(count: number): string {
  if (count >= 10) return "bg-blue-600";
  if (count >= 5) return "bg-blue-400";
  if (count > 0) return "bg-blue-200";
  return "bg-slate-200";
}

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
  <section class="space-y-3">
    <!-- Hero -->
    <section class="rounded-3xl bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 p-3.5 text-white shadow-lg shadow-blue-500/20">
      <div class="flex items-center justify-between gap-3">
        <div class="min-w-0">
          <p class="text-[11px] font-semibold text-white/70">{{ dateText }}</p>
          <h1 class="mt-0.5 text-xl font-black leading-tight">
            {{ usernameText }}，开始复习吧
          </h1>
        </div>
        <button
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/15 active:bg-white/25"
          type="button"
          aria-label="更新公告"
          @click="router.push('/announcements?from=home')"
        >
          <Megaphone :size="16" :stroke-width="2.4" />
        </button>
      </div>

      <button
        class="mt-3 flex h-10 w-full items-center gap-2.5 rounded-2xl bg-white px-3.5 text-left text-[13px] font-bold text-slate-400"
        type="button"
        @click="router.push('/courses')"
      >
        <Search :size="16" :stroke-width="2.4" />
        <span>搜索题库、课程、题目</span>
      </button>

      <div class="mt-3 grid grid-cols-4 gap-1.5">
        <button
          v-for="item in heroActions"
          :key="item.label"
          class="relative grid min-h-[60px] place-items-center gap-0.5 rounded-xl border border-white/15 bg-white/10 px-1 py-2 text-center active:bg-white/20"
          type="button"
          @click="goTo(item.to)"
        >
          <span v-if="item.badge" class="absolute -top-1.5 right-1 rounded-full bg-amber-300 px-1 py-px text-[8px] font-black leading-tight text-blue-900">
            {{ item.badge }}
          </span>
          <component :is="item.icon" :size="19" :stroke-width="2.3" />
          <strong class="text-[11px] font-black leading-tight">{{ item.label }}</strong>
        </button>
      </div>
    </section>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <!-- 学习概览（紧凑） -->
    <Card class="overflow-hidden border-slate-200 bg-white shadow-sm">
      <button class="block w-full text-left" type="button" @click="goTo({ name: 'study-overview', query: { from: 'home' } })">
        <CardContent class="p-3">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-black text-slate-950">学习概览</h2>
            <ChevronRight :size="15" :stroke-width="2.5" class="text-slate-300" />
          </div>
          <div class="mt-2 grid grid-cols-4 gap-1.5">
            <div v-for="item in statCards" :key="item.label" class="rounded-lg bg-slate-50 px-1 py-1.5 text-center">
              <div class="flex items-baseline justify-center gap-0.5">
                <strong class="text-sm font-black text-slate-950">
                  {{ item.value !== null && item.value !== undefined && item.value !== "" ? item.value : "--" }}
                </strong>
                <small v-if="item.suffix" class="text-[11px] font-bold text-slate-400">{{ item.suffix }}</small>
              </div>
              <span class="mt-0.5 block text-[11px] font-bold text-slate-500">{{ item.label }}</span>
            </div>
          </div>
          <div class="mt-2 flex items-center gap-2 rounded-lg bg-slate-50 px-2 py-1.5">
            <span class="text-[11px] font-bold text-slate-400">7日</span>
            <div class="flex flex-1 gap-1">
              <span
                v-for="(count, index) in heatmapData"
                :key="index"
                class="h-4 flex-1 rounded"
                :class="heatmapClass(count)"
                :title="`${count} 题`"
              />
            </div>
          </div>
        </CardContent>
      </button>
    </Card>

    <section class="space-y-2">
      <div class="flex items-end justify-between gap-3">
        <div>
          <p class="text-xs font-bold text-slate-400">我的学习空间</p>
          <h2 class="text-2xl font-black text-slate-950">最近题库</h2>
        </div>
        <Button variant="ghost" size="sm" @click="router.push('/courses')">
          查看全部
          <ChevronRight :size="15" :stroke-width="2.5" />
        </Button>
      </div>

      <p v-if="coursesLoading" class="status-banner status-banner--info">正在加载题库...</p>
      <p v-if="coursesError" class="status-banner status-banner--error">{{ coursesError }}</p>

      <Card v-if="!coursesLoading && !coursesError && recentCourses.length === 0" class="border-dashed border-slate-200 bg-white">
        <CardContent class="grid place-items-center gap-3 py-8 text-center">
          <BookOpen :size="36" :stroke-width="1.7" class="text-slate-300" />
          <div>
            <strong class="text-base font-black text-slate-900">还没有可练习题库</strong>
            <p class="mt-1 text-sm font-semibold text-slate-500">导入资料后，这里会显示最近学习的题库。</p>
          </div>
          <div class="flex gap-2">
            <Button size="sm" @click="goTo('/import')">去导入</Button>
            <Button variant="outline" size="sm" @click="goTo('/courses')">浏览题库</Button>
          </div>
        </CardContent>
      </Card>

      <div v-if="recentCourses.length > 0" class="space-y-2">
        <Card v-for="course in recentCourses" :key="course.id" class="overflow-hidden border-slate-200 bg-white">
          <CardContent class="p-3">
            <div class="flex items-center gap-3">
              <button class="flex min-w-0 flex-1 items-center gap-3 text-left" type="button" @click="goTo(`/courses/${course.id}`)">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600">
                  <BookOpen :size="20" :stroke-width="2.2" />
                </span>
                <span class="min-w-0">
                  <strong class="block truncate text-sm font-black text-slate-950">{{ getCourseDisplayName(course) }}</strong>
                  <small class="mt-0.5 block text-xs font-semibold text-slate-500">
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
      <CardContent class="flex items-center justify-between gap-3 p-3">
        <div class="min-w-0">
          <p class="text-[11px] font-black text-blue-600">最新公告 {{ latestNote.version }}</p>
          <h3 class="mt-0.5 truncate text-sm font-black text-slate-950">{{ latestNote.title }}</h3>
        </div>
        <Button variant="outline" size="sm" @click="router.push('/announcements?from=home')">查看</Button>
      </CardContent>
    </Card>
  </section>
</template>
