<script setup>
import { reactive, watch } from "vue";
import { X } from "@lucide/vue";

const props = defineProps({
  course: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["close", "save"]);

const form = reactive({ name: "", description: "", subject: "" });

watch(
  () => props.course,
  (course) => {
    form.name = course?.name || "";
    form.description = course?.description || "";
    form.subject = course?.subject || "";
  },
  { immediate: true }
);

function save() {
  emit("save", {
    name: form.name,
    description: form.description,
    subject: form.subject,
  });
}
</script>

<template>
  <div class="form-overlay" @click.self="$emit('close')">
    <div class="form-modal">
      <div class="form-head">
        <h3>编辑题库</h3>
        <button class="form-close" type="button" @click="$emit('close')">
          <X :size="18" :stroke-width="2.5" />
        </button>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>

      <label class="field">
        <span class="field-label">题库名称</span>
        <input v-model="form.name" class="field-input" type="text" />
      </label>
      <label class="field">
        <span class="field-label">科目</span>
        <input v-model="form.subject" class="field-input" type="text" placeholder="可选" />
      </label>
      <label class="field">
        <span class="field-label">描述</span>
        <textarea v-model="form.description" class="field-input field-textarea" placeholder="可选" />
      </label>

      <div class="form-actions">
        <button class="btn-cancel" type="button" @click="$emit('close')">取消</button>
        <button class="btn-save" type="button" :disabled="loading" @click="save">
          {{ loading ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
}

.form-modal {
  position: relative;
  display: grid;
  gap: var(--space-3);
  width: 100%;
  max-width: 420px;
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: var(--shadow-modal);
}

.form-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-head h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
}

.form-close {
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

.form-error {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--rose-soft);
  color: var(--rose);
  font-size: var(--text-sm);
  font-weight: 600;
}

.field {
  display: grid;
  gap: 4px;
}

.field-label {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 700;
}

.field-input {
  min-height: 42px;
  padding: 10px 12px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  color: var(--text-main);
  font-size: var(--text-sm);
  outline: none;
}

.field-input:focus {
  border-color: var(--primary);
  background: var(--surface);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

.field-textarea {
  min-height: 70px;
  resize: vertical;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.btn-cancel,
.btn-save {
  min-height: 44px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 700;
  cursor: pointer;
}

.btn-cancel {
  border: 1.5px solid var(--line-strong);
  background: var(--surface);
  color: var(--text-muted);
}

.btn-cancel:hover {
  background: var(--surface-soft);
}

.btn-save {
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
  box-shadow: var(--shadow-primary);
}

.btn-save:disabled {
  opacity: 0.55;
}
</style>
