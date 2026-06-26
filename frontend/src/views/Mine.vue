<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useStudyOverview } from "../composables/useStudyOverview";
import {
  BarChart3,
  Bell,
  BookMarked,
  ChevronRight,
  Clock,
  HelpCircle,
  LogOut,
  Megaphone,
  MessageCircle,
  ShieldCheck,
  TrendingUp,
} from "@lucide/vue";
import { releaseNotes } from "../data/releaseNotes";

const router = useRouter();
const { user, logout } = useAuth();
const { stats, loading, errorMessage, fetchAll } = useStudyOverview();

const usernameText = computed(() => user.value?.username || "未登录");
const avatarChar = computed(() => usernameText.value.slice(0, 1).toUpperCase());
const isLoggedIn = computed(() => !!user.value);

const roleText = computed(() => {
  const role = user.value?.role;
  if (role === "admin") return "管理员";
  if (role === "teacher") return "教师";
  return "普通用户";
});

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "--";
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
    label: "学习概览",
    desc: "数据和薄弱点",
    icon: TrendingUp,
    color: "var(--teal)",
    to: { name: "study-overview", query: { from: "mine" } },
  },
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
]);

const supportItems = [
  {
    label: "AI 对话",
    desc: "追问知识点",
    icon: MessageCircle,
    to: "/chat",
  },
  {
    label: "使用提示",
    desc: "导入失败时先看公告和错误提示",
    icon: HelpCircle,
    to: { name: "announcements", query: { from: "mine" } },
  },
];

function goTo(target) {
  if (typeof target === "string") {
    router.push(target);
    return;
  }
  router.push(target);
}

function handleLogout() {
  logout();
  router.push({ name: "login" });
}

onMounted(() => fetchAll());
</script>

<template>
  <section class="mine-page">
    <div class="mine-header">
      <div class="profile-row">
        <div class="profile-avatar">{{ avatarChar }}</div>
        <div class="profile-copy">
          <div class="profile-name-row">
            <h1>{{ usernameText }}</h1>
            <span v-if="isLoggedIn" class="role-pill">
              <ShieldCheck :size="12" :stroke-width="2.5" />
              {{ roleText }}
            </span>
          </div>
          <p>
            <span class="status-dot" :class="{ online: isLoggedIn }"></span>
            {{ isLoggedIn ? "账号已登录，学习数据已同步" : "请先登录账号" }}
          </p>
        </div>
        <button class="notify-button" type="button" @click="goTo({ name: 'announcements', query: { from: 'mine' } })">
          <Bell :size="18" :stroke-width="2.4" />
        </button>
      </div>

      <button
        class="overview-entry"
        type="button"
        @click="goTo({ name: 'study-overview', query: { from: 'mine' } })"
      >
        <span class="overview-icon">
          <BarChart3 :size="24" :stroke-width="2.3" />
        </span>
        <span class="overview-copy">
          <strong>学习概览</strong>
          <small>
            今日 {{ overviewSummary.today ?? "--" }} 题
            · 总计 {{ overviewSummary.total ?? "--" }} 题
            · 正确率 {{ overviewSummary.accuracy }}
          </small>
        </span>
        <span class="overview-chip">近 7 日 {{ overviewSummary.recent ?? "--" }} 题</span>
        <ChevronRight :size="17" :stroke-width="2.5" />
      </button>
    </div>

    <p v-if="loading" class="status-banner status-banner--info">学习数据更新中...</p>
    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <section class="mine-section">
      <div class="mine-section-head">
        <h2>学习服务</h2>
        <span>复盘、记录、公告</span>
      </div>
      <div class="service-grid">
        <button
          v-for="item in serviceGrid"
          :key="item.label"
          class="service-item"
          type="button"
          @click="goTo(item.to)"
        >
          <span class="service-icon" :style="{ color: item.color }">
            <component :is="item.icon" :size="24" :stroke-width="2.15" />
          </span>
          <strong>{{ item.label }}</strong>
          <small>{{ item.desc }}</small>
        </button>
      </div>
    </section>

    <section class="mine-section">
      <div class="mine-section-head">
        <h2>更多</h2>
        <span>保留必要入口</span>
      </div>
      <div class="support-list">
        <button
          v-for="item in supportItems"
          :key="item.label"
          class="support-row"
          type="button"
          @click="goTo(item.to)"
        >
          <span class="support-icon">
            <component :is="item.icon" :size="20" :stroke-width="2.2" />
          </span>
          <span class="support-copy">
            <strong>{{ item.label }}</strong>
            <small>{{ item.desc }}</small>
          </span>
          <ChevronRight :size="16" :stroke-width="2.5" />
        </button>
      </div>
    </section>

    <section class="mine-section">
      <button class="logout-row" type="button" @click="handleLogout">
        <span class="support-icon logout-icon">
          <LogOut :size="19" :stroke-width="2.2" />
        </span>
        <span class="support-copy">
          <strong>退出登录</strong>
          <small>{{ usernameText }}</small>
        </span>
      </button>
    </section>

    <p class="app-version">Exam System {{ appVersion }}</p>
  </section>
