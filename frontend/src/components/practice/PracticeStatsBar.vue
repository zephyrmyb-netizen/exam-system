<script setup>
defineProps({
  answeredCount: { type: Number, default: 0 },
  accuracy: { type: Number, default: null },
  streakText: { type: String, default: "0" },
});
</script>

<template>
  <div class="practice-stats-bar">
    <span class="practice-stat-chip">已答 {{ answeredCount }}</span>
    <span class="practice-stat-sep">·</span>
    <span
      class="practice-stat-chip"
      :class="{
        'practice-stat-chip--good': accuracy !== null && accuracy >= 70,
        'practice-stat-chip--bad': accuracy !== null && accuracy < 40,
      }"
    >
      正确率 {{ accuracy !== null ? `${accuracy}%` : "--" }}
    </span>
    <span class="practice-stat-sep">·</span>
    <span class="practice-stat-chip practice-stat-chip--streak">{{ streakText }}</span>
  </div>
</template>

<style scoped>
.practice-stats-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 2px 4px 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--text-muted);
  overflow-x: auto;
  scrollbar-width: none;
}

.practice-stats-bar::-webkit-scrollbar {
  display: none;
}

.practice-stat-chip {
  white-space: nowrap;
  color: var(--text-secondary);
}

.practice-stat-chip--good {
  color: var(--emerald);
}

.practice-stat-chip--bad {
  color: var(--rose);
}

.practice-stat-chip--streak {
  color: var(--amber);
}

.practice-stat-sep {
  color: var(--line-strong);
  font-weight: 600;
}
</style>
