<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useStudyOverview } from "../composables/useStudyOverview";
import {
  Play, Upload, ChevronRight,
  TrendingUp, BookMarked, Target, Zap, Megaphone,
} from "@lucide/vue";
import { releaseNotes } from "../data/releaseNotes";

const router = useRouter();
const { user } = useAuth();
const { stats, review, fetchAll } = useStudyOverview();

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了";
  if (hour < 12) return "早上好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

const usernameText = computed(() => user.value?.username || user.value?.name || "同学");

const dateText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "long", day: "numeric", weekday: "long",
  }).format(new Date())
);

const accuracyDisplay = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "--";
  return `${(rate * 100).toFixed(1)}%`;
});

const accuracyColor = computed(() => {
  const rate = stats.value.accuracyRate;
  if (rate === null) return "";
  if (rate >= 0.8) return "green";
  if (rate >= 0.5) return "amber";
  return "rose";
});

const summarySubtitle = computed(() => {
  const t = stats.value.todayCount;
  const a = stats.value.accuracyRate;
  const parts = [];
  if (t !== null) parts.push(`今日 ${t} 题`);
  if (a !== null) parts.push(`正确率 ${(a * 100).toFixed(0)}%`);
  return parts.length > 0 ? parts.join(" · ") : "查看详细学习数据";
});

/** 最新一条公告（用于首页入口） */
const latestNote = computed(() => {
  if (releaseNotes.length === 0) return null;
  return releaseNotes.sort((a, b) => (a.date > b.date ? -1 : 1))[0];
});

const quickEntries = [
  { key: "wrongbook", label: "错题本", icon: BookMarked, color: "var(--rose)" },
  { key: "study-overview", label: "学习概览", icon: TrendingUp, color: "var(--teal)" },
  { key: "announcements", label: "更新公告", icon: Megaphone, color: "var(--amber)" },
];

onMounted(() => fetchAll());

function handleQuickEntry(item) {
  if (item.key === "study-overview") {
    router.push({ name: "study-overview", query: { from: "home" } });
  } else if (item.key === "announcements") {
    router.push({ name: "announcements", query: { from: "home" } });
  } else {
    router.push("/" + item.key);
  }
}
</script>

