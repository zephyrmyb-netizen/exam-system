<script setup lang="ts">
</script>

<template>
  <div class="auth-page">
    <router-view />
  </div>
</template>

<style scoped>
/* auth-page 用 fixed 铺满整个视口，避免 body 的 padding-top: env(safe-area-inset-top)
   导致 min-height: 100vh 超出视口底部、内容被裁。 */
.auth-page {
  position: fixed;
  inset: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--page-bg);
  color: var(--text-main);
  padding: calc(var(--space-6) + env(safe-area-inset-top)) var(--space-4)
           calc(var(--space-6) + env(safe-area-inset-bottom));
}
</style>
