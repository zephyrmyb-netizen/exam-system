<script setup lang="ts">
import { ChevronLeft, Flag, LogOut } from "@lucide/vue";

defineProps({
  courseName: { type: String, default: "" },
  modeLabel: { type: String, default: "" },
  answeredCount: { type: Number, default: 0 },
  accuracy: { type: Number, default: null },
  totalQuestions: { type: Number, default: 0 },
  sessionOrder: { type: Number, default: 0 },
  sessionTotal: { type: Number, default: 0 },
  marked: { type: Boolean, default: false },
});

defineEmits(["back", "end", "toggle-mark"]);
</script>

<template>
  <nav class="practice-topbar" aria-label="答题导航">
    <button class="practice-icon-button" type="button" aria-label="返回" @click="$emit('back')">
      <ChevronLeft :size="18" :stroke-width="2.5" />
    </button>

    <div class="practice-topbar__center">
      <span class="practice-topbar__title">{{ courseName || modeLabel || "练习" }}</span>
      <span class="practice-topbar__meta">
        {{
          sessionTotal
            ? `第 ${sessionOrder} / ${sessionTotal} 题 · 已答 ${answeredCount}`
            : totalQuestions
              ? `已答 ${answeredCount} / ${totalQuestions}`
              : `已答 ${answeredCount}`
        }}
        ·
        {{ accuracy !== null ? `${accuracy}%` : "--" }}
      </span>
      <span v-if="totalQuestions" class="practice-topbar__track" aria-label="练习进度">
        <i :style="{ width: `${Math.min(100, Math.round((answeredCount / totalQuestions) * 100))}%` }"></i>
      </span>
    </div>

    <button
      class="practice-mark-button"
      type="button"
      :aria-label="marked ? '取消标记题目' : '标记题目'"
      @click="$emit('toggle-mark')"
    >
      <Flag :size="16" :stroke-width="2.5" :fill="marked ? 'currentColor' : 'none'" />
    </button>

    <button class="practice-end-button" type="button" aria-label="结束练习" @click="$emit('end')">
      <LogOut :size="16" :stroke-width="2.5" />
      <span class="practice-end-button__label">结束练习</span>
    </button>
  </nav>
</template>

<style scoped>
.practice-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 64px;
  padding: 10px 16px;
  overflow: hidden;
  border-bottom: 1px solid var(--glass-border);
  background: var(--glass-header);
  box-shadow: var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
  -webkit-backdrop-filter: blur(var(--glass-header-blur)) saturate(170%);
}

.practice-topbar__center {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  column-gap: 7px;
  row-gap: 4px;
  min-width: 0;
  max-width: 100%;
  flex: 1;
}

.practice-topbar__title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: 800;
  color: var(--text-secondary);
}

.practice-topbar__meta {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 800;
}

.practice-topbar__track {
  display: block;
  flex-basis: 100%;
  height: 6px;
  overflow: hidden;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
}

.practice-topbar__track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
  transition: width var(--ease-spring);
}

.practice-icon-button,
.practice-mark-button,
.practice-end-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  width: 36px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.42);
  color: var(--text-muted);
  transition:
    background var(--ease-out),
    border-color var(--ease-out),
    color var(--ease-out),
    box-shadow var(--ease-out);
  flex-shrink: 0;
}

.practice-icon-button:hover,
.practice-mark-button:hover,
.practice-end-button:hover {
  border-color: var(--line-accent);
  background: var(--surface-soft);
}

.practice-end-button:hover {
  color: var(--primary-strong);
  border-color: var(--line-accent);
  background: var(--primary-soft);
}

.practice-mark-button {
  color: var(--text-muted);
}

.practice-mark-button:hover {
  color: var(--amber-strong, #b45309);
  border-color: var(--amber, #f59e0b);
  background: var(--amber-soft, #fff7ed);
}

.practice-end-button__label {
  display: none;
}

@media (min-width: 420px) {
  .practice-end-button {
    width: auto;
    padding: 0 10px;
    border-radius: 18px;
    gap: 4px;
  }

  .practice-end-button__label {
    display: inline;
    font-size: 12px;
    font-weight: 800;
  }
}

@media (max-width: 360px) {
  .practice-topbar {
    gap: 6px;
    padding-inline: 10px;
  }

  .practice-topbar__title {
    max-width: 96px;
  }

  .practice-topbar__meta {
    font-size: 10px;
  }
}
</style>
