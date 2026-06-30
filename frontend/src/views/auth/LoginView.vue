<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Eye, EyeOff, Lock, User } from "@lucide/vue";

import { useAuth } from "../../stores/auth";

const router = useRouter();
const route = useRoute();
const { login, loading, authMessage, authError, resetFeedback } = useAuth();

const form = ref({
  username: "",
  password: "",
});
const showPassword = ref(false);

async function handleLogin() {
  resetFeedback();
  const ok = await login(form.value.username, form.value.password);
  if (!ok) return;

  const redirect = route.query.redirect;
  if (
    redirect
    && typeof redirect === "string"
    && redirect.startsWith("/")
    && !redirect.startsWith("/login")
    && !redirect.startsWith("/register")
  ) {
    router.push(redirect);
    return;
  }
  router.push({ name: "home" });
}
</script>

<template>
  <div class="auth-form-section">
    <div class="auth-form-header">
      <h2 class="auth-form-title">登录账号</h2>
      <p class="auth-desc">使用你的账号登录，开始刷题复习。</p>
    </div>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <form class="auth-form-stack" @submit.prevent="handleLogin">
      <div class="input-with-icon">
        <User class="input-icon" :size="18" />
        <input
          id="login-username"
          v-model="form.username"
          class="text-input has-left-icon"
          type="text"
          autocomplete="username"
          placeholder="请输入用户名"
        />
      </div>

      <div class="input-with-icon">
        <Lock class="input-icon" :size="18" />
        <input
          id="login-password"
          v-model="form.password"
          class="text-input has-left-icon has-right-icon"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="请输入密码"
        />
        <button
          type="button"
          class="input-suffix"
          tabindex="-1"
          aria-label="切换密码显示"
          @click="showPassword = !showPassword"
        >
          <EyeOff v-if="showPassword" :size="17" />
          <Eye v-else :size="17" />
        </button>
      </div>

      <button class="auth-submit-btn" type="submit" :disabled="loading">
        {{ loading ? "登录中..." : "登录" }}
      </button>
    </form>

    <p class="auth-switch">
      还没有账号？
      <router-link :to="{ name: 'register' }">去注册</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth-form-section {
  display: grid;
  gap: var(--space-5);
}

.auth-form-header {
  display: grid;
  gap: 6px;
}

.auth-form-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.2;
  color: var(--text-main);
}

.auth-form-stack {
  display: grid;
  gap: var(--space-3);
}

.input-with-icon {
  position: relative;
  display: grid;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  z-index: 1;
  color: var(--text-placeholder);
  pointer-events: none;
  transform: translateY(-50%);
}

.text-input.has-left-icon {
  padding-left: 42px;
}

.text-input.has-right-icon {
  padding-right: 46px;
}

.input-suffix {
  position: absolute;
  right: 8px;
  top: 50%;
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transform: translateY(-50%);
  transition: color var(--ease-out);
}

.input-suffix:hover {
  color: var(--text-secondary);
}

.auth-submit-btn {
  width: 100%;
  min-height: 48px;
  margin-top: var(--space-2);
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #ffffff;
  font: inherit;
  font-size: var(--text-base);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--ease-out), transform var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.auth-submit-btn:hover:not(:disabled) {
  background: var(--primary-strong);
}

.auth-submit-btn:active:not(:disabled) {
  transform: scale(0.99);
}

.auth-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
