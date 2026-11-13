<script setup lang="ts"></script>

<template>
  <div class="auth-page">
    <router-view />
  </div>
</template>

<style scoped>
/* auth-page 用 fixed 铺满整个视口，避免 body 的 padding-top: env(safe-area-inset-top)
   导致 min-height: 100vh 超出视口底部、内容被裁。
   背景是 iOS 式的安静画布：一层近乎无感的纵向微渐变，不用动效背景。 */
.auth-page {
  position: fixed;
  inset: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(180deg, var(--surface) 0%, var(--page-bg) 55%);
  color: var(--text-main);
  padding: calc(var(--space-6) + env(safe-area-inset-top)) var(--space-4)
    calc(var(--space-6) + env(safe-area-inset-bottom));
}
</style>
