<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useStudyOverview } from "../composables/useStudyOverview";
import {
  TrendingUp,
  BookMarked,
  Clock,
  LogOut,
  ChevronRight,
  ShieldCheck,
  Megaphone,
} from "@lucide/vue";

const router = useRouter();
const { user, logout } = useAuth();
const { stats, review, fetchAll } = useStudyOverview();

const usernameText = computed(() => user.value?.username || null);
const roleText = computed(() => {
  const r = user.value?.role;
  if (r === "admin") return "管理员";
  if (r === "teacher") return "教师";
  return "普通用户";
});
const avatarChar = computed(() => (usernameText.value || "?")[0].toUpperCase());
const isLoggedIn = computed(() => !!user.value);

const summaryDesc = computed(() => {
  const t = stats.value.todayCount;
  const a = stats.value.accuracyRate;
  const parts = [];
  if (t !== null) parts.push(`今日 ${t} 题`);
  if (a !== null) parts.push(`正确率 ${(a * 100).toFixed(0)}%`);
  if (parts.length === 0) return "查看学习数据";
  return parts.join(" · ");
});

function handleLogout() {
  logout();
  router.push({ name: "login" });
}

const menuSections = computed(() => [
  {
    key: "学习",
    items: [
      {
        icon: TrendingUp,
        label: "学习概览",
        desc: summaryDesc.value,
        to: "/study-overview",
        color: "var(--teal)",
        bg: "var(--teal-soft)",
      },
      {
        icon: BookMarked,
        label: "错题本",
        desc: stats.value.wrongCount !== null ? `${stats.value.wrongCount} 道错题` : "",
        to: "/wrongbook",
        color: "var(--rose)",
        bg: "var(--rose-soft)",
      },
      {
        icon: Clock,
        label: "练习记录",
        desc: "查看答题历史",
        to: "/practice/history",
        color: "var(--amber)",
        bg: "var(--amber-soft)",
      },
      {
        icon: Megaphone,
        label: "更新公告",
        desc: "查看最新更新",
        to: "/announcements",
        color: "var(--teal)",
        bg: "var(--teal-soft)",
      },
    ],
  },
]);

function goTo(path) {
  if (path === "/study-overview") {
    router.push({ name: "study-overview", query: { from: "mine" } });
  } else if (path === "/announcements") {
    router.push({ name: "announcements", query: { from: "mine" } });
  } else {
    router.push(path);
  }
}

onMounted(() => fetchAll());
</script>

<template>
  <section class="mine-page">
    <!-- ── User Banner ── -->
    <div class="user-banner">
      <div class="user-avatar">{{ avatarChar }}</div>
      <div class="user-meta">
        <div class="user-name-row">
          <span class="user-name">{{ usernameText || "未登录" }}</span>
          <span v-if="isLoggedIn" class="user-role">
            <ShieldCheck :size="11" :stroke-width="2.5" style="margin-right:2px" />
            {{ roleText }}
          </span>
        </div>
        <span class="user-status">
          <span class="status-dot" :class="{ online: isLoggedIn }"></span>
          {{ isLoggedIn ? "已登录" : "离线" }}
        </span>
      </div>
    </div>

    <!-- ── Menu Sections ── -->
    <div v-for="section in menuSections" :key="section.key" class="menu-section">
      <p class="menu-section-label">{{ section.key }}</p>
      <div class="menu-group">
        <button
          v-for="item in section.items"
          :key="item.label"
          class="menu-row"
          type="button"
          @click="goTo(item.to)"
        >
          <span class="menu-row-left">
            <span class="menu-row-icon" :style="{ color: item.color, background: item.bg }">
              <component :is="item.icon" :size="18" :stroke-width="2" />
            </span>
            <span class="menu-row-text">
              <span class="menu-row-label">{{ item.label }}</span>
              <span v-if="item.desc" class="menu-row-desc">{{ item.desc }}</span>
            </span>
          </span>
          <ChevronRight class="menu-chevron" :size="16" :stroke-width="2.5" color="var(--text-placeholder)" />
        </button>
      </div>
    </div>

    <!-- ── Account: Logout ── -->
    <div class="menu-section">
      <p class="menu-section-label">账号</p>
      <div class="menu-group">
        <button class="menu-row menu-row-logout" type="button" @click="handleLogout">
          <span class="menu-row-left">
            <span class="menu-row-icon logout-icon">
              <LogOut :size="17" :stroke-width="2" />
            </span>
            <span class="menu-row-text">
              <span class="menu-row-label">退出登录</span>
              <span class="menu-row-desc" v-if="usernameText">{{ usernameText }}</span>
            </span>
          </span>
        </button>
      </div>
    </div>

    <p class="app-version">Exam System v1.0</p>
  </section>
