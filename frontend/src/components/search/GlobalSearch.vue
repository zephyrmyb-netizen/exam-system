<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Search, X } from "@lucide/vue";

import { getMyCourses } from "@/api/courses";
import { getQuestions } from "@/api/questions";
import type { Course, Question } from "@/types";

const router = useRouter();

const openState = ref(false);
const keyword = ref("");
const inputEl = ref<HTMLInputElement | null>(null);
const courses = ref<Course[]>([]);
const questions = ref<Question[]>([]);
const loading = ref(false);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

defineExpose({
  open,
});

function open() {
  openState.value = true;
  void nextTick(() => inputEl.value?.focus());
}

function close() {
  openState.value = false;
  keyword.value = "";
  courses.value = [];
  questions.value = [];
}

async function search() {
  const q = keyword.value.trim();
  if (!q) {
    courses.value = [];
    questions.value = [];
    return;
  }

  loading.value = true;
  try {
    const [courseResult, questionResult] = await Promise.allSettled([
      getMyCourses(),
      getQuestions({ keyword: q, page_size: 6 }),
    ]);

    if (courseResult.status === "fulfilled") {
      courses.value = courseResult.value
        .filter((course) => course.name.toLowerCase().includes(q.toLowerCase()))
        .slice(0, 5);
    }

    if (questionResult.status === "fulfilled") {
      const data = questionResult.value;
      questions.value = (Array.isArray(data) ? data : data.items || []).slice(0, 6);
    }
  } finally {
    loading.value = false;
  }
}

watch(keyword, () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    void search();
  }, 240);
});

function goCourse(course: Course) {
  router.push(`/courses/${course.id}`);
  close();
}

function goQuestion(question: Question) {
  router.push(`/courses/${question.course_id || ""}`);
  close();
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="openState"
      class="global-search-mask"
      role="dialog"
      aria-modal="true"
      @click.self="close"
      @keydown.esc="close"
    >
      <section class="global-search-panel">
        <div class="global-search-input">
          <Search :size="18" :stroke-width="2.4" />
          <input ref="inputEl" v-model="keyword" type="search" placeholder="搜索题库、课程、题目" />
          <button type="button" aria-label="关闭搜索" @click="close">
            <X :size="18" :stroke-width="2.4" />
          </button>
        </div>

        <div class="global-search-body">
          <p v-if="loading" class="search-hint">搜索中...</p>
          <p v-else-if="!keyword.trim()" class="search-hint">输入关键词，快速跳到题库或题目。</p>
          <template v-else>
            <div v-if="courses.length" class="result-group">
              <p class="result-title">题库</p>
              <button v-for="course in courses" :key="course.id" type="button" class="result-item" @click="goCourse(course)">
                <span>{{ course.name }}</span>
                <small>{{ course.question_count ?? 0 }} 题</small>
              </button>
            </div>

            <div v-if="questions.length" class="result-group">
              <p class="result-title">题目</p>
              <button
                v-for="question in questions"
                :key="question.id"
                type="button"
                class="result-item"
                @click="goQuestion(question)"
              >
                <span>{{ question.question }}</span>
                <small>{{ question.subject || "题目" }}</small>
              </button>
            </div>

            <p v-if="!loading && !courses.length && !questions.length" class="search-hint">没有找到相关内容</p>
          </template>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.global-search-mask {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: max(76px, env(safe-area-inset-top)) var(--space-4) var(--space-4);
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(12px);
}
.global-search-panel {
  width: min(560px, 100%);
  max-height: min(640px, calc(100vh - 120px));
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: var(--surface);
  box-shadow: var(--shadow-modal);
}
.global-search-input {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--line-soft);
  color: var(--text-muted);
}
.global-search-input input {
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-main);
  font: inherit;
  font-size: var(--text-md);
  font-weight: 750;
}
.global-search-input button {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-muted);
}
.global-search-body {
  display: grid;
  gap: var(--space-3);
  max-height: 520px;
  overflow: auto;
  overscroll-behavior: contain;
  padding: var(--space-3);
}
.search-hint {
  margin: 0;
  padding: var(--space-5) var(--space-3);
  color: var(--text-muted);
  text-align: center;
  font-size: var(--text-sm);
  font-weight: 700;
}
.result-group {
  display: grid;
  gap: 6px;
}
.result-title {
  margin: 0;
  padding: 0 4px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 850;
}
.result-item {
  display: grid;
  gap: 3px;
  width: 100%;
  min-height: 54px;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  color: var(--text-main);
  text-align: left;
}
.result-item:hover {
  border-color: var(--line-accent);
  background: var(--primary-soft);
}
.result-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: 850;
}
.result-item small {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 650;
}
</style>
