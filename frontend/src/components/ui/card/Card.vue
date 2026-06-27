<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{ class?: string }>(), { class: "" });
const classes = computed(() => cn(
  "rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-sm",
  props.class,
));
</script>

<template>
  <section :class="classes">
    <slot />
  </section>
</template>