</template>

<style scoped>
.mine-page { display: grid; gap: var(--space-4); }

/* ── User Banner ── */
.user-banner {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(239,246,255,0.92));
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(8px);
}
.user-avatar {
  flex-shrink: 0; display: grid; place-items: center;
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #7c3aed);
  color: #fff; font-size: 22px; font-weight: 800;
  box-shadow: 0 4px 14px rgba(59,130,246,0.28);
}
.user-meta { min-width: 0; display: grid; gap: 3px; }
.user-name-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.user-name { font-size: var(--text-lg); font-weight: 800; line-height: 1.2; }
.user-role { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; background: var(--primary-soft); color: var(--primary-strong); font-size: 10px; font-weight: 700; }
.user-status { font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; display: flex; align-items: center; gap: 4px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-placeholder); }
.status-dot.online { background: var(--emerald); box-shadow: 0 0 0 3px rgba(5,150,105,0.15); }

/* ── Menu Sections ── */
.menu-section-label { margin: 0 0 2px 4px; font-size: var(--text-xs); font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.menu-group { display: grid; border: 1px solid var(--line-soft); border-radius: var(--radius-lg); background: var(--surface); overflow: hidden; box-shadow: var(--shadow-xs); }
.menu-row {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3);
  width: 100%; padding: var(--space-3) var(--space-3);
  border: none; border-bottom: 1px solid var(--line-soft);
  background: transparent; text-align: left; font: inherit; color: var(--text-main);
  cursor: pointer; transition: background var(--ease-out), transform var(--ease-out); min-height: 52px;
}
.menu-row:last-child { border-bottom: none; }
.menu-row:hover { background: var(--surface-soft); }
.menu-row:active { background: var(--surface-strong); transform: scale(0.99); }
.menu-row-left { display: flex; align-items: center; gap: var(--space-3); min-width: 0; flex: 1; }
.menu-row-icon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: var(--radius-sm); flex-shrink: 0; }
.menu-row-text { display: grid; gap: 1px; min-width: 0; }
.menu-row-label { font-size: var(--text-base); font-weight: 700; line-height: 1.3; }
.menu-row-desc { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.menu-chevron { flex-shrink: 0; }

/* Logout row */
.menu-row-logout { color: var(--text-muted); }
.logout-icon { color: var(--text-muted); background: var(--surface-soft); }
.menu-row-logout:hover { background: var(--rose-soft); color: var(--rose); }
.menu-row-logout:hover .logout-icon { color: var(--rose); background: #fff1f2; }

.app-version { text-align: center; font-size: var(--text-xs); color: var(--text-placeholder); font-weight: 600; margin: var(--space-2) 0 0; }

/* ── Responsive ── */
@media (max-width: 420px) {
  .menu-row { padding: var(--space-2) var(--space-2); min-height: 48px; }
  .menu-row-label { font-size: 14px; }
  .user-banner { padding: var(--space-3); }
  .user-avatar { width: 44px; height: 44px; font-size: 18px; }
  .user-name { font-size: 16px; }
}
</style>
