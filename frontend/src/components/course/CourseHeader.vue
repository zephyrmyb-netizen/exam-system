<script setup>
import {
  BookOpen,
  Download,
  Globe,
  Layers,
  Lock,
  Pencil,
  Play,
  Trash2,
  Upload,
} from "@lucide/vue";

import { getCourseDisplayName } from "../../utils/course";

defineProps({
  course: {
    type: Object,
    required: true,
  },
  isOwner: {
    type: Boolean,
    default: false,
  },
  canStartPractice: {
    type: Boolean,
    default: false,
  },
  publishLoading: {
    type: Boolean,
    default: false,
  },
  deleteLoading: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["practice", "import", "edit", "publish", "unpublish", "export", "delete"]);
</script>

<template>
  <div class="course-header">
    <div class="course-header-top">
      <div class="course-header-icon">
        <BookOpen :size="24" :stroke-width="2" />
      </div>
      <div class="course-header-info">
        <h2>{{ getCourseDisplayName(course) }}</h2>
        <p class="course-header-meta">
          <Layers :size="14" :stroke-width="2" />
          <span>{{ course.question_count ?? 0 }} 道题</span>
          <span v-if="course.subject" class="meta-subject">{{ course.subject }}</span>
          <span class="visibility-badge" :class="course.visibility">
            <Lock v-if="course.visibility === 'private'" :size="11" :stroke-width="2.5" />
            <Globe v-else :size="11" :stroke-width="2.5" />
            {{ course.visibility === "public" ? "已公开" : "私有" }}
          </span>
        </p>
      </div>
    </div>

    <p v-if="course.description" class="course-desc">{{ course.description }}</p>

    <p v-if="course.visibility === 'public' && isOwner" class="public-hint">
      <Globe :size="14" :stroke-width="2.5" />
      已公开，其他用户可在公共题库中看到
    </p>

    <p v-if="!canStartPractice" class="public-hint public-hint--empty">
      当前题库还没有题目，先导入题目后再开始练习。
    </p>

    <div class="course-header-actions">
      <button class="primary-button" type="button" :disabled="!canStartPractice" @click="$emit('practice')">
        <Play :size="17" :stroke-width="2.5" />
        {{ canStartPractice ? "开始练习" : "暂无题目" }}
      </button>
      <button v-if="isOwner && !canStartPractice" class="ghost-button" type="button" @click="$emit('import')">
        <Upload :size="15" :stroke-width="2.5" />
        去导入题目
      </button>
      <button v-if="isOwner" class="ghost-button" type="button" @click="$emit('edit')">
        <Pencil :size="15" :stroke-width="2.5" />
        编辑
      </button>
      <button v-if="isOwner" class="ghost-button" type="button" @click="$emit('export')">
        <Download :size="15" :stroke-width="2.5" />
        导出
      </button>
      <button
        v-if="isOwner && course.visibility === 'private'"
        class="ghost-button"
        type="button"
        :disabled="publishLoading"
        @click="$emit('publish')"
      >
        <Upload :size="15" :stroke-width="2.5" />
        发布到公共题库
      </button>
      <button
        v-if="isOwner && course.visibility === 'public'"
        class="ghost-button"
        type="button"
        :disabled="publishLoading"
        @click="$emit('unpublish')"
      >
        <Lock :size="15" :stroke-width="2.5" />
        撤回公开
      </button>
      <button
        v-if="isOwner"
        class="delete-button"
        type="button"
        :disabled="deleteLoading"
        title="删除此题库"
        @click="$emit('delete')"
      >
        <Trash2 :size="16" :stroke-width="2.5" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.course-header {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.course-header-top {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-3);
}

.course-header-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.course-header-info {
  min-width: 0;
}

.course-header-info h2 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 800;
  line-height: 1.2;
}

.course-header-meta {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
}

.meta-subject {
  color: var(--text-secondary);
  font-weight: 700;
}

.visibility-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.visibility-badge.private {
  background: #f1f5f9;
  color: #64748b;
}

.visibility-badge.public {
  background: #ecfdf3;
  color: #067647;
}

.course-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.55;
}

.public-hint {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  gap: 4px;
  margin: 0;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  background: var(--emerald-soft);
  color: var(--emerald);
  font-size: var(--text-xs);
  font-weight: 700;
}

.public-hint--empty {
  background: var(--amber-soft);
  color: var(--amber);
}

.course-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.delete-button {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--line-strong);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ease-out);
}

.delete-button:hover:not(:disabled) {
  border-color: var(--rose-border);
  background: var(--rose-soft);
  color: var(--rose);
}

@media (max-width: 420px) {
  .course-header-info h2 {
    font-size: var(--text-lg);
  }
}
</style>
