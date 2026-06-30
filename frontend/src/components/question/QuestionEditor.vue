<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import request, { getErrorMessage } from "../../api/request";
import { typeOptions } from "../../utils/question";
import { X, Plus, Trash2 } from "@lucide/vue";

const props = defineProps({
  courseId: { type: [String, Number], default: "" },
  question: { type: Object, default: null }, // existing question for edit mode
});

const emit = defineEmits(["close", "saved"]);

const isEdit = computed(() => !!props.question);

const form = reactive({
  type: "single_choice",
  subject: "",
  chapter: "",
  question: "",
  options: ["", ""], // array of option values for choices
  answer: "",
  analysis: "",
  difficulty: "normal",
});

const saving = ref(false);
const errorMessage = ref("");
const validationErrors = ref([]);

// Text answer hints
const answerHint = computed(() => {
  const t = form.type;
  if (t === "single_choice") return "例如：A";
  if (t === "multiple_choice") return "例如：A,C";
  if (t === "true_false") return "正确 或 错误";
  if (t === "fill_blank") return "用 || 分隔多个可接受答案，用 && 表示必须同时包含的关键词";
  if (t === "short_answer") return "用 || 分隔多个可接受答案，用 && 表示必须同时包含的关键词";
  return "";
});

function initForm() {
  if (props.question) {
    const q = props.question;
    form.type = q.type || "single_choice";
    form.subject = q.subject || "";
    form.chapter = q.chapter || "";
    form.question = q.question || "";
    form.answer = q.answer || "";
    form.analysis = q.analysis || "";
    form.difficulty = q.difficulty || "normal";
    // Parse options
    const opts = q.options;
    if (opts && typeof opts === "object") {
      const keys = Object.keys(opts).sort();
      form.options = keys.map(k => opts[k]);
    } else {
      form.options = ["", ""];
    }
  }
}

function addOption() {
  form.options.push("");
}

function removeOption(index) {
  if (form.options.length <= 2) return;
  form.options.splice(index, 1);
}

function validate() {
  const errors = [];
  const t = form.type;

  if (!form.subject.trim()) errors.push("请输入科目");
  if (!form.chapter.trim()) errors.push("请输入章节");
  if (!form.question.trim()) errors.push("请输入题目题干");
  if (!form.answer.trim()) errors.push("请输入答案");

  if (t === "single_choice" || t === "multiple_choice") {
    const filled = form.options.filter(o => o.trim());
    if (filled.length < 2) errors.push("选择题至少需要 2 个有效选项");
  }

  validationErrors.value = errors;
  return errors.length === 0;
}

async function submit() {
  if (!validate()) return;

  saving.value = true;
  errorMessage.value = "";

  // Build payload
  const payload = {
    type: form.type,
    subject: form.subject.trim(),
    chapter: form.chapter.trim(),
    question: form.question.trim(),
    answer: form.answer.trim(),
    analysis: form.analysis.trim(),
    difficulty: form.difficulty,
  };

  // Build options for choices
  if (form.type === "single_choice" || form.type === "multiple_choice") {
    const opts = {};
    form.options.forEach((val, i) => {
      if (val.trim()) {
        opts[String.fromCharCode(65 + i)] = val.trim();
      }
    });
    payload.options = opts;
  }

  if (isEdit.value) {
    // Add course_id for edit
    payload.course_id = props.question.course_id || Number(props.courseId) || 0;
  } else {
    payload.course_id = Number(props.courseId);
  }

  try {
    if (isEdit.value) {
      await request.patch(`/questions/${props.question.id}`, payload);
    } else {
      await request.post("/questions/", payload);
    }
    emit("saved");
    emit("close");
  } catch (error) {
    errorMessage.value = getErrorMessage(error, isEdit.value ? "更新题目失败" : "创建题目失败");
  } finally {
    saving.value = false;
  }
}

onMounted(initForm);
watch(() => props.question, initForm);
</script>

