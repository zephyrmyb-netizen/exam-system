<script setup>
// Standalone auth layout — clean brand entry
</script>

<template>
  <div class="auth-page">
    <div class="auth-logo fade-up">
      <div class="seal">宝</div>
      <h1>学习宝</h1>
      <p>Scholar's Atelier · 墨韵书房</p>
    </div>
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
  padding: calc(var(--space-6) + env(safe-area-inset-top)) var(--space-4)
           calc(var(--space-6) + env(safe-area-inset-bottom));
}
</style>
