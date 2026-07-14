<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, useId, watch } from "vue";
import { X } from "@lucide/vue";

import Button from "./button/Button.vue";
import Card from "./card/Card.vue";

const props = withDefaults(defineProps<{
  modelValue: boolean;
  title: string;
  closeOnBackdrop?: boolean;
}>(), {
  closeOnBackdrop: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  close: [];
}>();

const titleId = `bottom-sheet-title-${useId()}`;
const dialogRef = ref<HTMLElement | null>(null);
let previouslyFocused: HTMLElement | null = null;

const focusableSelector = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function focusableElements(): HTMLElement[] {
  return dialogRef.value
    ? Array.from(dialogRef.value.querySelectorAll<HTMLElement>(focusableSelector))
    : [];
}

async function moveFocusInside() {
  const activeElement = document.activeElement;
  previouslyFocused = activeElement instanceof HTMLElement ? activeElement : null;
  await nextTick();
  const target = focusableElements()[0] || dialogRef.value;
  target?.focus();
}

function restoreFocus(defer = true) {
  const target = previouslyFocused;
  previouslyFocused = null;
  if (!target?.isConnected) return;
  if (defer) {
    void nextTick(() => target.focus());
  } else {
    target.focus();
  }
}

function close() {
  emit("update:modelValue", false);
  emit("close");
}

function handleBackdropClick() {
  if (props.closeOnBackdrop) close();
}

function handleKeydown(event: KeyboardEvent) {
  if (event.defaultPrevented) return;
  if (!props.modelValue) return;
  if (event.key === "Escape") {
    event.preventDefault();
    close();
    return;
  }
  if (event.key !== "Tab") return;

  const focusable = focusableElements();
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const activeElement = document.activeElement;
  if (!first || !last) {
    event.preventDefault();
    dialogRef.value?.focus();
    return;
  }
  if (event.shiftKey && (activeElement === first || !dialogRef.value?.contains(activeElement))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (activeElement === last || !dialogRef.value?.contains(activeElement))) {
    event.preventDefault();
    first.focus();
  }
}

watch(() => props.modelValue, (isOpen, wasOpen) => {
  if (isOpen && !wasOpen) void moveFocusInside();
  if (!isOpen && wasOpen) restoreFocus();
});

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
  if (props.modelValue) void moveFocusInside();
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  restoreFocus(false);
});
</script>

<template>
  <Transition name="bottom-sheet">
    <div v-if="modelValue" class="bottom-sheet" @click.self="handleBackdropClick">
      <div
        ref="dialogRef"
        class="bottom-sheet__dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
      >
        <Card class="bottom-sheet__panel">
          <div class="bottom-sheet__handle" aria-hidden="true"></div>
          <header class="bottom-sheet__header">
            <h2 :id="titleId">{{ title }}</h2>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="bottom-sheet__close"
              :aria-label="`关闭${title}`"
              @click="close"
            >
              <X :size="20" :stroke-width="2.25" aria-hidden="true" />
            </Button>
          </header>
          <div class="bottom-sheet__content">
            <slot />
          </div>
        </Card>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.bottom-sheet {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-top: var(--safe-area-top);
  background: rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.bottom-sheet__dialog {
  width: min(100%, var(--shell-max));
  max-height: min(82dvh, 720px);
  outline: 0;
}

.bottom-sheet__dialog > .bottom-sheet__panel {
  width: 100%;
  max-height: inherit;
  overflow: auto;
  padding: var(--space-2) var(--space-4) max(var(--space-5), var(--safe-area-bottom));
  border: 1px solid var(--glass-border);
  border-bottom: 0;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  background: var(--glass-card);
  color: var(--text-main);
  box-shadow: var(--shadow-modal), var(--glass-inner-highlight);
  backdrop-filter: blur(var(--glass-overlay-blur)) saturate(155%);
  -webkit-backdrop-filter: blur(var(--glass-overlay-blur)) saturate(155%);
}

.bottom-sheet__handle {
  width: 38px;
  height: 4px;
  margin: 0 auto var(--space-2);
  border-radius: var(--radius-full);
  background: var(--line-strong);
}

.bottom-sheet__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 48px;
}

.bottom-sheet__header h2 {
  margin: 0;
  font-size: var(--text-lg);
  line-height: 1.35;
}

.bottom-sheet__header > .bottom-sheet__close {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-secondary);
  padding: 0;
}

.bottom-sheet__content {
  min-width: 0;
  padding-top: var(--space-2);
}

.bottom-sheet-enter-active,
.bottom-sheet-leave-active {
  transition: opacity var(--ease-out);
}

.bottom-sheet-enter-active .bottom-sheet__dialog,
.bottom-sheet-leave-active .bottom-sheet__dialog {
  transition: transform var(--ease-out);
}

.bottom-sheet-enter-from,
.bottom-sheet-leave-to {
  opacity: 0;
}

.bottom-sheet-enter-from .bottom-sheet__dialog,
.bottom-sheet-leave-to .bottom-sheet__dialog {
  transform: translateY(24px);
}
</style>
