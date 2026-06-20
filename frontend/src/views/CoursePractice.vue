<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import request from "../api/request";
import { getPracticeStats } from "../api/practice";
import {
  BookOpen, Layers, Play, Shuffle, RefreshCw,
  Target, ListChecks,
} from "@lucide/vue";
import Practice from "./Practice.vue";

const route = useRoute();
const router = useRouter();
const courseId = computed(() => route.params.courseId);

// ── Course info ──
const course = ref(null);
const loading = ref(false);

// ── Mode selection ──
const modes = [
  { key: "normal", label: "随机练习", desc: "随机抽题，适合日常巩固", icon: Shuffle, color: "var(--primary)", available: true },
  { key: "sequential", label: "顺序练习", desc: "按题目顺序依次答题", icon: ListChecks, color: "var(--teal)", available: false },
  { key: "wrong_review", label: "错题强化", desc: "针对本课程错题集中练习", icon: RefreshCw, color: "var(--rose)", available: true },
  { key: "type_practice", label: "题型专项", desc: "选择特定题型练习", icon: Target, color: "var(--violet)", available: false },
  { key: "chapter_practice", label: "章节专项", desc: "按章节筛选题目", icon: Layers, color: "var(--amber)", available: false },
];

const selectedMode = ref("normal");

// ── Start practice ──
const showPractice = ref(false);

function startPractice() {
  showPractice.value = true;
}

function endPractice() {
  showPractice.value = false;
}

async function fetchCourse() {
  if (!courseId.value) return;
  loading.value = true;
  try {
    const { data } = await request.get(`/courses/${courseId.value}`);
    course.value = data;
  } catch {
    // non-critical
  } finally {
    loading.value = false;
  }
}

onMounted(fetchCourse);
watch(() => route.params.courseId, () => { showPractice.value = false; fetchCourse(); });
</script>

<template>
  <section class="stack">
    <!-- ── Practice Mode ── -->
    <template v-if="!showPractice">
      <!-- Course header -->
      <div v-if="course" class="settings-header">
        <div class="settings-header-top">
          <div class="settings-icon"><BookOpen :size="22" :stroke-width="2" /></div>
          <div class="settings-info">
            <h2>{{ course.name || "课程" }}</h2>
            <p class="settings-meta">
              <Layers :size="13" :stroke-width="2" />
              <span>{{ course.question_count ?? 0 }} 道题</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Mode selection -->
      <p class="settings-section-label">选择练习模式</p>
      <div class="mode-grid">
        <button
          v-for="m in modes"
          :key="m.key"
          class="mode-card"
          :class="{
            'mode-active': selectedMode === m.key,
            'mode-disabled': !m.available,
          }"
          type="button"
          :disabled="!m.available"
          @click="selectedMode = m.key"
        >
          <span class="mode-card-icon" :style="{ color: m.color }">
            <component :is="m.icon" :size="20" :stroke-width="2" />
          </span>
          <span class="mode-card-text">
            <span class="mode-card-title">{{ m.label }}</span>
            <span class="mode-card-desc">{{ m.desc }}</span>
          </span>
          <span v-if="!m.available" class="mode-badge">后续开放</span>
        </button>
      </div>

      <!-- Stats summary -->
      <p class="settings-section-label">开始练习</p>
      <button class="start-btn" type="button" @click="startPractice">
        <Play :size="18" :stroke-width="2.5" style="margin-right:6px" />
        开始{{ selectedMode === 'wrong_review' ? '错题强化' : '练习' }}
      </button>
    </template>

    <!-- ── Immersive Practice ── -->
    <template v-else>
      <Practice
        :courseId="courseId"
        :courseName="course?.name || ''"
        :mode="selectedMode"
        modeParam=""
        @end-practice="endPractice"
      />
    </template>
  </section>
</template>

<style scoped>
/* ── Settings Header ── */
.settings-header {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
}
.settings-header-top { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: var(--space-3); }
.settings-icon { display: grid; place-items: center; width: 40px; height: 40px; border-radius: var(--radius-sm); background: var(--primary-soft); color: var(--primary-strong); flex-shrink: 0; }
.settings-info { min-width: 0; }
.settings-info h2 { margin: 0; font-size: var(--text-lg); font-weight: 800; line-height: 1.2; }
.settings-meta { display: inline-flex; align-items: center; gap: 4px; margin: 4px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; }

.settings-section-label {
  margin: 0 0 2px 4px;
  font-size: var(--text-xs);
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* ── Mode Cards ── */
.mode-grid { display: grid; gap: 6px; }

.mode-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-3);
  border: 1.5px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition: all var(--ease-out);
}

.mode-card:hover:not(:disabled) {
  border-color: var(--line-accent);
  box-shadow: var(--shadow-xs);
}

.mode-card:active:not(:disabled) {
  transform: scale(0.985);
}

.mode-active {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

.mode-active .mode-card-title {
  color: var(--primary-strong);
}

.mode-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-card-icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  flex-shrink: 0;
}

.mode-active .mode-card-icon {
  background: var(--surface);
}

.mode-card-text {
  display: grid;
  gap: 1px;
  min-width: 0;
}

.mode-card-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-main);
}

.mode-card-desc {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.mode-badge {
  padding: 2px 7px;
  border-radius: 5px;
  background: var(--surface-soft);
  color: var(--text-placeholder);
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

/* ── Start Button ── */
.start-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font-size: var(--text-base);
  font-weight: 800;
  cursor: pointer;
  box-shadow: var(--shadow-primary);
  transition: transform var(--ease-out), box-shadow var(--ease-out);
  min-height: 48px;
}

.start-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.3);
}

.start-btn:active {
  transform: translateY(0);
}

@media (max-width: 420px) {
  .settings-info h2 { font-size: 16px; }
}
</style>
