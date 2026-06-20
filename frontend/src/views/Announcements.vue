<script setup>
import { computed } from "vue";
import { releaseNotes } from "../data/releaseNotes";

/** 按日期降序排列（最新在前） */
const sorted = computed(() =>
  [...releaseNotes].sort((a, b) => (a.date > b.date ? -1 : 1))
);

/** 类型对应的标签颜色 */
function typeColor(type) {
  const map = {
    "修复": "var(--rose)",
    "新增": "var(--primary)",
    "优化": "var(--teal)",
    "重要": "var(--amber)",
  };
  return map[type] || "var(--text-muted)";
}

function typeBg(type) {
  const map = {
    "修复": "var(--rose-soft)",
    "新增": "var(--primary-soft)",
    "优化": "var(--teal-soft)",
    "重要": "var(--amber-soft)",
  };
  return map[type] || "var(--surface-soft)";
}
</script>

<template>
  <section class="stack">
    <div class="section-heading">
      <h2>更新公告</h2>
    </div>

    <article v-for="note in sorted" :key="note.id" class="note-card">
      <div class="note-head">
        <span class="note-type" :style="{ color: typeColor(note.type), background: typeBg(note.type) }">
          {{ note.type }}
        </span>
        <time class="note-date">{{ note.date }}</time>
      </div>

      <h3 class="note-title">{{ note.title }}</h3>

      <ul v-if="note.items?.length" class="note-items">
        <li v-for="item in note.items" :key="item">{{ item }}</li>
      </ul>
    </article>

    <div v-if="sorted.length === 0" class="empty-state">
      暂无更新公告
    </div>
  </section>
</template>

<style scoped>
.note-card {
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
  display: grid;
  gap: var(--space-2);
}

.note-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.note-type {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 0.04em;
}

.note-date {
  font-size: var(--text-xs);
  color: var(--text-placeholder);
  font-weight: 600;
}

.note-title {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 800;
  color: var(--text-main);
  line-height: 1.3;
}

.note-items {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 6px;
}

.note-items li {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.55;
}
</style>
