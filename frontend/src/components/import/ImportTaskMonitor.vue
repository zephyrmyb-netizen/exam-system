<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  detail: {
    type: String,
    default: "",
  },
});
</script>

<template>
  <div class="running-panel">
    <span class="running-dot"></span>
    <div>
      <strong>{{ title }}</strong>
      <p>{{ detail }}</p>
    </div>
  </div>
</template>

<style scoped>
.running-panel {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--line-accent);
  border-radius: var(--radius-lg);
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.running-panel p {
  margin: 2px 0 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.running-dot {
  flex-shrink: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary);
  animation: running-pulse 1.2s ease-in-out infinite;
}

@keyframes running-pulse {
  0%,
  100% {
    opacity: 0.4;
    transform: scale(0.8);
  }

  50% {
    opacity: 1;
    transform: scale(1.25);
  }
}
</style>
