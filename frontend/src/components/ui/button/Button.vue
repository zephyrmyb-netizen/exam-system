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
  "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
  {
    "bg-[var(--primary)] text-white shadow-lg shadow-blue-500/20 hover:brightness-105": props.variant === "default",
    "bg-[var(--surface-muted)] text-[var(--text-primary)] hover:bg-[var(--border)]": props.variant === "secondary",
    "bg-transparent text-[var(--text-secondary)] hover:bg-[var(--surface-muted)]": props.variant === "ghost",
    "border border-[var(--border)] bg-transparent text-[var(--text-primary)] hover:bg-[var(--surface-muted)]": props.variant === "outline",
    "bg-[var(--color-danger)] text-white hover:brightness-105": props.variant === "danger",
    "h-9 px-3 text-sm": props.size === "sm",
    "h-11 px-4 text-base": props.size === "md",
    "h-14 px-5 text-lg": props.size === "lg",
  },
  props.class,
));
</script>

<template>
  <button :class="classes">
    <slot />
  </button>
</template>
