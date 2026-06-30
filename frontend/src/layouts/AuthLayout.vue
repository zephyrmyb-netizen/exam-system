<script setup>
// Standalone auth layout — clean brand entry
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#logo-grad)" />
            <path d="M8 14l6-4.5 6 4.5" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M10 18l4-3 4 3" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
            <defs>
              <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#3b82f6" /><stop offset="1" stop-color="#1d4ed8" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1>学习宝</h1>
      </div>
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) var(--space-4);
  box-sizing: border-box;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: var(--space-8) var(--space-6);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-2xl);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.auth-brand {
  text-align: center;
  margin-bottom: var(--space-8);
}

.auth-logo {
  display: inline-flex;
  margin-bottom: var(--space-4);
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.24);
}

.auth-logo svg {
  width: 48px;
  height: 48px;
}

.auth-brand h1 {
  margin: 8px 0 0;
  font-size: var(--text-2xl);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--text-main);
}

@media (max-width: 420px) {
  .auth-card {
    padding: var(--space-6) var(--space-5);
    border-radius: var(--radius-xl);
  }

  .auth-brand h1 {
    font-size: var(--text-xl);
  }
}
</style>
