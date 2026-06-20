<script setup>
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import {
  Globe,
  ChevronRight,
  Layers,
  BookOpen,
  Search,
} from "@lucide/vue";

const router = useRouter();
const libraries = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const searchKeyword = ref("");

let debounceTimer = null;

async function fetchPublicCourses() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = {};
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim();
    const { data } = await request.get("/library/public", { params });
    libraries.value = Array.isArray(data) ? data : data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "获取公共题库失败");
  } finally {
    loading.value = false;
  }
}

function viewCourse(course) {
  router.push({
    name: "course-detail",
    params: { courseId: course.id },
    query: { from: "public-library" },
  });
}

// Debounced search: 300ms after last keystroke
watch(searchKeyword, () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchPublicCourses();
  }, 300);
});

onMounted(fetchPublicCourses);
onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer);
});
</script>

<template>
  <section class="stack">
    <div class="section-heading row-heading">
      <div>
        <h2>公共题库</h2>
        <p>公开分享的题目集，只读浏览 · 直接练习</p>
      </div>
      <button class="ghost-button" type="button" :disabled="loading" @click="fetchPublicCourses">
        刷新
      </button>
    </div>

    <!-- Search -->
    <div class="search-bar">
      <Search :size="16" :stroke-width="2.5" color="var(--text-muted)" />
      <input
        v-model="searchKeyword"
        class="search-input"
        type="search"
        placeholder="搜索课程名、描述或科目..."
      />
    </div>

    <p v-if="loading" class="info-message">加载中...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div v-if="!loading && libraries.length === 0 && !errorMessage" class="empty-state">
      <Globe :size="40" :stroke-width="1.5" color="var(--text-placeholder)" />
      <p v-if="searchKeyword">未找到匹配「{{ searchKeyword }}」的公开课程</p>
      <p v-else>还没有人发布公开课程，成为第一个吧！</p>
      <button
        v-if="!searchKeyword"
        class="ghost-button"
        type="button"
        @click="router.push('/courses')"
      >
        去我的题库
      </button>
    </div>

    <article
      v-for="lib in libraries"
      :key="lib.id"
      class="public-card"
      @click="viewCourse(lib)"
    >
      <div class="public-card-body">
        <div class="public-icon">
          <BookOpen :size="22" :stroke-width="2" />
        </div>
        <div class="public-info">
          <h3>{{ lib.name || "未命名" }}</h3>
          <p class="public-meta">
            <Layers :size="13" :stroke-width="2" />
            <span>{{ lib.question_count ?? 0 }} 道题</span>
          </p>
          <p v-if="lib.description" class="public-desc">{{ lib.description }}</p>
        </div>
        <ChevronRight class="public-chevron" :size="18" :stroke-width="2.5" color="var(--text-placeholder)" />
      </div>
    </article>
  </section>
</template>

<style scoped>
.row-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-lg);
  background: var(--surface-soft);
  transition: border-color var(--ease-out), box-shadow var(--ease-out);
}

.search-bar:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
  background: var(--surface);
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-main);
  font-size: 15px;
  outline: none;
  min-height: 24px;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.public-card {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: transform var(--ease-out);
}

.public-card:active {
  transform: scale(0.99);
}

.public-card-body {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: var(--space-3);
  padding: var(--space-3);
}

.public-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: var(--emerald-soft);
  color: var(--emerald);
}

.public-info {
  min-width: 0;
}

.public-info h3 {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 700;
}

.public-meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
}

.public-desc {
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.public-chevron {
  flex-shrink: 0;
  margin-top: 12px;
}

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
}

@media (min-width: 640px) {
  .search-bar {
    min-width: 360px;
  }
}
</style>