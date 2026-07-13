<script setup>
defineProps({
  answeredCount: { type: Number, default: 0 },
  accuracy: { type: Number, default: null },
  streakText: { type: String, default: "0" },
});
</script>

<template>
  <div class="practice-stats-bar" aria-label="本次练习统计">
    <span class="practice-stat-chip">已答 {{ answeredCount }}</span>
    <span
      class="practice-stat-chip"
      :class="{
        'practice-stat-chip--good': accuracy !== null && accuracy >= 70,
        'practice-stat-chip--bad': accuracy !== null && accuracy < 40,
      }"
    >
      正确率 {{ accuracy !== null ? `${accuracy}%` : "--" }}
    </span>
    <span class="practice-stat-chip practice-stat-chip--streak">{{ streakText }}</span>
  </div>
</template>

<style scoped>
.practice-stats-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  margin: 0;
  padding: 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--text-muted);
  overflow: hidden;
  scrollbar-width: none;
}

.practice-stats-bar::-webkit-scrollbar {
  display: none;
}

.practice-stat-chip {
  white-space: nowrap;
  color: var(--text-secondary);
  padding: 5px 9px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-full);
  background: var(--glass-card);
  box-shadow: var(--glass-inner-highlight);
}

.practice-stat-chip--good {
  color: var(--emerald);
}

.practice-stat-chip--bad {
  color: var(--rose);
}

.practice-stat-chip--streak {
  color: var(--primary-strong);
}

</style>
