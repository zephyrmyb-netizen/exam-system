<script setup lang="ts">
import { computed } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{
  variant?: "default" | "secondary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  class?: string;
}>(), {
  variant: "default",
  size: "md",
  class: "",
});

const classes = computed(() => cn(
  "btn",
  {
    "btn--default": props.variant === "default",
    "btn--secondary": props.variant === "secondary",
    "btn--ghost": props.variant === "ghost",
    "btn--outline": props.variant === "outline",
    "btn--danger": props.variant === "danger",
    "btn--sm": props.size === "sm",
    "btn--md": props.size === "md",
    "btn--lg": props.size === "lg",
  },
  props.class,
));
</script>

<template>
  <button :class="classes">
    <slot />
  </button>
</template>
