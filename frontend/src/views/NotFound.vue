<script setup lang="ts">
import { useRouter } from "vue-router";
import { Home } from "@lucide/vue";

const router = useRouter();
</script>

<template>
  <section class="not-found-page">
    <div class="not-found-card">
      <strong class="not-found-code">404</strong>
      <p class="not-found-text">页面不存在</p>
      <p class="not-found-desc">你访问的页面可能已被移除或链接有误。</p>
      <button class="home-btn" type="button" @click="router.push({ name: 'home' })">
        <Home :size="18" />
        返回首页
      </button>
    </div>
  </section>
</template>

<style scoped>
.not-found-page {
  display: grid;
  place-items: center;
  min-height: 70vh;
  padding: var(--space-6);
}

.not-found-card {
  display: grid;
  gap: var(--space-3);
  justify-items: center;
  text-align: center;
}

.not-found-code {
  font-size: 80px;
  font-weight: 900;
  line-height: 1;
  color: var(--primary);
  letter-spacing: -0.04em;
}

.not-found-text {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--text-main);
}

.not-found-desc {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.home-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  margin-top: var(--space-3);
  padding: 0 24px;
  border: 0;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
</style>