<template>
  <section class="home-panel">
    <!-- Welcome area -->
    <div class="welcome-bar">
      <div class="welcome-text">
        <p class="welcome-greeting">{{ greeting }}，{{ usernameText }}</p>
        <p class="welcome-date">{{ dateText }}</p>
        <p class="welcome-prompt">今天准备练哪一类题？</p>
      </div>
      <div class="welcome-avatar" aria-hidden="true">
        {{ usernameText.slice(0, 1).toUpperCase() }}
      </div>
    </div>

    <!-- Dashboard stats — clickable to /study-overview -->
    <button class="dash-summary" type="button" @click="router.push({ name: 'study-overview', query: { from: 'home' } })">
      <div class="dash-head">
        <Target :size="16" :stroke-width="2.5" class="dash-head-icon" />
        <span class="dash-head-title">学习概览</span>
        <ChevronRight :size="16" :stroke-width="2.5" class="dash-head-chevron" />
      </div>
      <div class="dash-body">
        <div class="dash-item">
          <Zap :size="14" :stroke-width="2.5" class="di-icon teal" />
          <div class="di-text">
            <span class="di-val">{{ stats.todayCount !== null ? stats.todayCount : "--" }}</span>
            <span class="di-lbl">今日</span>
          </div>
        </div>
        <div class="dash-item">
          <TrendingUp :size="14" :stroke-width="2.5" class="di-icon blue" />
          <div class="di-text">
            <span class="di-val">{{ stats.totalCount !== null ? stats.totalCount : "--" }}</span>
            <span class="di-lbl">累计</span>
          </div>
        </div>
        <div class="dash-item">
          <Target :size="14" :stroke-width="2.5" class="di-icon" :class="accuracyColor" />
          <div class="di-text">
            <span class="di-val" :class="accuracyColor">{{ accuracyDisplay }}</span>
            <span class="di-lbl">正确率</span>
          </div>
        </div>
        <div class="dash-item">
          <BookMarked :size="14" :stroke-width="2.5" class="di-icon rose" />
          <div class="di-text">
            <span class="di-val rose">{{ stats.recentCount7d !== null ? stats.recentCount7d : "--" }}</span>
            <span class="di-lbl">近 7 天</span>
          </div>
        </div>
      </div>
      <span class="dash-subtitle">{{ summarySubtitle }}</span>
    </button>

    <!-- Main actions -->
    <div class="home-ctas">
      <button class="cta-card cta-card--primary" type="button" @click="router.push('/practice')">
        <div class="cta-icon"><Play :size="24" /></div>
        <div class="cta-text">
          <span class="cta-title">继续练习</span>
          <span class="cta-desc">选择课程 · 专注练习</span>
        </div>
        <ChevronRight class="cta-chevron" :size="18" />
      </button>
      <button class="cta-card cta-card--teal" type="button" @click="router.push('/import')">
        <div class="cta-icon"><Upload :size="24" /></div>
        <div class="cta-text">
          <span class="cta-title">AI 导入</span>
          <span class="cta-desc">JSON · 文件 · 智能识别</span>
        </div>
        <ChevronRight class="cta-chevron" :size="18" />
      </button>
    </div>

    <!-- Latest announcement -->
    <button
      v-if="latestNote"
      class="announce-banner"
      type="button"
      @click="router.push({ name: 'announcements', query: { from: 'home' } })"
    >
      <Megaphone :size="14" :stroke-width="2.5" class="announce-icon" />
      <span class="announce-text">
        <template v-if="latestNote.version">{{ latestNote.version }} · </template>{{ latestNote.type }}：{{ latestNote.title }}
      </span>
      <ChevronRight :size="14" :stroke-width="2.5" class="announce-chevron" />
    </button>

    <!-- Quick entries -->
    <div class="section-label"><span>快捷入口</span></div>
    <div class="home-grid">
      <button
        v-for="item in quickEntries"
        :key="item.key"
        class="home-entry"
        type="button"
        @click="handleQuickEntry(item)"
      >
        <span class="home-entry-icon" :style="{ background: item.color }">
          <component :is="item.icon" :size="22" :stroke-width="2.2" />
        </span>
        <span class="home-entry-label">{{ item.label }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
/* ── Welcome Bar ── */
.welcome-bar {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(239,246,255,0.96));
  box-shadow: var(--shadow-card);
}
.welcome-text { min-width: 0; }
.welcome-greeting { margin: 0; font-size: var(--text-lg); font-weight: 800; color: var(--text-main); letter-spacing: -0.01em; }
.welcome-date { margin: 2px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; }
.welcome-prompt { margin: 6px 0 0; font-size: var(--text-sm); color: var(--text-secondary); font-weight: 600; }
.welcome-avatar {
  flex-shrink: 0; display: grid; place-items: center;
  width: 44px; height: 44px; border-radius: var(--radius-md);
  color: #fff; background: linear-gradient(135deg, var(--primary), var(--violet));
  font-size: var(--text-lg); font-weight: 800;
  box-shadow: 0 4px 12px rgba(59,130,246,0.22);
}

/* ── Dashboard Summary (clickable card) ── */
.dash-summary {
  display: grid; gap: var(--space-2);
  width: 100%; padding: var(--space-3) var(--space-4);
  border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  background: var(--surface); cursor: pointer; font: inherit; text-align: left;
  box-shadow: var(--shadow-xs);
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out);
}
.dash-summary:hover { border-color: var(--line-accent); box-shadow: var(--shadow-card); }
.dash-summary:active { transform: scale(0.985); }

.dash-head { display: flex; align-items: center; gap: 6px; }
.dash-head-icon { color: var(--teal); }
.dash-head-title { font-size: var(--text-sm); font-weight: 800; color: var(--text-main); flex: 1; }
.dash-head-chevron { color: var(--text-placeholder); flex-shrink: 0; }

