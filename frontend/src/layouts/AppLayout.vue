<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, CheckCircle, Home, Library, Moon, Plus, Sparkles, Sun, User } from "@lucide/vue";

import { getAuthEventName, getToken } from "../api/request";
import ConfirmDialog from "../components/common/ConfirmDialog.vue";
import GlobalSearch from "../components/search/GlobalSearch.vue";
import { useAiImportTask } from "../stores/aiImportTask";
import { useAuth } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const route = useRoute();
const router = useRouter();
const { fetchProfile } = useAuth();
const theme = useThemeStore();

const {
  status: aiStatus,
  fileName: aiFileName,
  progressTitle: aiProgressTitle,
  progressDetail: aiProgressDetail,
} = useAiImportTask();

const showSuccessToast = ref(false);
const searchRef = ref<InstanceType<typeof GlobalSearch> | null>(null);
let successTimer: ReturnType<typeof setTimeout> | null = null;

const keyboardActive = ref(false);
const inputFocusActive = ref(false);
const immersiveRouteNames = new Set(["course-practice", "practice-wrong", "practice-due", "exam-take"]);

const showAiBanner = computed(() => aiStatus.value === "running" && route.path !== "/import");

const isImmersiveRoute = computed(() => immersiveRouteNames.has(route.name as string));
const showBottomNav = computed(() => !keyboardActive.value && !inputFocusActive.value && !isImmersiveRoute.value);

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

const sourceAwareRoutes = new Set(["study-overview", "announcements", "practice-history"]);

const activeNavKey = computed(() => {
  const nav = route.meta?.navKey;
  if (sourceAwareRoutes.has(route.name as string)) {
    if (route.query.from === "home") return "home";
    if (route.query.from === "mine") return "mine";
    return nav || "";
  }
  return nav || "";
});

const showHeader = computed(() => !isImmersiveRoute.value && !["home", "mine", "chat"].includes(route.name as string));
const showBackButton = computed(() => !!route.meta?.parent);

function goBack() {
  const allowedFromRoutes = ["home", "mine", "courses", "practice", "public-library"];
  const from = route.query.from;

  if (sourceAwareRoutes.has(route.name as string) && typeof from === "string" && allowedFromRoutes.includes(from)) {
    router.replace({ name: from });
    return;
  }

  const parent = route.meta?.parent;
  if (typeof parent === "string") {
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

function handleTabClick(item: { to: string }) {
  if (route.path === item.to) return;
  router.replace({ path: item.to });
}

function goToImportTab() {
  if (route.path === "/import") return;
  router.replace({ path: "/import" });
}

function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchRef.value?.open();
  }
}

function handleViewportResize() {
  if (window.visualViewport) {
    const vv = window.visualViewport;
    const heightDiff = window.innerHeight - vv.height;
    keyboardActive.value = heightDiff > 120;
  }
}

function isEditableElement(target: unknown): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

function handleFocusIn(event: { target: unknown }) {
  inputFocusActive.value = isEditableElement(event.target);
}

function handleFocusOut() {
  window.setTimeout(() => {
    inputFocusActive.value = isEditableElement(document.activeElement);
  }, 0);
}

onMounted(() => {
  if (getToken()) fetchProfile();
  window.addEventListener(getAuthEventName(), handleAuthChange);
  window.addEventListener("storage", handleAuthChange);
  window.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener("focusin", handleFocusIn);
  window.addEventListener("focusout", handleFocusOut);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", handleViewportResize);
  }
});

