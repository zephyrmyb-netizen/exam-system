<!-- Vendored from Vue Bits (https://vuebits.dev) by David Haz — MIT + Commons Clause.
     Local adaptations for 学习宝 (declared, keep in sync manually):
     - items take Lucide icon components instead of icon-font class names
     - emits "select" so parents can navigate
     - compact 4-across layout with always-visible labels (mobile-first;
       the upstream showcase grid shows labels only on hover) -->
<template>
  <div :class="['grid grid-cols-4 gap-1 w-full overflow-visible', className]">
    <button
      v-for="(item, index) in items"
      :key="index"
      type="button"
      :aria-label="item.label"
      class="relative bg-transparent outline-none [-webkit-tap-highlight-color:transparent] group flex flex-col items-center cursor-pointer"
      @click="emit('select', item)"
    >
      <span class="relative block w-[3.4em] h-[3.4em] [perspective:24em] [transform-style:preserve-3d]">
        <span
          class="absolute top-0 left-0 w-full h-full rounded-[1.05em] block transition-[opacity,transform] duration-300 ease-[cubic-bezier(0.83,0,0.17,1)] origin-[100%_100%] rotate-[15deg] group-hover:[transform:rotate(25deg)_translate3d(-0.5em,-0.5em,0.5em)]"
          :style="{
            ...getBackgroundStyle(item.color),
            boxShadow: '0.5em -0.5em 0.75em hsla(223, 10%, 10%, 0.15)'
          }"
        ></span>

        <span
          class="absolute top-0 left-0 w-full h-full rounded-[1.05em] bg-[hsla(0,0%,100%,0.15)] transition-[opacity,transform] duration-300 ease-[cubic-bezier(0.83,0,0.17,1)] origin-[80%_50%] flex backdrop-blur-[0.75em] [-webkit-backdrop-filter:blur(0.75em)] transform group-hover:[transform:translateZ(2em)]"
          :style="{
            boxShadow: '0 0 0 0.1em hsla(0, 0%, 100%, 0.3) inset'
          }"
        >
          <span class="m-auto w-[1.5em] h-[1.5em] flex items-center justify-center text-white" aria-hidden="true">
            <component :is="item.icon" :size="20" :stroke-width="2.2" />
          </span>
        </span>
      </span>

      <span class="mt-[0.55em] text-center whitespace-nowrap leading-none text-[0.82em] font-medium text-current">
        {{ item.label }}
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Component } from "vue";

export interface GlassIconsItem {
  icon: Component;
  color: string;
  label: string;
}

interface Props {
  items: GlassIconsItem[];
  className?: string;
}

withDefaults(defineProps<Props>(), {
  items: () => [],
  className: ''
});

const emit = defineEmits<{
  select: [item: GlassIconsItem];
}>();

const gradientMapping: Record<string, string> = {
  blue: 'linear-gradient(hsl(223, 90%, 50%), hsl(208, 90%, 50%))',
  purple: 'linear-gradient(hsl(283, 90%, 50%), hsl(268, 90%, 50%))',
  red: 'linear-gradient(hsl(3, 90%, 50%), hsl(348, 90%, 50%))',
  indigo: 'linear-gradient(hsl(253, 90%, 50%), hsl(238, 90%, 50%))',
  orange: 'linear-gradient(hsl(43, 90%, 50%), hsl(28, 90%, 50%))',
  green: 'linear-gradient(hsl(123, 90%, 40%), hsl(108, 90%, 40%))'
};

const getBackgroundStyle = (color: string): Record<string, string> => {
  if (gradientMapping[color]) {
    return { background: gradientMapping[color] };
  }
  return { background: color };
};
</script>
