<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  BarChart3,
  Bell,
  BookMarked,
  ChevronRight,
  Clock,
  HelpCircle,
  LogOut,
  Megaphone,
  ShieldCheck,
} from "@lucide/vue";

import { useStudyOverview } from "../composables/useStudyOverview";
import { releaseNotes } from "../data/releaseNotes";
import { useAuth } from "../stores/auth";
import Button from "../components/ui/button/Button.vue";
import Card from "../components/ui/card/Card.vue";
import CardContent from "../components/ui/card/CardContent.vue";

const router = useRouter();
const { user, logout } = useAuth();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();

const usernameText = computed(() => user.value?.username || "未登录");
const avatarChar = computed(() => usernameText.value.slice(0, 1).toUpperCase());
const roleText = computed(() => {
  const role = user.value?.role;
  if (role === "admin") return "管理员";
  if (role === "teacher") return "教师";
  return "普通用户";
});

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null || rate === undefined) return "--";
  return `${(rate * 100).toFixed(0)}%`;
});

const appVersion = computed(() => releaseNotes[0]?.version || "v1.0.0");

const overviewSummary = computed(() => ({
  today: stats.value.todayCount,
  total: stats.value.totalCount,
  accuracy: accuracyDisplay.value,
  recent: stats.value.recentCount7d,
}));

const serviceGrid = computed(() => [
  {
    label: "错题本",
    desc: stats.value.wrongCount !== null ? `${stats.value.wrongCount} 道待复盘` : "集中复盘",
    icon: BookMarked,
    color: "var(--rose)",
    to: "/wrongbook",
  },
  {
    label: "练习记录",
    desc: "查看答题历史",
    icon: Clock,
    color: "var(--amber)",
    to: { name: "practice-history", query: { from: "mine" } },
  },
  {
    label: "更新公告",
    desc: "最近修复内容",
    icon: Megaphone,
    color: "var(--primary)",
    to: { name: "announcements", query: { from: "mine" } },
  },
  {
    label: "使用提示",
    desc: "导入失败时先看这里",
    icon: HelpCircle,
    color: "var(--teal)",
    to: { name: "announcements", query: { from: "mine" } },
  },
]);

function goTo(target: string | Record<string, unknown>) {
  router.push(target);
}

function handleLogout() {
  logout();
  router.push({ name: "login" });
}

onMounted(() => fetchAll());
</script>

<template>
  <section class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-3">
        <div class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-500 to-violet-600 text-xl font-black text-white shadow-lg shadow-blue-500/20">
          {{ avatarChar }}
        </div>
        <div class="min-w-0">
          <h1 class="truncate text-2xl font-black text-slate-950">{{ usernameText }}</h1>
          <p class="mt-0.5 flex items-center gap-1.5 text-xs font-bold text-slate-500">
            <ShieldCheck :size="13" :stroke-width="2.5" />
            {{ roleText }}
          </p>
        </div>
      </div>
      <button class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white text-slate-600 shadow-sm" type="button" @click="goTo({ name: 'announcements', query: { from: 'mine' } })">
        <Bell :size="18" :stroke-width="2.4" />
      </button>
    </div>

    <Card class="overflow-hidden border-blue-100 bg-gradient-to-br from-blue-50 to-white">
      <button class="block w-full text-left" type="button" @click="goTo({ name: 'study-overview', query: { from: 'mine' } })">
        <CardContent class="flex items-center gap-3 p-3">
          <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-500/20">
            <BarChart3 :size="22" :stroke-width="2.4" />
          </span>
          <span class="min-w-0 flex-1">
            <strong class="block text-base font-black text-slate-950">学习概览</strong>
            <small class="mt-0.5 block truncate text-xs font-bold text-slate-500">
              今日 {{ overviewSummary.today ?? "--" }} 题 · 总计 {{ overviewSummary.total ?? "--" }} 题 · 正确率 {{ overviewSummary.accuracy }}
            </small>
          </span>
          <span class="hidden rounded-full bg-white px-2.5 py-0.5 text-[11px] font-black text-blue-600 shadow-sm sm:inline-flex">
            近 7 日 {{ overviewSummary.recent ?? "--" }} 题
          </span>
          <ChevronRight :size="16" :stroke-width="2.5" class="text-slate-400" />
        </CardContent>
      </button>
    </Card>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <section class="space-y-2">
      <div>
        <h2 class="text-xl font-black text-slate-950">学习服务</h2>
        <p class="mt-0.5 text-xs font-semibold text-slate-500">复盘、记录、公告和帮助</p>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="item in serviceGrid"
          :key="item.label"
          class="grid min-h-[84px] gap-1.5 rounded-2xl border border-slate-200 bg-white p-3 text-left shadow-sm transition active:scale-[0.99]"
          type="button"
          @click="goTo(item.to)"
        >
          <span class="grid h-8 w-8 place-items-center rounded-lg bg-slate-50" :style="{ color: item.color }">
            <component :is="item.icon" :size="19" :stroke-width="2.2" />
          </span>
          <span>
            <strong class="block text-sm font-black text-slate-950">{{ item.label }}</strong>
            <small class="mt-0.5 block text-[11px] font-bold text-slate-500">{{ item.desc }}</small>
          </span>
        </button>
      </div>
    </section>

    <Card class="border-slate-200 bg-white">
      <CardContent class="space-y-2 p-3">
        <div class="flex items-center justify-between text-xs font-bold text-slate-500">
          <span>学习宝</span>
          <span>{{ appVersion }}</span>
        </div>
        <Button variant="outline" class="w-full justify-start text-rose-600" @click="handleLogout">
          <LogOut :size="17" :stroke-width="2.3" />
          退出登录
        </Button>
      </CardContent>
    </Card>
  </section>
</template>
