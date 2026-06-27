<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{ class?: string }>(), { class: "" });
const classes = computed(() => cn("space-y-2 p-6 pb-3", props.class));
</script>

<template>
  <header :class="classes">
    <slot />
  </header>
</template>