.dash-body { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-2); }
.dash-item { display: flex; align-items: center; gap: 6px; }
.di-icon { flex-shrink: 0; }
.di-icon.teal { color: var(--teal); }
.di-icon.blue { color: var(--primary); }
.di-icon.rose { color: var(--rose); }
.di-icon.green { color: var(--emerald); }
.di-icon.amber { color: var(--amber); }
.di-text { display: grid; gap: 0; }
.di-val { font-size: var(--text-sm); font-weight: 800; line-height: 1.2; color: var(--text-main); }
.di-val.rose { color: var(--rose); }
.di-val.blue { color: var(--primary-strong); }
.di-val.green { color: var(--emerald); }
.di-val.amber { color: var(--amber); }
.di-lbl { font-size: 9px; color: var(--text-muted); font-weight: 600; }

.dash-subtitle { font-size: var(--text-xs); color: var(--text-placeholder); font-weight: 500; }

/* ── CTA Cards ── */
.home-ctas { display: grid; gap: var(--space-2); }
.cta-card {
  display: grid; grid-template-columns: 48px 1fr auto; align-items: center; gap: var(--space-3);
  width: 100%; padding: var(--space-4);
  border: 1.5px solid transparent; border-radius: var(--radius-md);
  text-align: left; font: inherit; cursor: pointer;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out);
}
.cta-card:active { transform: scale(0.985); }
.cta-card--primary { color: #fff; background: linear-gradient(135deg, var(--primary), var(--primary-strong)); border-color: rgba(37,99,235,0.6); box-shadow: var(--shadow-primary); }
.cta-card--primary:hover { box-shadow: 0 10px 24px rgba(37,99,235,0.3); transform: translateY(-1px); }
.cta-card--teal { color: #fff; background: linear-gradient(135deg, var(--teal), var(--teal-strong)); border-color: rgba(15,118,110,0.6); box-shadow: var(--shadow-teal); }
.cta-card--teal:hover { box-shadow: 0 10px 24px rgba(13,148,136,0.3); transform: translateY(-1px); }
.cta-icon { display: grid; place-items: center; width: 44px; height: 44px; border-radius: var(--radius-md); background: rgba(255,255,255,0.18); }
.cta-text { display: grid; gap: 2px; }
.cta-title { font-size: var(--text-base); font-weight: 800; letter-spacing: -0.005em; }
.cta-desc { font-size: var(--text-xs); font-weight: 500; opacity: 0.8; }
.cta-chevron { opacity: 0.6; }

/* ── Section Label ── */
.section-label { padding: var(--space-2) 0 0; }
.section-label span { font-size: var(--text-xs); font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }

/* ── Home Grid ── */
.home-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-2); }
.home-entry {
  display: grid; gap: 6px; justify-items: center;
  min-height: 92px; padding: var(--space-4) 8px;
  border: 1px solid var(--line-soft); border-radius: var(--radius-md);
  background: var(--surface); cursor: pointer; font: inherit; text-align: center;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out);
  box-shadow: var(--shadow-xs);
}
.home-entry:hover { border-color: var(--line-accent); box-shadow: var(--shadow-card); transform: translateY(-2px); }
.home-entry:active { transform: scale(0.97); }
.home-entry-icon { display: grid; place-items: center; width: 40px; height: 40px; border-radius: var(--radius-md); color: #fff; }
.home-entry-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-secondary); }

/* ── Announcement Banner ── */
.announce-banner {
  display: flex; align-items: center; gap: var(--space-2);
  width: 100%; padding: var(--space-2) var(--space-3);
  border: none; border-radius: var(--radius-md);
  background: var(--surface-soft); cursor: pointer; font: inherit; text-align: left;
  color: var(--text-muted);
  transition: background var(--ease-out), color var(--ease-out);
}
.announce-banner:hover { background: var(--primary-soft); color: var(--primary-strong); }
.announce-banner:active { transform: scale(0.99); }
.announce-icon { flex-shrink: 0; }
.announce-text { flex: 1; font-size: var(--text-xs); font-weight: 700; line-height: 1.3; }
.announce-chevron { flex-shrink: 0; }

/* ── Responsive ── */
@media (min-width: 640px) {
  .home-ctas { grid-template-columns: 1fr 1fr; }
  .home-grid { grid-template-columns: repeat(5, 1fr); }
}
@media (max-width: 420px) {
  .dash-body { gap: 4px; }
  .di-val { font-size: 12px; }
  .home-grid { gap: 6px; }
  .home-entry { min-height: 82px; padding: var(--space-3) 6px; }
  .home-entry-icon { width: 36px; height: 36px; }
}
</style>