</template>

<style scoped>
.mine-page {
  display: grid;
  gap: var(--space-4);
}

.mine-header {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 34%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
}

.profile-row {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) 40px;
  align-items: center;
  gap: var(--space-3);
}

.profile-avatar {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--violet));
  font-size: 24px;
  font-weight: 900;
  box-shadow: 0 10px 24px rgba(59, 130, 246, 0.24);
}

.profile-copy {
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.profile-name-row h1 {
  min-width: 0;
  overflow: hidden;
  margin: 0;
  color: var(--text-main);
  font-size: var(--text-xl);
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  color: var(--primary-strong);
  background: var(--primary-soft);
  font-size: 10px;
  font-weight: 800;
}

.profile-copy p {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-placeholder);
}

.status-dot.online {
  background: var(--emerald);
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15);
}

.notify-button {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  color: var(--text-secondary);
  background: var(--surface);
}

.overview-entry {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 76px;
  padding: var(--space-3);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-lg);
  color: inherit;
  background:
    radial-gradient(circle at right top, rgba(59, 130, 246, 0.14), transparent 38%),
    linear-gradient(135deg, #eff6ff, #ffffff);
  box-shadow: var(--shadow-xs);
  text-align: left;
}

.overview-icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
}

.overview-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.overview-copy strong {
  color: var(--text-main);
  font-size: var(--text-base);
}

.overview-copy small {
  overflow: hidden;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-chip {
  padding: 5px 9px;
  border-radius: var(--radius-full);
  color: var(--primary-strong);
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid var(--primary-border);
  font-size: 10px;
  font-weight: 900;
  white-space: nowrap;
}

.mine-section {
  display: grid;
  gap: var(--space-3);
}

.mine-section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-3);
  padding: 0 2px;
}

.mine-section-head h2 {
  margin: 0;
  color: var(--text-main);
  font-size: var(--text-xl);
  line-height: 1.2;
}

.mine-section-head span {
  color: var(--text-placeholder);
  font-size: var(--text-xs);
  font-weight: 800;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.service-item {
  display: grid;
  justify-items: center;
  gap: 6px;
  min-height: 96px;
  padding: var(--space-2) 2px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  text-align: center;
}

.service-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  background: var(--surface-soft);
}

.service-item strong {
  color: var(--text-main);
  font-size: var(--text-sm);
  line-height: 1.2;
}

.service-item small {
  max-width: 100%;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 700;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.support-list {
  display: grid;
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.support-row,
.logout-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 58px;
  padding: var(--space-3);
  border: none;
  border-bottom: 1px solid var(--line-soft);
  background: transparent;
  text-align: left;
  font: inherit;
}

.support-row:last-child {
  border-bottom: none;
}

.support-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  color: var(--primary-strong);
  background: var(--primary-soft);
}

.support-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.support-copy strong {
  color: var(--text-main);
  font-size: var(--text-base);
}

.support-copy small {
  overflow: hidden;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-row {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.logout-icon {
  color: var(--rose);
  background: var(--rose-soft);
}

.app-version {
  margin: 0;
  color: var(--text-placeholder);
  text-align: center;
  font-size: var(--text-xs);
  font-weight: 700;
}

@media (max-width: 420px) {
  .mine-header {
    padding: var(--space-4);
  }

  .profile-row {
    grid-template-columns: 50px minmax(0, 1fr) 38px;
  }

  .profile-avatar {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }

  .overview-entry {
    grid-template-columns: 42px minmax(0, 1fr) auto;
    gap: var(--space-2);
  }

  .overview-icon {
    width: 42px;
    height: 42px;
  }

  .overview-chip {
    grid-column: 2 / 4;
    justify-self: start;
  }

  .service-grid {
    gap: 4px;
    padding: var(--space-3);
  }

  .service-item {
    min-height: 88px;
  }

  .service-icon {
    width: 38px;
    height: 38px;
  }
}
</style>
