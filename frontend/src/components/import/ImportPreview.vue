<script setup>
import { computed, ref } from "vue";
import { typeLabel, formatOptions } from "../../utils/question";
import {
  ArrowLeft, CheckCircle, AlertCircle, Trash2, Plus,
  Edit3, BookOpen, Layers, Lock, Globe, Sparkles,
} from "@lucide/vue";
import QuestionEditor from "../question/QuestionEditor.vue";

const emit = defineEmits(["confirm", "back", "retry"]);

const props = defineProps({
  /** { suggested_course_name, questions: [...], warnings: [...], total_count } */
  previewData: { type: Object, required: true },
  /** existing courses for dropdown */
  courses: { type: Array, default: () => [] },
  coursesLoading: { type: Boolean, default: false },
});

// ── Editable questions list ──
const questions = ref([]);
const warnings = ref([]);
const suggestedCourseName = ref("");

// Initialize from props
function initFromProps() {
  if (props.previewData) {
    questions.value = (props.previewData.questions || []).map((q, i) => ({
      ...q,
      _tempId: q.id || `q-${Date.now()}-${i}`,
    }));
    warnings.value = props.previewData.warnings || [];
    suggestedCourseName.value = props.previewData.suggested_course_name || "";
  }
}
initFromProps();

// Watch for prop changes
import { watch } from "vue";
watch(() => props.previewData, initFromProps);

// ── Course selection ──
const selectedCourseId = ref(0);
const courseNameInput = ref("");

// When previewData changes, set course name from suggestion
watch(suggestedCourseName, (v) => {
  if (v && selectedCourseId.value === 0) courseNameInput.value = v;
}, { immediate: true });

const effectiveCourseName = computed(() => {
  if (selectedCourseId.value > 0) {
    const found = props.courses.find(c => c.id === selectedCourseId.value);
    return found?.name || "";
  }
  return courseNameInput.value.trim();
});

// ── Question editing ──
const editingIndex = ref(-1); // -1 = not editing
const showNewQuestionEditor = ref(false);

function editQuestion(index) {
  editingIndex.value = index;
}

function closeEditor() {
  editingIndex.value = -1;
  showNewQuestionEditor.value = false;
}

function onQuestionSaved(data) {
  if (showNewQuestionEditor.value) {
    // Add new question
    const q = {
      ...data,
      _tempId: `q-${Date.now()}`,
    };
    if (data.options) q.options = { ...data.options };
    questions.value.push(q);
    showNewQuestionEditor.value = false;
  } else if (editingIndex.value >= 0) {
    // Update existing
    const idx = editingIndex.value;
    const q = {
      ...questions.value[idx],
      ...data,
      _tempId: questions.value[idx]._tempId,
    };
    if (data.options) q.options = { ...data.options };
    questions.value.splice(idx, 1, q);
    editingIndex.value = -1;
  }
}

function removeQuestion(index) {
  if (!window.confirm(`确定删除第 ${index + 1} 题吗？`)) return;
  questions.value.splice(index, 1);
}

// ── Confirm ──
const confirming = ref(false);
const confirmError = ref("");

function findFirstInvalid() {
  for (let i = 0; i < questions.value.length; i++) {
    const q = questions.value[i];
    if (!q.question?.trim()) return `第 ${i + 1} 题：缺少题干`;
    const validTypes = ["single_choice","multiple_choice","true_false","fill_blank","short_answer"];
    if (!q.type || !validTypes.includes(q.type)) return `第 ${i + 1} 题：题型无效`;
    if (!q.answer?.trim()) return `第 ${i + 1} 题：缺少答案`;
  }
  return null;
}

async function handleConfirm() {
  if (questions.value.length === 0) {
    confirmError.value = "没有可导入的题目，请先解析或添加题目";
    return;
  }

  const invalidMsg = findFirstInvalid();
  if (invalidMsg) {
    confirmError.value = invalidMsg;
    return;
  }

  if (!effectiveCourseName.value && selectedCourseId.value === 0) {
    confirmError.value = "请输入题库名称或选择已有题库";
    return;
  }

  confirming.value = true;
  confirmError.value = "";

  // Build payload — strip _tempId
  const payload = {
    questions: questions.value.map(({ _tempId, ...rest }) => ({ ...rest })),
  };
  if (selectedCourseId.value > 0) {
    payload.course_id = selectedCourseId.value;
  } else {
    payload.course_name = courseNameInput.value.trim();
  }

  emit("confirm", payload);
}

