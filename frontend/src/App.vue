<script setup lang="ts">
import { onMounted } from "vue";
import { useThemeStore } from "@/stores/theme";

const theme = useThemeStore();
onMounted(() => theme.init());
</script>

<template>
  <router-view />
</template>
