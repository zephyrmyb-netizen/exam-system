<script setup lang="ts">
import { computed, onMounted } from "vue";
import type { RouteLocationRaw } from "vue-router";
import {
  Bookmark,
  BookMarked,
  CircleHelp,
  ChevronRight,
  Clock,
  LogOut,
  MessageCircle,
  Megaphone,
  Palette,
  Settings2,
  ShieldCheck,
} from "@lucide/vue";

import StatGrid from "../components/ui/StatGrid.vue";
import { useStudyOverview } from "../composables/useStudyOverview";
import { useAppNavigation } from "../composables/useAppNavigation";
import { releaseNotes } from "../data/releaseNotes";
import { useAuth } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const { replaceTo } = useAppNavigation();
const { user, logout } = useAuth();
const theme = useThemeStore();
const { stats, streak, streakAvailable, loading, errorMessage, fetchAll } = useStudyOverview();

const usernameText = computed(() => user.value?.username || "未登录");
const avatarChar = computed(() => usernameText.value.slice(0, 1).toUpperCase());
const roleText = computed(() => {
  if (!user.value) return "未登录";
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

const mineStatItems = computed(() => [
  { label: "累计题数", value: stats.value.totalCount, tone: "primary" as const },
  { label: "正确率", value: accuracyDisplay.value },
  {
    label: "连续打卡",
    value: streakAvailable.value === true ? `${streak.value.current_streak}天` : null,
    dataKey: "streak",
  },
  { label: "徽章", value: null, dataKey: "badges" },
]);

const isDarkMode = computed(() => theme.mode === "dark");

const quickItems = computed(() => [
  {
    label: "错题本",
    desc: stats.value.wrongCount !== null ? `${stats.value.wrongCount} 题待复习` : "集中复盘",
    icon: BookMarked,
    to: { name: "wrongbook", query: { from: "mine" } },
    tone: "rose",
  },
  { label: "收藏题目", desc: "重点题目", icon: Bookmark, to: { name: "bookmarks", query: { from: "mine" } }, tone: "amber" },
  { label: "练习记录", desc: "查看学习轨迹", icon: Clock, to: { name: "practice-history", query: { from: "mine" } }, tone: "blue" },
  { label: "AI 对话", desc: "智能复习助手", icon: MessageCircle, to: { name: "chat", query: { from: "mine" } }, tone: "emerald" },
]);

function toggleTheme() {
  theme.setMode(isDarkMode.value ? "light" : "dark");
}

function goTo(target: RouteLocationRaw) {
  replaceTo(target);
}

function handleLogout() {
  logout();
  replaceTo({ name: "login" });
}

onMounted(() => fetchAll());
</script>

<template>
  <section class="mine-page" data-reference-page="mine">
    <div class="profile-card profile-card--centered fade-up d1">
      <div class="profile-head">
        <div class="avatar-wrap">
          <div class="avatar-ring"></div>
          <div class="avatar">{{ avatarChar }}</div>
        </div>
        <div class="profile-info">
          <h3 class="profile-name">{{ usernameText }}</h3>
          <span class="profile-tag">
            <ShieldCheck :size="11" :stroke-width="2.5" />
            {{ roleText }}
          </span>
        </div>
      </div>
      <div class="profile-level">
        <span>学习等级</span>
        <span>--</span>
      </div>
      <div class="profile-level__track" aria-label="学习等级数据暂未开放"><i></i></div>
    </div>

    <button
      class="fade-up d2 stat-link"
      type="button"
      @click="goTo({ name: 'study-overview', query: { from: 'mine' } })"
    >
      <StatGrid
        class="stat-grid-4"
        label="我的学习统计"
        :items="mineStatItems"
      />
    </button>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <div class="section-head fade-up d3">
      <h3 class="section-title">快捷入口</h3>
    </div>
    <nav class="mine-quick-grid fade-up d3">
      <button
        v-for="item in quickItems"
        :key="item.label"
        class="mine-quick"
        type="button"
        @click="goTo(item.to)"
      >
        <span class="mine-quick__icon" :class="`mine-quick__icon--${item.tone}`"><component :is="item.icon" :size="20" :stroke-width="2.2" /></span>
        <strong>{{ item.label }}</strong>
        <small>{{ item.desc }}</small>
      </button>
    </nav>

    <div class="section-head fade-up d4">
      <h3 class="section-title">设置与服务</h3>
    </div>
    <div class="menu-list fade-up d4">
      <button class="menu-item" type="button" @click="goTo({ name: 'announcements', query: { from: 'mine' } })">
        <span class="mi-ico mi-ico--primary"><Megaphone :size="16" :stroke-width="2.2" /></span>
        <span class="mi-label">更新公告</span>
        <span class="mi-arrow"><ChevronRight :size="16" :stroke-width="2.2" /></span>
      </button>
      <button class="menu-item" data-theme-toggle type="button" @click="toggleTheme">
        <span class="mi-ico mi-ico--neutral">
          <Settings2 :size="16" :stroke-width="2.2" />
        </span>
        <span class="mi-label">主题 · 深色模式</span>
        <span class="theme-switch" :class="{ 'is-active': isDarkMode }" aria-hidden="true"><i></i></span>
      </button>
      <button class="menu-item" type="button" @click="goTo({ name: 'study-overview', query: { from: 'mine' } })">
        <span class="mi-ico mi-ico--neutral"><Palette :size="16" :stroke-width="2.2" /></span>
        <span class="mi-label">学习概览</span>
        <span class="mi-arrow"><ChevronRight :size="16" :stroke-width="2.2" /></span>
      </button>
      <button class="menu-item" type="button" @click="goTo({ name: 'announcements', query: { from: 'mine' } })">
        <span class="mi-ico mi-ico--neutral"><CircleHelp :size="16" :stroke-width="2.2" /></span>
        <span class="mi-label">帮助与反馈</span>
        <span class="mi-arrow"><ChevronRight :size="16" :stroke-width="2.2" /></span>
      </button>
      <button class="menu-item" type="button" @click="handleLogout">
        <span class="mi-ico mi-ico--danger">
          <LogOut :size="16" :stroke-width="2.2" />
        </span>
        <span class="mi-label">退出登录</span>
        <span class="mi-arrow">
          <ChevronRight :size="16" :stroke-width="2.2" />
        </span>
      </button>
    </div>

    <div class="mine-foot">
      <span class="mf-brand">学习宝</span>
      <span class="mf-ver">{{ appVersion }}</span>
    </div>
  </section>
</template>

<style scoped>
.mine-page {
  padding-bottom: var(--space-5);
  min-width: 0;
}

/* Profile card internal layout */
.profile-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.profile-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
}
.profile-info .profile-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.profile-card { padding: var(--space-3); }
.profile-card { border-radius: var(--radius-xl); }
.profile-card--centered { text-align: center; }
.profile-card--centered .profile-head { flex-direction: column; align-items: center; }
.profile-card--centered .profile-info { align-items: center; }

.profile-level {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 14px;
  color: rgba(255,255,255,.9);
  font-size: 11px;
  font-weight: 700;
}
.profile-level__track { height: 5px; margin-top: 7px; overflow: hidden; border-radius: 999px; background: rgba(255,255,255,.28); }
.profile-level__track i { display: block; width: 0; height: 100%; border-radius: inherit; background: rgba(255,255,255,.94); }

.profile-head { min-height: 44px; }

.avatar-wrap,
.avatar { width: 56px; height: 56px; }

/* Clickable stat grid (button element reset) */
button.stat-link {
  border: none;
  background: transparent;
  padding: 0;
  font: inherit;
  text-align: left;
  cursor: pointer;
  width: 100%;
  min-height: 44px;
  transition: transform var(--ease-out);
}
button.stat-link:active {
  transform: scale(0.985);
}
button.stat-link:active :deep(.stat-grid__item) {
  border-color: var(--primary-border);
}

.stat-grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.stat-grid-4 :deep(.stat-grid__item) {
  min-height: 72px;
  padding: 14px 4px;
  border-radius: var(--radius-md);
  background: var(--glass-card);
  box-shadow: var(--shadow-card), var(--glass-inner-highlight);
}

.mine-quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.mine-quick {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  column-gap: 9px;
  align-items: center;
  min-height: 74px;
  padding: 12px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  background: var(--glass-card);
  color: var(--text-main);
  text-align: left;
  box-shadow: var(--shadow-xs), var(--glass-inner-highlight);
}
.mine-quick:active { transform: scale(.98); }
.mine-quick__icon { display: grid; width: 36px; height: 36px; grid-row: span 2; place-items: center; border-radius: 13px; }
.mine-quick__icon--rose { background: var(--rose-soft); color: var(--rose); }
.mine-quick__icon--amber { background: var(--amber-soft); color: var(--amber); }
.mine-quick__icon--blue { background: #eff6ff; color: #2563eb; }
.mine-quick__icon--emerald { background: var(--primary-soft); color: var(--primary-strong); }
.mine-quick strong, .mine-quick small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mine-quick strong { font-size: 13px; }
.mine-quick small { margin-top: 3px; color: var(--text-muted); font-size: 10px; }

/* Button / label menu-item resets */
button.menu-item {
  font: inherit;
  text-align: left;
  width: 100%;
  cursor: pointer;
}
.menu-item .mi-arrow {
  display: inline-flex;
  align-items: center;
}

.menu-item { min-height: 52px; }
.menu-item { border-radius: 8px; }
.menu-item:active {
  transform: translateX(2px);
}
.menu-item:active .mi-ico {
  transform: scale(0.92);
}

/* Icon color variants for settings rows */
.menu-item .mi-ico.mi-ico--neutral {
  background: var(--surface-soft);
  color: var(--text-secondary);
}
.menu-item .mi-ico.mi-ico--primary {
  background: var(--surface-soft);
  color: var(--primary);
}
.menu-item .mi-ico.mi-ico--danger {
  background: var(--rose-soft);
  color: var(--rose);
}

.theme-switch {
  display: inline-flex;
  width: 38px;
  height: 22px;
  align-items: center;
  margin-left: auto;
  padding: 2px;
  border-radius: 999px;
  background: var(--line-strong);
  transition: background var(--ease-out);
}
.theme-switch i { display: block; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: var(--shadow-xs); transition: transform var(--ease-out); }
.theme-switch.is-active { background: var(--primary); }
.theme-switch.is-active i { transform: translateX(16px); }

/* Footer */
.mine-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-5);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--line-soft);
  font-size: var(--text-xs);
  color: var(--text-muted);
}
.mf-brand {
  font-family: var(--font-sans);
  font-weight: 800;
  letter-spacing: 0.04em;
}
.mf-ver {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-muted);
}

@media (max-width: 420px) {
  .stat-grid-4 :deep(.stat-grid__value) { font-size: var(--text-lg); }
  .menu-item { min-height: 52px; }
}

.mine-page { padding-top: 0; }
.profile-card--centered { margin-inline: -16px; padding: 28px 20px 22px; border-radius: 0 0 24px 24px; }
.profile-card--centered .avatar-wrap, .profile-card--centered .avatar { width: 64px; height: 64px; }
.profile-card--centered .profile-name { font-size: 20px; }
.stat-grid-4 { position: relative; z-index: 2; margin-top: -12px; }
.mine-quick { min-height: 112px; grid-template-columns: 1fr; justify-items: center; text-align: center; }
.mine-quick__icon { grid-row: auto; width: 48px; height: 48px; border-radius: 50%; }
.mine-quick strong, .mine-quick small { max-width: 100%; }
.menu-list { margin-top: 4px; }
</style>