function handleBack() {
  emit("back");
}

function handleRetry() {
  emit("retry");
}
</script>

<template>
  <div class="preview-root">
    <!-- ── Header ── -->
    <div class="preview-head">
      <button class="back-btn" type="button" @click="handleBack" aria-label="返回">
        <ArrowLeft :size="18" :stroke-width="2.5" />
      </button>
      <div class="preview-head-text">
        <p class="preview-title">预览解析结果</p>
        <p v-if="previewData.suggested_course_name" class="preview-sub">
          推荐题库：<strong>{{ previewData.suggested_course_name }}</strong>
        </p>
      </div>
    </div>

    <!-- ── Warnings ── -->
    <div v-if="warnings.length > 0" class="warnings-box">
      <AlertCircle :size="16" :stroke-width="2.5" color="var(--amber)" style="flex-shrink:0" />
      <div>
        <p v-for="(w, i) in warnings" :key="i" class="warn-line">{{ w }}</p>
      </div>
    </div>

    <!-- ── Summary bar ── -->
    <div class="summary-bar">
      <span class="sum-count"><strong>{{ questions.length }}</strong> 道题待导入</span>
      <button class="add-btn" type="button" @click="showNewQuestionEditor = true">
        <Plus :size="14" :stroke-width="2.5" />
        新增题目
      </button>
    </div>

    <!-- ── Question list ── -->
    <div class="q-list">
      <div
        v-for="(q, idx) in questions"
        :key="q._tempId"
        class="q-item"
      >
        <div class="q-item-head">
          <span class="q-index">{{ idx + 1 }}</span>
          <span class="q-type-tag">{{ typeLabel(q.type) }}</span>
          <span class="q-preview">{{ q.question?.slice(0, 60) }}{{ (q.question?.length || 0) > 60 ? '...' : '' }}</span>
        </div>
        <div class="q-item-actions">
          <button class="q-btn" type="button" @click="editQuestion(idx)" title="编辑">
            <Edit3 :size="14" :stroke-width="2.5" />
          </button>
          <button class="q-btn q-btn-danger" type="button" @click="removeQuestion(idx)" title="删除">
            <Trash2 :size="14" :stroke-width="2.5" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── Course selector ── -->
    <div class="course-section">
      <p class="section-label">导入到题库</p>
      <div class="course-row">
        <input
          v-model="courseNameInput"
          class="course-input"
          type="text"
          :disabled="selectedCourseId > 0"
          placeholder="输入新题库名称"
        />
        <span class="course-or">或</span>
        <select v-model="selectedCourseId" class="course-select">
          <option :value="0">新建题库</option>
          <option v-if="coursesLoading" disabled>加载中...</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}（{{ c.question_count ?? 0 }}题）</option>
        </select>
      </div>
    </div>

    <!-- ── Error ── -->
    <p v-if="confirmError" class="msg msg-err">{{ confirmError }}</p>

    <!-- ── Actions ── -->
    <div class="action-row">
      <button class="ghost-button" type="button" @click="handleRetry">
        <Sparkles :size="16" :stroke-width="2.5" style="margin-right:4px" />
        重新解析
      </button>
      <button
        class="primary-button"
        type="button"
        :disabled="confirming || questions.length === 0"
        @click="handleConfirm"
      >
        <CheckCircle :size="16" :stroke-width="2.5" style="margin-right:6px" />
        {{ confirming ? "导入中..." : `确认导入（${questions.length} 题）` }}
      </button>
    </div>

    <!-- ── Question editor overlay ── -->
    <QuestionEditor
      v-if="editingIndex >= 0"
      :question="questions[editingIndex]"
      @close="closeEditor"
      @saved="onQuestionSaved"
    />
    <QuestionEditor
      v-if="showNewQuestionEditor"
      @close="closeEditor"
      @saved="onQuestionSaved"
    />
  </div>
</template>

<style scoped>
.preview-root {
  display: grid;
  gap: var(--space-3);
}

