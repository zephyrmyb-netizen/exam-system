<script setup>
import { computed, onMounted, onUnmounted } from "vue";
import { AlertTriangle, CheckCircle, X } from "@lucide/vue";
import { useConfirmDialog } from "../../stores/confirmDialog";

const { visible, options, accept, cancel } = useConfirmDialog();

const icon = computed(() => (options.value.tone === "danger" ? AlertTriangle : CheckCircle));

function handleKeydown(event) {
  if (!visible.value) return;
  if (event.key === "Escape") {
    event.preventDefault();
    cancel();
  }
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <transition name="confirm-fade">
    <div v-if="visible" class="confirm-overlay" role="presentation" @click.self="cancel">
      <section
        class="confirm-card"
        :class="`confirm-card--${options.tone}`"
        role="dialog"
        aria-modal="true"
        :aria-label="options.title"
      >
        <button class="confirm-close icon-button" type="button" aria-label="关闭" @click="cancel">
          <X :size="18" :stroke-width="2.5" />
        </button>

        <div class="confirm-icon">
          <component :is="icon" :size="30" :stroke-width="2.4" />
        </div>

        <h2>{{ options.title }}</h2>
        <p v-if="options.message">{{ options.message }}</p>

        <div class="confirm-actions">
          <button class="confirm-cancel" type="button" @click="cancel">
            {{ options.cancelText }}
          </button>
          <button class="confirm-accept" type="button" @click="accept">
            {{ options.confirmText }}
          </button>
        </div>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(6px);
}

.confirm-card {
  position: relative;
  display: grid;
  gap: var(--space-3);
  width: min(100%, 340px);
  padding: var(--space-6) var(--space-5) var(--space-5);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-modal);
  text-align: center;
}

.confirm-close {
  position: absolute;
  top: 12px;
  right: 12px;
}

.confirm-icon {
  display: grid;
  place-items: center;
  justify-self: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.confirm-card--danger .confirm-icon {
  background: var(--rose-soft);
  color: var(--rose);
}

.confirm-card h2 {
  margin: 0;
  color: var(--text-main);
  font-size: var(--text-lg);
  font-weight: 800;
}

.confirm-card p {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.55;
  white-space: pre-line;
}

.confirm-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.confirm-cancel,
.confirm-accept {
  min-height: 44px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 800;
  cursor: pointer;
}

.confirm-cancel {
  border: 1.5px solid var(--line-strong);
  background: var(--surface);
  color: var(--text-secondary);
}

.confirm-accept {
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.confirm-card--danger .confirm-accept {
  background: linear-gradient(135deg, #f43f5e, #be123c);
  box-shadow: 0 12px 26px rgba(225, 29, 72, 0.24);
}

.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.18s ease;
}

.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}

@media (max-width: 420px) {
  .confirm-card {
    width: min(100%, 320px);
    padding: var(--space-5) var(--space-4) var(--space-4);
  }
}
</style>
