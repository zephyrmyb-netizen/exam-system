<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { BookMarked, Folder, Trash2 } from "@lucide/vue";

import { listBookmarks, removeBookmark } from "@/api/bookmark";
import type { Bookmark, BookmarkList } from "@/types";

const router = useRouter();

const data = ref<BookmarkList>({ items: [], total: 0, folders: [] });
const activeFolder = ref("");
const loading = ref(false);
const errorMessage = ref("");

const items = computed(() => data.value.items || []);

async function fetchBookmarks(folder = activeFolder.value) {
  loading.value = true;
  errorMessage.value = "";
  activeFolder.value = folder;
  try {
    data.value = await listBookmarks(folder || undefined);
  } catch {
    errorMessage.value = "收藏加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

async function remove(item: Bookmark) {
  await removeBookmark(item.question_id);
  await fetchBookmarks();
}

function openQuestion(item: Bookmark) {
  const courseId = item.question?.course_id;
  if (courseId) router.push(`/courses/${courseId}`);
}

onMounted(() => {
  void fetchBookmarks("");
});
</script>

<template>
  <section class="bookmark-page">
    <div class="bookmark-hero">
      <div class="bookmark-hero-icon">
        <BookMarked :size="26" :stroke-width="2.3" />
      </div>
      <div>
        <p>个人复习资料</p>
        <h1>我的收藏</h1>
      </div>
    </div>

    <p v-if="errorMessage" class="status-banner status-banner--error">{{ errorMessage }}</p>

    <div class="folder-tabs">
      <button type="button" :class="{ active: activeFolder === '' }" @click="fetchBookmarks('')">全部</button>
      <button
        v-for="folder in data.folders"
        :key="folder"
        type="button"
        :class="{ active: activeFolder === folder }"
        @click="fetchBookmarks(folder)"
      >
        <Folder :size="13" :stroke-width="2.2" />
        {{ folder }}
      </button>
    </div>

    <p v-if="loading" class="bookmark-empty">加载中...</p>
    <div v-else-if="items.length" class="bookmark-list">
      <article v-for="item in items" :key="item.id" class="bookmark-card">
        <button class="bookmark-body" type="button" @click="openQuestion(item)">
          <span class="bookmark-folder">{{ item.folder_name || "Default" }}</span>
          <strong>{{ item.question?.question || "题目已删除" }}</strong>
          <small v-if="item.note">{{ item.note }}</small>
        </button>
        <button class="bookmark-delete" type="button" aria-label="删除收藏" @click="remove(item)">
          <Trash2 :size="16" :stroke-width="2.4" />
        </button>
      </article>
    </div>

    <div v-else class="bookmark-empty">
      <BookMarked :size="42" :stroke-width="1.7" />
      <p>暂无收藏</p>
      <small>刷题时遇到重点题，可以先收藏，之后集中复盘。</small>
    </div>
  </section>
</template>

<style scoped>
.bookmark-page { display: grid; gap: var(--space-4); }
.bookmark-hero { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--line-soft); border-radius: var(--radius-lg); background: linear-gradient(135deg, var(--surface), var(--primary-soft)); }
.bookmark-hero-icon { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 18px; background: var(--primary); color: #fff; }
.bookmark-hero p { margin: 0; color: var(--text-muted); font-size: var(--text-xs); font-weight: 800; }
.bookmark-hero h1 { margin: 2px 0 0; color: var(--text-main); font-size: var(--text-2xl); font-weight: 900; }
.folder-tabs { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.folder-tabs button { display: inline-flex; align-items: center; gap: 5px; min-height: 34px; padding: 0 12px; border: 1px solid var(--line-soft); border-radius: var(--radius-full); background: var(--surface); color: var(--text-muted); font-weight: 800; white-space: nowrap; }
.folder-tabs button.active { border-color: var(--line-accent); background: var(--primary-soft); color: var(--primary-strong); }
.bookmark-list { display: grid; gap: var(--space-3); }
.bookmark-card { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2); align-items: center; padding: var(--space-3); border: 1px solid var(--line-soft); border-radius: var(--radius-lg); background: var(--surface); }
.bookmark-body { display: grid; gap: 5px; min-width: 0; border: none; background: transparent; color: inherit; text-align: left; }
.bookmark-folder { width: fit-content; padding: 2px 8px; border-radius: var(--radius-full); background: var(--surface-soft); color: var(--text-muted); font-size: 11px; font-weight: 800; }
.bookmark-body strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-main); font-size: var(--text-sm); }
.bookmark-body small { color: var(--text-muted); font-size: var(--text-xs); }
.bookmark-delete { display: grid; place-items: center; width: 36px; height: 36px; border: none; border-radius: 50%; background: var(--rose-soft); color: var(--rose); }
.bookmark-empty { display: grid; place-items: center; gap: 8px; min-height: 180px; padding: var(--space-5); border: 1px dashed var(--line-strong); border-radius: var(--radius-lg); background: var(--surface); color: var(--text-muted); text-align: center; font-weight: 800; }
.bookmark-empty p, .bookmark-empty small { margin: 0; }
.bookmark-empty small { max-width: 260px; font-size: var(--text-xs); font-weight: 650; }
</style>
