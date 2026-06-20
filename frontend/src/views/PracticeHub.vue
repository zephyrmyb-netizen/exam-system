<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import request from "../api/request";
import { getPracticeStats, getTodayReview, getWeakTypes } from "../api/practice";
import { typeLabel } from "../utils/question";
import {
  BookOpen, Play, Layers, Upload, Library, GraduationCap,
  RefreshCw, BookMarked, ListChecks, ChevronRight,
} from "@lucide/vue";

const router = useRouter();

// ── Stats overview ──
const stats = ref({ todayCount: null, totalCount: null, wrongCount: null });
const review = ref({ dueCount: null, wrongCount: null, weakTypes: [] });
const reviewLoading = ref(false);

// ── Recent courses (max 3, lightweight) ──
const recentCourses = ref([]);
const coursesLoading = ref(false);

const hasWrongQuestions = computed(() => {
  const w = review.value.wrongCount ?? stats.value.wrongCount;
  return w !== null && w > 0;
});

const hasDueQuestions = computed(() => {
  return review.value.dueCount !== null && review.value.dueCount > 0;
});

const hasRecentCourses = computed(() => recentCourses.value.length > 0);

async function fetchStatsReview() {
  reviewLoading.value = true;
  const [statsR, reviewR, weakR] = await Promise.allSettled([
    getPracticeStats(),
    getTodayReview(),
    getWeakTypes(),
  ]);
  if (statsR.status === "fulfilled") {
    const d = statsR.value;
    stats.value.todayCount = d.today_count ?? null;
    stats.value.totalCount = d.total_count ?? null;
    stats.value.wrongCount = d.wrong_count ?? null;
  }
  if (reviewR.status === "fulfilled") {
    const d = reviewR.value;
    review.value.dueCount = d.due_count ?? null;
    review.value.wrongCount = d.wrong_count ?? null;
  }
  if (weakR.status === "fulfilled") {
    review.value.weakTypes = weakR.value.slice(0, 3);
  }
  reviewLoading.value = false;
}

async function fetchRecentCourses() {
  coursesLoading.value = true;
  try {
    const { data } = await request.get("/courses/mine");
    const items = Array.isArray(data) ? data : data.items || [];
    // Show at most 3 recent courses (last created / first in list)
    recentCourses.value = items.slice(0, 3);
  } catch {
    recentCourses.value = [];
  } finally {
    coursesLoading.value = false;
  }
}

onMounted(() => {
  fetchStatsReview();
  fetchRecentCourses();
});
</script>