/* ── Head ── */
.preview-head {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}
.back-btn {
  display: grid; place-items: center;
  width: 34px; height: 34px;
  border: 1px solid var(--line-soft); border-radius: 50%;
  background: var(--surface); color: var(--text-secondary);
  cursor: pointer; flex-shrink: 0;
}
.preview-head-text { min-width: 0; }
.preview-title { margin: 0; font-size: var(--text-base); font-weight: 800; color: var(--text-main); }
.preview-sub { margin: 2px 0 0; font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; }
.preview-sub strong { color: var(--primary-strong); }

/* ── Warnings ── */
.warnings-box {
  display: flex; gap: var(--space-2); align-items: flex-start;
  padding: var(--space-3); border-radius: var(--radius-md);
  background: var(--amber-soft); border: 1px solid #fde68a;
}
.warn-line { margin: 0; font-size: var(--text-xs); color: #92400e; font-weight: 600; line-height: 1.5; }
.warn-line + .warn-line { margin-top: 4px; }

/* ── Summary ── */
.summary-bar {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-2);
}
.sum-count { font-size: var(--text-sm); color: var(--text-muted); }
.sum-count strong { color: var(--text-main); font-size: var(--text-lg); }
.add-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 12px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm);
  background: var(--surface); color: var(--primary-strong); font-size: var(--text-xs); font-weight: 700;
  cursor: pointer; transition: background var(--ease-out), border-color var(--ease-out);
}
.add-btn:hover { background: var(--primary-soft); border-color: var(--primary-border); }

/* ── Question list ── */
.q-list { display: grid; gap: 6px; }
.q-item {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--line-soft); border-radius: var(--radius-md);
  background: var(--surface); transition: box-shadow var(--ease-out);
}
.q-item:hover { box-shadow: var(--shadow-xs); }

.q-item-head { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.q-index {
  display: grid; place-items: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--surface-soft); color: var(--text-muted);
  font-size: 11px; font-weight: 800; flex-shrink: 0;
}
.q-type-tag {
  padding: 2px 6px; border-radius: 4px;
  background: var(--primary-soft); color: var(--primary-strong);
  font-size: 10px; font-weight: 700; flex-shrink: 0;
}
.q-preview { font-size: var(--text-xs); color: var(--text-secondary); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.q-item-actions { display: flex; gap: 4px; flex-shrink: 0; }
.q-btn {
  display: grid; place-items: center;
  width: 28px; height: 28px; border: none; border-radius: var(--radius-sm);
  background: transparent; color: var(--text-placeholder); cursor: pointer;
  transition: all var(--ease-out);
}
.q-btn:hover { background: var(--primary-soft); color: var(--primary-strong); }
.q-btn-danger:hover { background: var(--rose-soft); color: var(--rose); }

/* ── Course section ── */
.course-section { display: grid; gap: 6px; }
.section-label { margin: 0; font-size: var(--text-xs); font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.course-row { display: grid; grid-template-columns: 1fr auto 1fr; gap: var(--space-2); align-items: center; }
.course-input {
  min-height: 42px; padding: 8px 12px;
  border: 1.5px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--surface-soft); font-size: var(--text-sm); outline: none;
  transition: border-color var(--ease-out), box-shadow var(--ease-out);
}
.course-input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); background: var(--surface); }
.course-input:disabled { opacity: 0.5; cursor: not-allowed; }
.course-or { font-size: var(--text-xs); color: var(--text-placeholder); font-weight: 600; }
.course-select {
  min-height: 42px; padding: 8px 10px;
  border: 1.5px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--surface-soft); font-size: var(--text-sm); color: var(--text-main);
}

/* ── Messages ── */
.msg { margin: 0; padding: 8px 12px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600; text-align: center; }
.msg-err { background: var(--rose-soft); color: var(--rose); }

/* ── Actions ── */
.action-row { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2); margin-top: var(--space-1); }
.ghost-button, .primary-button { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; font-size: var(--text-sm); font-weight: 700; border-radius: var(--radius-md); }
.ghost-button { padding: 0 14px; color: var(--primary-strong); background: var(--primary-soft); border: 1px solid var(--primary-border); cursor: pointer; }
.primary-button {
  padding: 0 18px; border: none; color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary); cursor: pointer;
}
.primary-button:disabled { opacity: 0.55; cursor: not-allowed; box-shadow: none; }

@media (max-width: 420px) {
  .course-row { grid-template-columns: 1fr; }
  .course-or { text-align: center; }
}
</style>
