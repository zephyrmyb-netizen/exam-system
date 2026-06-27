<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{ class?: string }>(), { class: "" });
const classes = computed(() => cn("text-2xl font-bold text-[var(--text-primary)]", props.class));
</script>

<template>
  <h2 :class="classes">
    <slot />
  </h2>
</template>
