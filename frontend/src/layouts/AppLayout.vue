<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useAiImportTask } from "../stores/aiImportTask";
import { getAuthEventName, getToken } from "../api/request";
import {
  Home,
  Library,
  Plus,
  User,
  ArrowLeft,
  Sparkles,
  CheckCircle,
} from "@lucide/vue";

const route = useRoute();
const router = useRouter();
const { fetchProfile } = useAuth();

const {
  status: aiStatus,
  fileName: aiFileName,
  elapsedSeconds,
  estimatedSeconds,
} = useAiImportTask();

const showSuccessToast = ref(false);
let successTimer = null;

// Show the slim running banner when AI is running and user is NOT on /import
const showAiBanner = computed(() => {
  return aiStatus.value === "running" && route.path !== "/import";
});

// Show success toast for 3 seconds then dismiss
watch(aiStatus, (val) => {
  if (val === "success") {
    showSuccessToast.value = true;
    if (successTimer) clearTimeout(successTimer);
    successTimer = setTimeout(() => {
      showSuccessToast.value = false;
    }, 3000);
  }
  if (val === "idle" || val === "running") {
    showSuccessToast.value = false;
    if (successTimer) clearTimeout(successTimer);
  }
});

const navItems = [
  { key: "home", label: "首页", icon: Home, to: "/" },
  { key: "list", label: "题库", icon: Library, to: "/courses" },
  { key: "import", label: "导入", icon: Plus, to: "/import", emphasis: true },
  { key: "ai", label: "AI", icon: Sparkles, to: "/chat" },
  { key: "mine", label: "我的", icon: User, to: "/mine" },
];

const activeNavKey = computed(() => {
  const nav = route.meta?.navKey;
  if (route.name === "study-overview") {
    if (route.query.from === "home") return "home";
    if (route.query.from === "mine") return "mine";
    return nav || "";
  }
  if (route.name === "announcements") {
    if (route.query.from === "home") return "home";
    if (route.query.from === "mine") return "mine";
    return nav || "";
  }
  if (route.name === "practice-history") {
    if (route.query.from === "mine") return "mine";
    return "";
  }
  return nav || "";
});
const showHeader = computed(() => route.name !== "home");
const showBackButton = computed(() => !!route.meta?.parent);

function goBack() {
  const allowedFromRoutes = ["home", "mine", "courses", "practice", "public-library"];
  const from = route.query.from;

  // 1. query.from takes priority
  if (from && allowedFromRoutes.includes(from)) {
    router.replace({ name: from });
    return;
  }

  // 2. meta.parent fallback
  const parent = route.meta?.parent;
  if (parent) {
    router.replace({ name: parent, params: { ...route.params } });
    return;
  }

  // 3. final fallback
  router.replace({ name: "home" });
}

function handleAuthChange() {
  if (!getToken()) {
    // 仅在当前不在登录页时跳转，避免重定向循环
    if (route.name !== "login" && route.name !== "register") {
      router.push({ name: "login", query: { redirect: route.fullPath } });
    }
  }
}

function handleTabClick(item) {
  if (route.path === item.to) return;
  router.replace(item.to);
}

onMounted(() => {
  if (getToken()) {
    fetchProfile();
  }
  window.addEventListener(getAuthEventName(), handleAuthChange);
  window.addEventListener("storage", handleAuthChange);
});

onUnmounted(() => {
  window.removeEventListener(getAuthEventName(), handleAuthChange);
  window.removeEventListener("storage", handleAuthChange);
});
</script>

<template>
  <div class="app-shell">
    <header v-if="showHeader" class="app-header">
      <button
        v-if="showBackButton"
        class="ghost-button back-button"
        type="button"
        @click="goBack"
      >
        <ArrowLeft :size="18" :stroke-width="2.5" />
        <span style="margin-left: 4px">返回</span>
      </button>
      <div class="page-intro">
        <p class="page-kicker" v-if="route.meta?.description">{{ route.meta.description }}</p>
        <h1>{{ route.meta?.title || "" }}</h1>
      </div>
    </header>

    <!-- AI import running banner -->
    <div
      v-if="showAiBanner"
      class="ai-task-banner"
      role="button"
      tabindex="0"
      @click="router.push('/import')"
      @keydown.enter="router.push('/import')"
    >
      <span class="ai-banner-dot"></span>
      <span class="ai-banner-text">AI 正在导入题目，预计约 {{ estimatedSeconds }} 秒</span>
      <span class="ai-banner-arrow">
        <ArrowLeft :size="14" :stroke-width="2.5" style="transform:rotate(180deg)" />
      </span>
    </div>

    <!-- AI import success toast -->
    <div
      v-if="showSuccessToast"
      class="ai-task-toast"
    >
      <CheckCircle :size="16" :stroke-width="2.5" style="margin-right:6px;flex-shrink:0" />
      <span>导入成功</span>
    </div>

    <main class="app-main">
      <router-view />
    </main>

    <nav class="bottom-nav" aria-label="主导航">
      <button
        v-for="item in navItems"
        :key="item.key"
        class="nav-button"
        :class="{
          active: activeNavKey === item.key,
          'nav-button--ai': item.emphasis,
        }"
        type="button"
        @click="handleTabClick(item)"
      >
        <span
          class="nav-icon"
          :class="{ 'nav-icon--ai': item.emphasis }"
          aria-hidden="true"
        >
          <component
            :is="item.icon"
            :size="item.emphasis ? 24 : 20"
            :stroke-width="item.emphasis ? 2.4 : 2"
          />
        </span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
/* Only new / overriding styles; everything else is in style.css */

.ghost-button.back-button {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}

/* ── Bottom Nav touch optimisation ── */
.nav-button {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

/* ── AI Task Banner ── */
.ai-task-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  margin-bottom: var(--space-2);
  border: 1px solid var(--line-accent);
  border-radius: var(--radius-md);
  background: var(--primary-soft);
  cursor: pointer;
  transition: background var(--ease-out);
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.ai-task-banner:active {
  background: #dbeafe;
}

.ai-banner-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: ai-dot-pulse 1.4s ease-in-out infinite;
}

@keyframes ai-dot-pulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50%      { opacity: 1;   transform: scale(1.2); }
}

.ai-banner-text {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--primary-strong);
  line-height: 1.3;
}

.ai-banner-arrow {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--primary);
}

/* ── AI Success Toast ── */
.ai-task-toast {
  position: fixed;
  bottom: calc(var(--nav-height) + var(--space-4));
  left: 50%;
  transform: translateX(-50%);
  z-index: 40;
  display: inline-flex;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  background: var(--emerald-soft);
  border: 1px solid var(--emerald-border);
  color: var(--emerald);
  font-size: var(--text-sm);
  font-weight: 700;
  box-shadow: var(--shadow-elevated);
  animation: ai-toast-in 0.3s ease-out;
  white-space: nowrap;
}

@keyframes ai-toast-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