onUnmounted(() => {
  window.removeEventListener(getAuthEventName(), handleAuthChange);
  window.removeEventListener("storage", handleAuthChange);
  window.removeEventListener("keydown", handleGlobalKeydown);
  window.removeEventListener("focusin", handleFocusIn);
  window.removeEventListener("focusout", handleFocusOut);
  if (window.visualViewport) {
    window.visualViewport.removeEventListener("resize", handleViewportResize);
  }
  if (successTimer) clearTimeout(successTimer);
});
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--keyboard': keyboardActive, 'app-shell--immersive': isImmersiveRoute }">
    <header v-if="showHeader" class="app-header">
      <button v-if="showBackButton" class="layout-back-button" type="button" @click="goBack">
        <ArrowLeft :size="18" :stroke-width="2.5" />
        <span>返回</span>
      </button>
      <div class="header-row">
        <div class="page-intro">
          <p v-if="route.meta?.description" class="page-kicker">{{ route.meta.description }}</p>
          <h1>{{ route.meta?.title || "" }}</h1>
        </div>
        <button class="theme-toggle" type="button" aria-label="切换主题" @click="theme.toggle()">
          <Sun v-if="theme.mode === 'dark'" :size="18" :stroke-width="2.4" />
          <Moon v-else :size="18" :stroke-width="2.4" />
        </button>
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
        {{ aiProgressTitle || "AI 正在解析题目，请稍候" }}
        <small v-if="aiFileName"> · {{ aiFileName }}</small>
        <small v-if="aiProgressDetail"> · {{ aiProgressDetail }}</small>
      </span>
      <span class="ai-banner-arrow">
        <ArrowLeft :size="14" :stroke-width="2.5" style="transform: rotate(180deg)" />
      </span>
    </div>

    <div v-if="showSuccessToast" class="ai-task-toast">
      <CheckCircle :size="16" :stroke-width="2.5" />
      <span>导入解析完成</span>
    </div>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <nav v-if="showBottomNav" class="bottom-nav" aria-label="主导航">
      <button
        v-for="item in navItems"
        :key="item.key"
        class="nav-button"
        :class="{ active: activeNavKey === item.key, 'nav-button--ai': item.emphasis }"
        type="button"
        @click.stop.prevent="handleTabClick(item)"
      >
        <span class="nav-icon" :class="{ 'nav-icon--ai': item.emphasis }" aria-hidden="true">
          <component :is="item.icon" :size="item.emphasis ? 24 : 20" :stroke-width="item.emphasis ? 2.4 : 2" />
        </span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>

    <ConfirmDialog />
    <GlobalSearch ref="searchRef" />
  </div>
</template>

<style scoped>
.app-shell {
  width: 100%;
  max-width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding-bottom: calc(112px + env(safe-area-inset-bottom));
}

.app-shell--keyboard,
.app-shell--immersive {
  padding-bottom: env(safe-area-inset-bottom);
}

.app-shell--immersive {
  --practice-sticky-bottom: calc(12px + env(safe-area-inset-bottom));
  overflow-x: hidden;
}

.app-main {
  width: 100%;
  max-width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  /* 不设 overflow-x: hidden —— 根据 CSS 规范，设置 overflow-x 为非 visible 值
     会把 overflow-y 计算为 auto，使 .app-main 成为滚动容器，从而破坏
     ExamTake .exam-topbar 的 position: sticky（会相对于 .app-main 而非视口吸顶）。
     子元素已用 min-width: 0 + max-width: 100% 约束，不会横向溢出。 */
}

.app-main :deep(> *) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.app-header {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4) var(--space-2);
}

.layout-back-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
  min-height: 36px;
  padding: 0 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-full);
  background: var(--surface);
  color: var(--text-main);
  font-weight: 800;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.theme-toggle {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: var(--surface);
  color: var(--text-main);
}

.ai-task-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 var(--space-4) var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--line-accent);
  border-radius: var(--radius-md);
  background: var(--primary-soft);
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
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
  font-weight: 800;
  color: var(--primary-strong);
  line-height: 1.35;
}

.ai-banner-text small {
  color: var(--text-muted);
  font-weight: 650;
}

.ai-banner-arrow {
  display: grid;
  place-items: center;
  color: var(--primary-strong);
}

.ai-task-toast {
  position: fixed;
  left: 50%;
  bottom: calc(104px + env(safe-area-inset-bottom));
  z-index: 80;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-full);
  background: rgba(15, 23, 42, 0.92);
  color: #fff;
  font-size: var(--text-xs);
  font-weight: 800;
  transform: translateX(-50%);
  box-shadow: var(--shadow-modal);
}

.bottom-nav {
  position: fixed;
  left: max(14px, env(safe-area-inset-left));
  right: max(14px, env(safe-area-inset-right));
  bottom: calc(10px + env(safe-area-inset-bottom));
  z-index: 70;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  align-items: end;
  min-height: 74px;
  padding: 8px 10px 10px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(18px);
  transform: none;
  width: auto;
}

.nav-button {
  display: grid;
  place-items: center;
  gap: 3px;
  min-width: 0;
  min-height: 56px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 850;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.nav-button.active { color: var(--primary); }
.nav-icon { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 14px; }
.nav-icon--ai {
  width: 58px;
  height: 58px;
  margin-top: -28px;
  border-radius: 20px;
  color: #fff;
  background: linear-gradient(135deg, #3b82f6, #7c3aed);
  box-shadow: 0 12px 30px rgba(59, 130, 246, 0.32);
}
.nav-label { line-height: 1; }

@media (min-width: 760px) {
  .app-shell { max-width: 640px; margin: 0 auto; }
  .bottom-nav { left: 50%; right: auto; width: min(612px, calc(100% - 28px)); transform: translateX(-50%); }
}
</style>