<template>
  <section class="hub">
    <!-- ── Overview Banner ── -->
    <div class="hub-overview">
      <div class="hub-stats">
        <div class="hub-stat">
          <span class="hub-stat-val">{{ stats.todayCount !== null ? stats.todayCount : "--" }}</span>
          <span class="hub-stat-lbl">今日练习</span>
        </div>
        <div class="hub-stat">
          <span class="hub-stat-val">{{ stats.totalCount !== null ? stats.totalCount : "--" }}</span>
          <span class="hub-stat-lbl">累计</span>
        </div>
        <div class="hub-stat">
          <span class="hub-stat-val">{{ hasWrongQuestions ? (review.wrongCount ?? stats.wrongCount) : "0" }}</span>
          <span class="hub-stat-lbl">错题</span>
        </div>
        <div class="hub-stat">
          <span class="hub-stat-val" :class="{ 'stat-accent': hasDueQuestions }">{{ review.dueCount !== null ? review.dueCount : "--" }}</span>
          <span class="hub-stat-lbl">到期</span>
        </div>
      </div>
      <div v-if="review.weakTypes.length > 0" class="hub-weak">
        <span class="hub-weak-lbl">薄弱</span>
        <span v-for="wt in review.weakTypes" :key="wt.question_type" class="hub-weak-chip">
          {{ typeLabel(wt.question_type) }}
        </span>
      </div>
    </div>

    <!-- ── Mode Cards ── -->
    <div class="modes">
      <button class="mode mode--cta" type="button" @click="router.push('/courses')">
        <Library :size="18" :stroke-width="2.5" class="mode-icon" style="color:var(--primary)" />
        <span class="mode-text">
          <span class="mode-title">从题库选择课程</span>
          <span class="mode-desc">选一门课，开始练习</span>
        </span>
        <ChevronRight :size="16" :stroke-width="2.5" style="color:var(--text-placeholder);flex-shrink:0" />
      </button>
      <button
        class="mode"
        :class="{ 'mode--dim': !hasWrongQuestions }"
        type="button"
        :disabled="!hasWrongQuestions"
        @click="router.push('/practice/wrong')"
      >
        <RefreshCw :size="18" :stroke-width="2.5" class="mode-icon" style="color:var(--rose)" />
        <span class="mode-text">
          <span class="mode-title">错题强化</span>
          <span class="mode-desc">{{ hasWrongQuestions ? `${review.wrongCount ?? stats.wrongCount} 道待复习` : "暂无错题" }}</span>
        </span>
      </button>
      <button
        class="mode"
        :class="{ 'mode--dim': !hasDueQuestions }"
        type="button"
        :disabled="!hasDueQuestions"
        @click="router.push('/practice/due')"
      >
        <BookMarked :size="18" :stroke-width="2.5" class="mode-icon" style="color:var(--teal)" />
        <span class="mode-text">
          <span class="mode-title">到期复习</span>
          <span class="mode-desc">{{ hasDueQuestions ? `${review.dueCount} 道今日到期` : "暂无到期题目" }}</span>
        </span>
      </button>
      <button class="mode" type="button" @click="router.push('/practice/history')">
        <ListChecks :size="18" :stroke-width="2.5" class="mode-icon" style="color:var(--amber)" />
        <span class="mode-text">
          <span class="mode-title">练习记录</span>
          <span class="mode-desc">查看答题历史</span>
        </span>
      </button>
    </div>

    <!-- ── Recent Courses ── -->
    <div v-if="hasRecentCourses" class="hub-section">
      <div class="hub-section-head">
        <span class="hub-section-label">最近可练习</span>
        <button class="hub-section-link" type="button" @click="router.push('/courses')">查看全部</button>
      </div>
      <div class="recent-list">
        <div v-for="course in recentCourses" :key="course.id" class="recent-row">
          <div class="recent-body" @click="router.push(`/courses/${course.id}`)">
            <div class="recent-icon" :class="course.visibility === 'public' ? 'icon-pub' : 'icon-mine'">
              <BookOpen :size="16" :stroke-width="2" />
            </div>
            <div class="recent-info">
              <span class="recent-name">{{ course.name || "未命名" }}</span>
              <span class="recent-meta"><Layers :size="10" :stroke-width="2" /> {{ course.question_count ?? 0 }} 题</span>
            </div>
          </div>
          <button class="recent-btn" type="button" @click="router.push(`/courses/${course.id}/practice`)">
            <Play :size="12" :stroke-width="2.5" style="margin-right:2px" />练习
          </button>
        </div>
      </div>
    </div>

    <!-- ── Guidance when no courses ── -->
    <div v-if="!coursesLoading && !hasRecentCourses" class="hub-guidance">
      <GraduationCap :size="44" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p class="hub-guidance-title">从题库中选择一门课开始练习</p>
      <p class="hub-guidance-hint">还没有课程？先去导入题目创建一门课。</p>
      <div class="hub-guidance-actions">
        <button class="primary-button" type="button" @click="router.push('/courses')">
          <Library :size="16" :stroke-width="2.5" style="margin-right:6px" />
          去题库选择
        </button>
        <button class="ghost-button" type="button" @click="router.push('/import')">
          <Upload :size="16" :stroke-width="2.5" style="margin-right:4px" />
          导入题目
        </button>
      </div>
      <div v-if="hasWrongQuestions || stats.totalCount" class="hub-guidance-alts">
        <button v-if="hasWrongQuestions" class="ghost-button" type="button" @click="router.push('/practice/wrong')">
          错题强化
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hub { display: grid; gap: var(--space-3); }