<template>
  <div class="editor-overlay" @click.self="emit('close')">
    <div class="editor-modal">
      <div class="editor-head">
        <h3>{{ isEdit ? "编辑题目" : "新增题目" }}</h3>
        <button class="editor-close" type="button" @click="emit('close')" aria-label="关闭">
          <X :size="18" :stroke-width="2.5" />
        </button>
      </div>

      <!-- Error -->
      <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

      <!-- Validation -->
      <ul v-if="validationErrors.length" class="val-errors">
        <li v-for="e in validationErrors" :key="e">{{ e }}</li>
      </ul>

      <div class="editor-body">
        <!-- Type -->
        <label class="field">
          <span class="field-label">题型</span>
          <select v-model="form.type" class="field-input">
            <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>

        <!-- Subject & Chapter -->
        <div class="field-row">
          <label class="field flex-1">
            <span class="field-label">科目</span>
            <input v-model="form.subject" class="field-input" type="text" placeholder="如：数学" />
          </label>
          <label class="field flex-1">
            <span class="field-label">章节</span>
            <input v-model="form.chapter" class="field-input" type="text" placeholder="如：第一章" />
          </label>
        </div>

        <!-- Question -->
        <label class="field">
          <span class="field-label">题干</span>
          <textarea v-model="form.question" class="field-input field-textarea" placeholder="请输入题目内容" />
        </label>

        <!-- Options for choices -->
        <template v-if="form.type === 'single_choice' || form.type === 'multiple_choice'">
          <div class="field">
            <div class="field-label-row">
              <span class="field-label">选项</span>
              <button type="button" class="add-opt-btn" @click="addOption">
                <Plus :size="14" :stroke-width="2.5" />
                添加选项
              </button>
            </div>
            <div class="options-list">
              <div v-for="(opt, idx) in form.options" :key="idx" class="option-row">
                <span class="option-letter">{{ String.fromCharCode(65 + idx) }}</span>
                <input
                  v-model="form.options[idx]"
                  class="field-input"
                  type="text"
                  :placeholder="`选项 ${String.fromCharCode(65 + idx)}`"
                />
                <button
                  v-if="form.options.length > 2"
                  type="button"
                  class="opt-remove"
                  @click="removeOption(idx)"
                  title="删除此选项"
                >
                  <Trash2 :size="14" :stroke-width="2" />
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- Answer -->
        <label class="field">
          <span class="field-label">答案</span>
          <input v-model="form.answer" class="field-input" type="text" :placeholder="answerHint" />
          <span class="field-hint">{{ answerHint }}</span>
        </label>

        <!-- Analysis -->
        <label class="field">
          <span class="field-label">解析（可选）</span>
          <textarea v-model="form.analysis" class="field-input field-textarea-sm" placeholder="输入解析内容" />
        </label>

        <!-- Difficulty -->
        <label class="field">
          <span class="field-label">难度</span>
          <select v-model="form.difficulty" class="field-input">
            <option value="easy">简单</option>
            <option value="normal">普通</option>
            <option value="hard">困难</option>
          </select>
        </label>
      </div>

      <div class="editor-actions">
        <button class="btn-cancel" type="button" @click="emit('close')">取消</button>
        <button class="btn-save" type="button" :disabled="saving" @click="submit">
          {{ saving ? "保存中..." : isEdit ? "保存修改" : "创建题目" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editor-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
}

.editor-modal {
  position: relative;
  display: grid;
  gap: var(--space-3);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-modal);
}

.editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.editor-head h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
}

.editor-close {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--line-soft);
  border-radius: 50%;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}
.editor-close:hover { background: var(--surface-soft); }

.editor-body {
  display: grid;
  gap: var(--space-3);
}

.field {
  display: grid;
  gap: 4px;
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--text-secondary);
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-hint {
  font-size: 11px;
  color: var(--text-placeholder);
  font-weight: 500;
  line-height: 1.4;
}

.field-input {
  min-height: 42px;
  padding: 10px 12px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  font-size: var(--text-sm);
  color: var(--text-main);
  outline: none;
  transition: border-color var(--ease-out);
}

.field-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
  background: var(--surface);
}

.field-textarea {
  min-height: 80px;
  resize: vertical;
}

.field-textarea-sm {
  min-height: 60px;
  resize: vertical;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.flex-1 { flex: 1; }

/* Options list */
.options-list {
  display: grid;
  gap: 6px;
}

.option-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 6px;
}

.option-letter {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
}

.add-opt-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 4px 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}
.add-opt-btn:hover { background: var(--primary-soft); border-color: var(--primary-border); color: var(--primary-strong); }

.opt-remove {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-placeholder);
  cursor: pointer;
}
.opt-remove:hover { background: var(--rose-soft); color: var(--rose); }

.error-msg {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--rose-soft);
  color: var(--rose);
  font-size: var(--text-sm);
  font-weight: 600;
}

.val-errors {
  margin: 0;
  padding: 8px 12px 8px 28px;
  border-radius: var(--radius-sm);
  background: #fef3c7;
  color: #92400e;
  font-size: var(--text-xs);
  font-weight: 600;
  display: grid;
  gap: 2px;
}

.editor-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.btn-cancel {
  min-height: 44px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-muted);
  font-weight: 700;
  font-size: var(--text-sm);
  cursor: pointer;
}
.btn-cancel:hover { background: var(--surface-soft); }

.btn-save {
  min-height: 44px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  font-weight: 800;
  font-size: var(--text-sm);
  cursor: pointer;
  box-shadow: var(--shadow-primary);
}
.btn-save:hover:not(:disabled) { transform: translateY(-1px); }
.btn-save:disabled { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 420px) {
  .editor-modal {
    padding: var(--space-4);
    max-height: 95vh;
  }
  .field-row {
    grid-template-columns: 1fr;
  }
}
</style>
