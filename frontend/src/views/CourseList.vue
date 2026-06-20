<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import {
  BookOpen,
  GraduationCap,
  ChevronRight,
  Layers,
  Globe,
  Lock,
  Upload,
  Play,
  Sparkles,
  Trash2,
} from "@lucide/vue";

const router = useRouter();
const courses = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const deleteLoading = ref(null); // course.id or null

const cardColors = [
  { bar: "#3b82f6" },
  { bar: "#0d9488" },
  { bar: "#7c3aed" },
  { bar: "#d97706" },
  { bar: "#e11d48" },
];

function getCardColor(index) {
  return cardColors[index % cardColors.length];
}

async function fetchCourses() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await request.get("/courses/mine");
    courses.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取课程列表失败");
  } finally {
    loading.value = false;
  }
}

onMounted(fetchCourses);

async function deleteCourse(course) {
  const confirmed = window.confirm(
    `确定删除课程「${course.name}」吗？\n该课程共 ${course.question_count ?? 0} 道题，删除后题目将被一并移除，此操作不可撤销。`
  );
  if (!confirmed) return;

  deleteLoading.value = course.id;
  errorMessage.value = "";
  try {
    await request.delete(`/courses/${course.id}`);
    courses.value = courses.value.filter(c => c.id !== course.id);
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "删除课程失败");
  } finally {
    deleteLoading.value = null;
  }
}
</script>

<template>
  <section class="stack">
    <div class="section-heading row-heading">
      <div>
        <h2>我的题库</h2>
        <p>选择一门课程，开始练习或管理题目。</p>
      </div>
      <button class="ghost-button" type="button" :disabled="loading" @click="fetchCourses">
        刷新
      </button>
    </div>

    <p v-if="loading" class="info-message">加载中...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <!-- Empty state -->
    <div v-if="!loading && courses.length === 0 && !errorMessage" class="empty-state">
      <GraduationCap :size="44" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p>上传 Word / PPT，自动生成第一套题库</p>
      <button class="primary-button" type="button" @click="router.push('/import')">
        <Sparkles :size="17" :stroke-width="2.5" style="margin-right:6px" />
        去导入
      </button>
    </div>

    <!-- Course cards -->
    <div
      v-for="(course, idx) in courses"
      :key="course.id"
      class="course-card"
      :style="{ '--card-accent': getCardColor(idx).bar }"
    >
      <div class="course-card-body" @click="router.push(`/courses/${course.id}`)">
        <div class="course-icon" :style="{ background: 'var(--primary-soft)', color: 'var(--primary-strong)' }">
          <BookOpen :size="20" :stroke-width="2" />
        </div>
        <div class="course-info">
          <h3>{{ course.name || "未命名课程" }}</h3>
          <p class="course-meta">
            <Layers :size="13" :stroke-width="2" />
            <span>{{ course.question_count ?? 0 }} 道题</span>
            <span class="visibility-badge" :class="course.visibility">
              <Lock v-if="course.visibility === 'private'" :size="11" :stroke-width="2.5" />
              <Globe v-else :size="11" :stroke-width="2.5" />
              {{ course.visibility === "public" ? "已公开" : "私有" }}
            </span>
          </p>
        </div>
        <ChevronRight class="course-chevron" :size="18" :stroke-width="2.5" color="var(--text-placeholder)" />
      </div>
      <div class="course-actions">
        <button
          class="ghost-button course-action-btn"
          type="button"
          @click="router.push(`/courses/${course.id}`)"
        >
          查看题目
        </button>
        <button
          class="primary-button course-action-btn course-start-btn"
          type="button"
          @click="router.push(`/courses/${course.id}/practice`)"
        >
          <Play :size="15" :stroke-width="2.5" style="margin-right:4px" />
          开始练习
        </button>
        <button
          class="delete-btn"
          type="button"
          :disabled="deleteLoading === course.id"
          @click.stop="deleteCourse(course)"
          title="删除课程"
        >
          <Trash2 :size="15" :stroke-width="2.5" />
        </button>
      </div>
    </div>

    <!-- Published courses link -->
    <div v-if="courses.length > 0" class="public-library-link">
      <button class="ghost-button full-button" type="button" @click="router.push('/public-library')">
        <Globe :size="16" :stroke-width="2.5" style="margin-right:6px" />
        浏览公共题库
      </button>
    </div>
  </section>
</template>

<style scoped>
.row-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.course-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
  transition: transform var(--ease-out), box-shadow var(--ease-out);
  position: relative;
  overflow: hidden;
}

/* Left accent bar (color set via --card-accent custom property) */
.course-card::before {
  content: "";
  position: absolute;
  top: 12px;
  left: 0;
  width: 4px;
  height: calc(100% - 24px);
  border-radius: 0 4px 4px 0;
  background: var(--card-accent, var(--primary));
  opacity: 0.6;
}

.course-card:active {
  transform: scale(0.99);
}

.course-card:hover {
  box-shadow: var(--shadow-sm);
}

.course-card-body {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  padding-left: var(--space-1); /* room for accent bar */
}

.course-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.course-info {
  min-width: 0;
}

.course-info h3 {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-main);
}

.course-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  flex-wrap: wrap;
}

.visibility-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}

.visibility-badge.private {
  background: #f1f5f9;
  color: #64748b;
}

.visibility-badge.public {
  background: var(--emerald-soft);
  color: var(--emerald);
}

.course-chevron {
  flex-shrink: 0;
}

.course-actions {
  display: flex;
  gap: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid var(--line-soft);
}

.course-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  padding: 8px 12px;
  min-height: 36px;
  flex: 1;
  border-radius: var(--radius-sm);
}

.course-start-btn {
  flex: 1.5;
}

.delete-btn {
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--line-strong);
  cursor: pointer;
  transition: all var(--ease-out);
}

.delete-btn:hover:not(:disabled) {
  color: var(--rose);
  background: var(--rose-soft);
  border-color: var(--rose-border);
}

/* Empty state */
.empty-state {
  display: grid;
  place-items: center;
  gap: var(--space-3);
  padding: var(--space-10) var(--space-4);
  text-align: center;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.empty-state p {
  margin: 0;
  max-width: 280px;
}

/* Public library link */
.public-library-link {
  padding-top: var(--space-1);
}

.public-library-link button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* ── 375px responsive ── */
@media (max-width: 420px) {
  .course-card {
    padding: var(--space-3);
  }
  .course-action-btn {
    font-size: 10px;
    padding: 6px 8px;
    min-height: 32px;
  }
}
</style>
