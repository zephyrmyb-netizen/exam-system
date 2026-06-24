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
import ConfirmDialog from "../components/common/ConfirmDialog.vue";

const route = useRoute();
const router = useRouter();
const { fetchProfile } = useAuth();

const {
  status: aiStatus,
  fileName: aiFileName,
  progressTitle: aiProgressTitle,
  progressDetail: aiProgressDetail,
} = useAiImportTask();

const showSuccessToast = ref(false);
let successTimer = null;

const showAiBanner = computed(() => aiStatus.value === "running" && route.path !== "/import");

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

const sourceAwareRoutes = new Set(["study-overview", "announcements"]);

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

  if (sourceAwareRoutes.has(route.name) && from && allowedFromRoutes.includes(from)) {
    router.replace({ name: from });
    return;
  }

  const parent = route.meta?.parent;
  if (parent) {
    router.replace({ name: parent, params: { ...route.params } });
    return;
  }

  router.replace({ name: "home" });
}

function handleAuthChange() {
  if (!getToken() && route.name !== "login" && route.name !== "register") {
    router.push({ name: "login", query: { redirect: route.fullPath } });
  }
}

function handleTabClick(item) {
  if (route.path === item.to) return;
  router.replace({ path: item.to });
}

function goToImportTab() {
  if (route.path === "/import") return;
  router.replace({ path: "/import" });
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
  if (successTimer) clearTimeout(successTimer);
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
        <p v-if="route.meta?.description" class="page-kicker">{{ route.meta.description }}</p>
        <h1>{{ route.meta?.title || "" }}</h1>
      </div>
    </header>

    <div
      v-if="showAiBanner"
      class="ai-task-banner"
      role="button"
      tabindex="0"
      @click="goToImportTab"
      @keydown.enter="goToImportTab"
    >
      <span class="ai-banner-dot"></span>
      <span class="ai-banner-text">
        {{ aiProgressTitle }}
        <small v-if="aiFileName"> · {{ aiFileName }}</small>
        <small v-if="aiProgressDetail"> · {{ aiProgressDetail }}</small>
      </span>
      <span class="ai-banner-arrow">
        <ArrowLeft :size="14" :stroke-width="2.5" style="transform:rotate(180deg)" />
      </span>
    </div>

    <div v-if="showSuccessToast" class="ai-task-toast">
      <CheckCircle :size="16" :stroke-width="2.5" style="margin-right:6px;flex-shrink:0" />
      <span>导入解析完成</span>
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

    <ConfirmDialog />
  </div>
</template>

<style scoped>
.ghost-button.back-button {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}

.nav-button {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

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
  50% { opacity: 1; transform: scale(1.2); }
}

.ai-banner-text {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--primary-strong);
  line-height: 1.3;
}

.ai-banner-text small {
  font-size: var(--text-xs);
  color: var(--text-secondary);
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
