<script setup>
defineProps({
  modelValue: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
});

defineEmits(["update:modelValue", "keydown"]);
</script>

<template>
  <div class="practice-text-answer">
    <textarea
      :value="modelValue"
      class="practice-text-answer__input"
      :disabled="disabled"
      placeholder="在这里输入你的答案"
      @input="$emit('update:modelValue', $event.target.value)"
      @keydown="$emit('keydown', $event)"
    />
    <p class="practice-text-answer__hint">Enter 提交，Shift + Enter 换行</p>
  </div>
</template>

<style scoped>
.practice-text-answer {
  display: grid;
  gap: 8px;
}

.practice-text-answer__input {
  width: 100%;
  min-height: 144px;
  padding: 12px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-main);
  font-size: 15px;
  line-height: 1.75;
  resize: vertical;
  transition: border-color var(--ease-out), box-shadow var(--ease-out), background var(--ease-out);
}

.practice-text-answer__input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-soft);
  background: var(--surface);
}

.practice-text-answer__input:disabled {
  opacity: 0.72;
}

.practice-text-answer__hint {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-placeholder);
}

@media (max-width: 420px) {
  .practice-text-answer__input {
    min-height: 128px;
    padding: 12px;
  }
}
</style>
