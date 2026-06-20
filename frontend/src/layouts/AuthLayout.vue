<script setup>
// Standalone auth layout — brand entry with glass surface
</script>

<template>
  <div class="auth-page">
    <!-- Background decor -->
    <div class="auth-bg-decor" aria-hidden="true">
      <div class="auth-blob auth-blob--1"></div>
      <div class="auth-blob auth-blob--2"></div>
    </div>

    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
            <path d="M8 14l6-4.5 6 4.5" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 18l4-3 4 3" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#3b82f6"/><stop offset="1" stop-color="#1d4ed8"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <p class="auth-eyebrow">AI 智能练习</p>
        <h1>考前复习系统</h1>
        <p class="auth-tagline">导入资料 · 智能出题 · 错题复盘</p>
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
  position: relative;
  overflow: hidden;
}

/* ── Soft animated background blobs ── */
.auth-bg-decor {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.auth-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.22;
  animation: auth-float 12s ease-in-out infinite alternate;
}

.auth-blob--1 {
  width: 280px;
  height: 280px;
  top: -60px;
  right: -80px;
  background: radial-gradient(circle, #3b82f6, #8b5cf6 70%);
}

.auth-blob--2 {
  width: 240px;
  height: 240px;
  bottom: -40px;
  left: -60px;
  background: radial-gradient(circle, #0d9488, #3b82f6 70%);
  animation-delay: -6s;
  opacity: 0.18;
}

@keyframes auth-float {
  0%   { transform: translate(0, 0) scale(1); }
  50%  { transform: translate(18px, -14px) scale(1.06); }
  100% { transform: translate(-12px, 10px) scale(0.96); }
}

/* ── Card ── */
.auth-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: var(--space-8) var(--space-6);
  border: 1px solid rgba(203, 213, 225, 0.5);
  border-radius: var(--radius-2xl);
  background: rgba(255, 255, 255, 0.88);
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.06),
    0 20px 48px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

/* ── Brand ── */
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

.auth-eyebrow {
  margin: 0;
  color: var(--primary);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.auth-brand h1 {
  margin: 8px 0 0;
  font-size: var(--text-2xl);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--text-main);
}

.auth-tagline {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.5;
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
