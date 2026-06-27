<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{ class?: string }>(), { class: "" });
const classes = computed(() => cn("flex items-center gap-3 p-6 pt-3", props.class));
</script>

<template>
  <footer :class="classes">
    <slot />
  </footer>
</template>