/* ── Overview ── */
.hub-overview {
  display: grid; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-md);
  background: var(--primary-soft);
}
.hub-stats { display: flex; gap: var(--space-5); }
.hub-stat { display: grid; gap: 1px; }
.hub-stat-val { font-size: 18px; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em; }
.hub-stat-lbl { font-size: 10px; font-weight: 600; color: var(--text-muted); }
.stat-accent { color: var(--teal); }
.hub-weak { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.hub-weak-lbl { font-size: 10px; font-weight: 700; color: var(--text-muted); }
.hub-weak-chip { padding: 2px 7px; border-radius: 999px; background: var(--rose-soft); color: var(--rose); font-size: 10px; font-weight: 700; }

/* ── Modes ── */
.modes { display: grid; gap: 6px; }
.mode {
  display: flex; align-items: center; gap: var(--space-3);
  width: 100%; padding: var(--space-3) var(--space-3);
  border: 1px solid var(--line-soft); border-radius: var(--radius-md);
  background: var(--surface); cursor: pointer; font: inherit; text-align: left;
  transition: transform var(--ease-out), box-shadow var(--ease-out), border-color var(--ease-out);
}
.mode:hover:not(.mode--dim) { border-color: var(--line-accent); box-shadow: var(--shadow-xs); }
.mode:active:not(.mode--dim) { transform: scale(0.985); }
.mode--cta { border-color: var(--primary-border); background: linear-gradient(135deg, #fafcff, #f0f6ff); }
.mode--dim { opacity: 0.5; cursor: not-allowed; }
.mode-icon { flex-shrink: 0; color: var(--primary); }
.mode-text { display: grid; gap: 1px; min-width: 0; flex: 1; }
.mode-title { font-size: var(--text-sm); font-weight: 700; color: var(--text-main); }
.mode-desc { font-size: 11px; color: var(--text-muted); font-weight: 500; }

/* ── Section ── */
.hub-section { display: grid; gap: var(--space-2); }
.hub-section-head { display: flex; align-items: center; justify-content: space-between; }
.hub-section-label { font-size: var(--text-xs); font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.hub-section-link { font-size: 11px; font-weight: 700; color: var(--primary); background: none; border: none; cursor: pointer; padding: 0; }
.hub-section-link:hover { color: var(--primary-strong); }

/* ── Recent Courses ── */
.recent-list { display: grid; gap: 6px; }
.recent-row {
  display: grid; grid-template-columns: 1fr auto; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--surface);
}
.recent-body { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: var(--space-2); cursor: pointer; min-width: 0; }
.recent-icon { display: grid; place-items: center; width: 32px; height: 32px; border-radius: var(--radius-sm); flex-shrink: 0; }
.icon-mine { background: var(--primary-soft); color: var(--primary-strong); }
.icon-pub { background: var(--emerald-soft); color: var(--emerald); }
.recent-info { display: grid; gap: 1px; min-width: 0; }
.recent-name { font-size: var(--text-sm); font-weight: 700; color: var(--text-main); line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-meta { display: inline-flex; align-items: center; gap: 3px; font-size: 10px; color: var(--text-muted); font-weight: 600; }
.recent-btn {
  display: inline-flex; align-items: center;
  padding: 4px 10px; min-height: 28px;
  border: 1px solid var(--primary-border); border-radius: var(--radius-full);
  background: var(--primary-soft); color: var(--primary-strong);
  font-size: 11px; font-weight: 700; cursor: pointer; flex-shrink: 0;
}

/* ── Guidance (no courses) ── */
.hub-guidance { display: grid; place-items: center; gap: var(--space-2); padding: var(--space-8) var(--space-4); text-align: center; color: var(--text-muted); }
.hub-guidance p { margin: 0; }
.hub-guidance-title { font-size: var(--text-base); font-weight: 700; color: var(--text-secondary); }
.hub-guidance-hint { font-size: var(--text-sm); color: var(--text-muted); }
.hub-guidance-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); justify-content: center; margin-top: var(--space-2); }
.hub-guidance-alts { display: flex; flex-wrap: wrap; gap: var(--space-2); justify-content: center; margin-top: var(--space-1); }
.hub-guidance-alts button { font-size: var(--text-xs); padding: 6px 12px; min-height: 32px; }

.primary-button, .ghost-button { display: inline-flex; align-items: center; justify-content: center; }
</style>
