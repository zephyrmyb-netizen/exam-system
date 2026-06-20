<script setup>
import { computed } from "vue";
import { releaseNotes } from "../data/releaseNotes";

/**
 * Parse a version string like "v1.2.1" or "v2" into a numeric array
 * for comparison.  "v2" → [2]; "v1.11.3" → [1, 11, 3].
 */
function parseVersion(v) {
  if (!v || typeof v !== "string") return [];
  return v.replace(/^v/i, "").split(".").map(Number);
}

/**
 * Compare two version strings. Returns negative if a<b, positive if a>b, 0 if equal.
 * Major versions (v2) rank higher than any v1.x.x.
 */
function versionCompare(a, b) {
  const pa = parseVersion(a);
  const pb = parseVersion(b);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const va = pa[i] ?? 0;
    const vb = pb[i] ?? 0;
    if (va !== vb) return vb - va; // descending
  }
  return 0;
}

/** Sort: version descending, then date descending */
const sorted = computed(() =>
  [...releaseNotes].sort((a, b) => {
    const v = versionCompare(a.version, b.version);
    if (v !== 0) return v;
    return a.date > b.date ? -1 : 1;
  })
);

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
        <span v-if="note.version" class="note-version">{{ note.version }}</span>
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
  flex-wrap: wrap;
}

.note-version {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: var(--primary-soft);
  color: var(--primary-strong);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 0.04em;
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
